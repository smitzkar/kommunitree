import asyncio
import time
import logging
from contextlib import suppress # can be used to suppress exceptions

#MARK: EventBus
class EventBus:
    def __init__(self):
        self.queue = asyncio.Queue()

    async def publish(self, event):
        await self.queue.put(event)

    async def subscribe(self):
        while True:
            yield await self.queue.get()

#MARK: Shared State
class State:
    def __init__(self):
        self.hunger = 0
        self.light_level = 100
        self.mode = "idle"

#MARK: Worker Task
async def worker(event: str, state: State):
    if event == "hunger_tick":
        state.hunger += 1
        print(f"[WORKER] Hunger: {state.hunger}")
        if state.hunger > 5:
            print("[WORKER] Triggering alarm_fire!")
            state.mode = "alarm_fire"

#MARK: Sensor Loop
async def sensor(bus):
    while True:
        await asyncio.sleep(1)
        await bus.publish("hunger_tick")

#MARK: 2nd "Sensor" Loop
async def time_keeper(bus):
    while True:
        await asyncio.sleep(1)
        current_time = int(time.time())
        if current_time % 14 == 0:
            await bus.publish("divisible_by_14")

#MARK: Supervisor 
async def supervisor(bus, state, stop_event):
    active_tasks = set()
    try:
        async for event in bus.subscribe():
            if state.mode == "alarm_fire":
                print("[SUPERVISOR] Canceling all tasks!")
                for t in active_tasks:
                    t.cancel()
                    # Wait for them to finish/cancel to ensure graceful cleanup
                    if active_tasks:
                        # `*`` = unpacking operator -> unpacks elements of iterable and passes them into the one function call as individual elements
                        await asyncio.gather(*active_tasks, return_exceptions=True)
                stop_event.set()
                break
            elif event == "divisible_by_14":
                print("The nerd found one, let's all congratulate him and move on.")
            t = asyncio.create_task(worker(event, state))
            active_tasks.add(t)
            t.add_done_callback(lambda x: active_tasks.discard(x))
    except asyncio.CancelledError:
        print("[SUPERVISOR] Stopped")

#MARK: Main 
async def main():

    # initialise everything
    bus = EventBus()
    state = State()
    stop_event = asyncio.Event()

    # configure logging
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s: %(message)s")

    # create tasks
    tasks = [
        asyncio.create_task(sensor(bus)),
        asyncio.create_task(time_keeper(bus)),
        asyncio.create_task(supervisor(bus, state, stop_event))
    ]

    # waits until it encounters the stop_event, then cancels all tasks
    # upon encountering the stop condition, the supervisor cancels all his workers, then set the stop_event,
    # which in turn shuts down the supervisor but also the other tasks created in main
    await stop_event.wait()
    for t in tasks:
        t.cancel()
    await asyncio.gather(*tasks, return_exceptions=True)

    print("[MAIN] Shutdown complete")

if __name__ == "__main__":
    # with suppress(KeyboardInterrupt):
    #     asyncio.run(main())
    asyncio.run(main())
