# also see notes_on_asyncio.md

import asyncio
import time
import logging
import random
from collections import deque
# from contextlib import suppress # can be used to suppress exceptions

#MARK: EventBus
class EventBus:
    def __init__(self):
        # topic -> set of subscriber queues
        self._topics: dict[str, set[asyncio.Queue]] = {}
        # topic -> retained messages (older first)
        self._retained: dict[str, deque[tuple[str, object, float]]] = {}
        self._retain_limit: int = 10  # keep last N messages per topic

    # the `*` here specified that all args after it, must be passed in as keyword args.
    # `publish("some topic", 10, True)` would throw an error
    # `publish("some topic", 10, retain=True)` would work
    # -> basically forces the one calling the function to know what the optional bool argument really does here
    # (because it does different things in other methods of the same class)
    async def publish(self, topic: str, data=None, *, retain: bool = False):
        """Publish message to a topic. All subscribers to that topic receive it."""
        if retain:
            dq = self._retained.setdefault(topic, deque(maxlen=self._retain_limit))
            dq.append((topic, data, time.time()))
        queues = self._topics.get(topic, set()).copy()
        for q in queues:
            await q.put((topic, data))

    async def subscribe(self, topic: str, *, replay_retained: bool = True):
        """
        Async generator: yields messages published to `topic`.
        New subscribers receive retained messages first (if replay_retained=True).
        """
        q: asyncio.Queue = asyncio.Queue()
        subs = self._topics.setdefault(topic, set())
        subs.add(q)
        # Push retained messages to this subscriber first
        if replay_retained and topic in self._retained:
            for (t, data, _ts) in self._retained[topic]:
                await q.put((t, data))
        try:
            while True:
                yield await q.get()
        finally:
            subs.discard(q)
            if not subs:
                self._topics.pop(topic, None)

#MARK: State
class State:
    def __init__(self):
        self.hunger = 0
        self.food = 2
        self.light_level = 100
        self.mode = "idle"  # "idle" | "hungry" | "sated" | "alarm_starvation"
        # Metrics
        self.food_gathered_total = 0
        self.food_consumed_total = 0
        self.time_nerd_found_count = 0
        self.start_time = time.monotonic()
        self.last_hunger_alert_time: float | None = None
        self.active_tasks = 0

#MARK: hunger_monitor
# subscribes to hunger ticks; raises alerts and starvation alarms; publishes food.need
async def hunger_monitor(bus: EventBus, state: State, *, hungry_threshold: int = 20, starvation: int = 100):
    async for (_topic, _data) in bus.subscribe("hunger.tick"):
        if state.mode == "alarm_starvation":
            continue
        state.hunger = min(starvation, state.hunger + 1)
        logging.info(f"[HUNGER] Hunger: {state.hunger}")
        # Publish periodic need while hungry to stimulate gatherers
        if state.hunger >= hungry_threshold and state.mode != "alarm_starvation":
            if state.mode != "hungry":
                state.mode = "hungry"
                state.last_hunger_alert_time = time.monotonic()
                await bus.publish("system.alarm", {"type": "hunger_alert"})
            # Ask for food every tick while hungry (back-off could be added)
            await bus.publish("food.need", {"urgency": state.hunger})
        # Starvation
        if state.hunger >= starvation and state.mode != "alarm_starvation":
            state.mode = "alarm_starvation"
            await bus.publish("system.alarm", {"type": "starvation"})

#MARK: hunger_clock
# publishes hunger ticks
async def hunger_clock(bus: EventBus, period_sec: float = 1.0):
    while True:
        await asyncio.sleep(period_sec)
        await bus.publish("hunger.tick", None)

#MARK: eater
# consumes food when hungry to reduce hunger; announces consumption
async def eater(bus: EventBus, state: State, *, eat_amount: int = 15):
    async for (_topic, _data) in bus.subscribe("hunger.tick"):
        if state.mode == "hungry" and state.food > 0:
            state.food -= 1
            state.food_consumed_total += 1
            old = state.hunger
            state.hunger = max(0, state.hunger - eat_amount)
            if state.hunger < 10:
                state.mode = "sated"
            logging.info(f"[EATER] Ate 1 food. Hunger {old} -> {state.hunger}. Food left={state.food}")
            await bus.publish("food.consumed", {"amount": 1})

#MARK: gatherer workers
# multiple workers subscribe to food.need and try to find food
async def gatherer(bus: EventBus, state: State, worker_id: int, *, success_p: float = 0.5, max_batch: int = 3):
    async for (_topic, payload) in bus.subscribe("food.need"):
        if state.mode == "alarm_starvation":
            continue
        # Simulate attempt
        await asyncio.sleep(random.uniform(0.1, 0.4))
        if random.random() < success_p:
            amount = random.randint(1, max_batch)
            await bus.publish("food.found", {"amount": amount, "by": worker_id})
            logging.info(f"[GATHERER-{worker_id}] Found {amount} food")
        else:
            logging.info(f"[GATHERER-{worker_id}] No luck this time")

#MARK: pantry
# subscribes to food.found and stores it
async def pantry(bus: EventBus, state: State):
    async for (_topic, payload) in bus.subscribe("food.found"):
        amt = int((payload or {}).get("amount", 0))
        state.food += amt
        state.food_gathered_total += amt
        logging.info(f"[PANTRY] Stored {amt}. Food now={state.food}")

#MARK: time_nerd
# silently publishes its own topic; pauses if hungry
async def time_nerd(bus: EventBus, state: State):
    while True:
        await asyncio.sleep(1)
        if state.mode == "hungry":
            continue
        current_time = int(time.time())
        if current_time % 14 == 0:
            state.time_nerd_found_count += 1
            await bus.publish("time.divisible.14", current_time)

#MARK: time_nerds_proud_mom
# time_nerd's biggest fan, proudly lets everyone know (even though they could just subscribe if they cared)
# has her own stash of snacks, so doesn't care about communal food stores
async def time_nerds_proud_mom(bus: EventBus):
    async for (_topic, payload) in bus.subscribe("time.divisible.14"):
        logging.info("[PROUD_MOM] My boy found another one of his ... things! I'm so proud.")

#MARK: newsletter
# periodically publishes a retained newsletter with system status
async def newsletter(bus: EventBus, state: State, *, period_sec: float = 5.0):
    while True:
        await asyncio.sleep(period_sec)
        now = time.monotonic()
        since_start = now - state.start_time
        since_alert = (now - state.last_hunger_alert_time) if state.last_hunger_alert_time else None
        report = {
            "active_tasks": state.active_tasks,
            "hunger": state.hunger,
            "food": state.food,
            "food_gathered_total": state.food_gathered_total,
            "food_consumed_total": state.food_consumed_total,
            "time_nerd_found_count": state.time_nerd_found_count,
            "since_start_sec": round(since_start, 1),
            "since_last_hunger_alert_sec": round(since_alert, 1) if since_alert is not None else None,
        }
        logging.info(f"[NEWS] {report}")
        # Retain last newsletters so new subscribers get a snapshot
        await bus.publish("system.newsletter", report, retain=True)

#MARK: newsletter_subscriber (example: receives retained immediately)
async def newsletter_subscriber(bus: EventBus):
    async for (_topic, payload) in bus.subscribe("system.newsletter"):
        logging.info(f"[NEWS-SUB] Received newsletter: {payload}")

#MARK: supervisor
# subscribes to system.alarm and coordinates response
async def supervisor(bus: EventBus, state: State, stop_event: asyncio.Event):
    try:
        async for (_topic, payload) in bus.subscribe("system.alarm"):
            kind = (payload or {}).get("type")
            logging.info(f"[SUPERVISOR] Alarm: {kind}")
            if kind == "starvation":
                logging.info("[SUPERVISOR] Starvation reached. Shutting down.")
                stop_event.set()
                break
            # On hunger_alert we keep running; gatherers will react
    except asyncio.CancelledError:
        logging.info("[SUPERVISOR] Stopped")

#MARK: main
async def main():
    # initialise everything
    bus = EventBus()
    state = State()
    stop_event = asyncio.Event()

    # configure logging
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s: %(message)s")

    def track_task(t: asyncio.Task):
        state.active_tasks += 1
        t.add_done_callback(lambda _t: setattr(state, "active_tasks", max(0, state.active_tasks - 1)))
        return t

    # Top-level structured concurrency with TaskGroup
    try:
        async with asyncio.TaskGroup() as tg:
            tasks = [
                track_task(tg.create_task(hunger_clock(bus))),
                track_task(tg.create_task(hunger_monitor(bus, state, hungry_threshold=20, starvation=100))),
                track_task(tg.create_task(eater(bus, state, eat_amount=15))),
                # multiple gatherers
                track_task(tg.create_task(gatherer(bus, state, worker_id=1, success_p=0.6))),
                track_task(tg.create_task(gatherer(bus, state, worker_id=2, success_p=0.5))),
                track_task(tg.create_task(gatherer(bus, state, worker_id=3, success_p=0.4))),
                track_task(tg.create_task(pantry(bus, state))),
                track_task(tg.create_task(time_nerd(bus, state))),
                track_task(tg.create_task(time_nerds_proud_mom(bus))),
                track_task(tg.create_task(supervisor(bus, state, stop_event))),
                track_task(tg.create_task(newsletter(bus, state, period_sec=5.0))),
                # Demonstrate retained delivery: this subscriber may start later and still receive last newsletters
                track_task(tg.create_task(newsletter_subscriber(bus))),
            ]

            # Run until supervisor signals shutdown
            await stop_event.wait()
            for t in tasks:
                t.cancel()
    except* Exception as excs:
        logging.exception("Exceptions in TaskGroup: %s", excs)

    logging.info("[MAIN] Shutdown complete")

#MARK: __name__
if __name__ == "__main__":
    # with suppress(KeyboardInterrupt):
    #     asyncio.run(main())
    asyncio.run(main())
    print("coroutine main() is done!")