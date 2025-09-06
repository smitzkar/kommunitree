import time
import threading
from datetime import datetime, timedelta

# Method 1: Using absolute time targets (like millis() approach)
def precise_countdown_absolute(n):
    """Countdown that triggers at precise 1-second intervals"""
    start_time = time.time()
    
    for i in range(n):
        current_count = n - i
        yield current_count
        
        # Calculate when the next second should occur
        target_time = start_time + (i + 1)
        current_time = time.time()
        
        # Sleep only for the remaining time to hit the target
        sleep_duration = target_time - current_time
        if sleep_duration > 0:
            time.sleep(sleep_duration)

# Method 2: Using time.perf_counter() for higher precision
def precise_countdown_perf(n):
    """Countdown using perf_counter for better precision"""
    start_time = time.perf_counter()
    
    for i in range(n):
        current_count = n - i
        yield current_count
        
        # Calculate target time for next iteration
        target_time = start_time + (i + 1)
        
        # Wait until we reach the target time
        while time.perf_counter() < target_time:
            time.sleep(0.001)  # Sleep for 1ms to avoid busy waiting

# Method 3: Non-blocking version that you can check periodically
class PreciseTimer:
    def __init__(self, interval=1.0):
        self.interval = interval
        self.start_time = time.perf_counter()
        self.last_trigger = 0
    
    def should_trigger(self):
        """Returns True if enough time has passed for the next trigger"""
        elapsed = time.perf_counter() - self.start_time
        expected_triggers = int(elapsed / self.interval)
        
        if expected_triggers > self.last_trigger:
            self.last_trigger = expected_triggers
            return True
        return False
    
    def time_until_next(self):
        """Returns time in seconds until next trigger"""
        elapsed = time.perf_counter() - self.start_time
        next_trigger_time = (self.last_trigger + 1) * self.interval
        return max(0, next_trigger_time - elapsed)

# Method 4: Using threading.Timer for scheduled execution
def scheduled_countdown(n, callback):
    """Schedule countdown events at precise intervals"""
    def trigger(count):
        callback(count)
        if count > 1:
            # Schedule next trigger
            timer = threading.Timer(1.0, trigger, args=(count - 1,))
            timer.start()
    
    # Start the first trigger
    timer = threading.Timer(0, trigger, args=(n,))
    timer.start()
    return timer

# Test the methods
if __name__ == "__main__":
    print("=== Method 1: Absolute timing ===")
    start = time.time()
    c = precise_countdown_absolute(5)
    for count in c:
        print(f"{count} at {time.time() - start:.3f}s")
    print("LIFTOFF!")
    print(f"Total time: {time.time() - start:.3f}s")
    
    print("\n=== Method 2: perf_counter ===")
    start = time.perf_counter()
    c = precise_countdown_perf(5)
    for count in c:
        print(f"{count} at {time.perf_counter() - start:.3f}s")
    print("LIFTOFF!")
    print(f"Total time: {time.perf_counter() - start:.3f}s")
    
    print("\n=== Method 3: Non-blocking timer ===")
    timer = PreciseTimer(1.0)
    count = 5
    start = time.perf_counter()
    
    while count > 0:
        if timer.should_trigger():
            print(f"{count} at {time.perf_counter() - start:.3f}s")
            count -= 1
        
        # Simulate other work being done
        time.sleep(0.01)  # 10ms of "other work"
    
    print("LIFTOFF!")
    print(f"Total time: {time.perf_counter() - start:.3f}s")
    
    print("\n=== Method 4: Threaded scheduling ===")
    start_time = time.time()
    
    def print_countdown(count):
        elapsed = time.time() - start_time
        print(f"{count} at {elapsed:.3f}s")
        if count == 1:
            print("LIFTOFF!")
            print(f"Total time: {elapsed:.3f}s")
    
    timer = scheduled_countdown(5, print_countdown)
    
    # Keep main thread alive for the countdown
    time.sleep(6)
