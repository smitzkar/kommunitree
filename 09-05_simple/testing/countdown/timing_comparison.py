import time

# Your original version
def countdown_original(n):
    while n > 0:
        yield n
        time.sleep(1.0)  # Sleeps for 1 second + execution time
        n -= 1

# Fixed version - like Arduino millis()
def countdown_precise(n):
    start_time = time.perf_counter()  # Record start time
    
    for i in range(n):
        current_count = n - i
        yield current_count
        
        # Calculate target time for next iteration
        target_time = start_time + (i + 1) * 1.0  # Each iteration should be 1 second after start
        current_time = time.perf_counter()
        
        # Only sleep for the remaining time to hit the target
        sleep_time = target_time - current_time
        if sleep_time > 0:
            time.sleep(sleep_time)

# Test both versions
print("=== Original version (accumulates delays) ===")
start = time.perf_counter()
for count in countdown_original(3):
    elapsed = time.perf_counter() - start
    print(f"{count} at {elapsed:.3f}s")
    # Simulate 100ms of processing
    time.sleep(0.1)

total = time.perf_counter() - start
print(f"LIFTOFF! Total: {total:.3f}s (should be 3.0s)")

print(f"\n=== Precise version (compensates for delays) ===")
start = time.perf_counter()
for count in countdown_precise(3):
    elapsed = time.perf_counter() - start
    print(f"{count} at {elapsed:.3f}s")
    # Same 100ms of processing
    time.sleep(0.1)

total = time.perf_counter() - start
print(f"LIFTOFF! Total: {total:.3f}s (should be 3.0s)")

print(f"\n=== Arduino-style millis() approach ===")
class MillisTimer:
    def __init__(self):
        self.start = time.perf_counter()
    
    def millis(self):
        return int((time.perf_counter() - self.start) * 1000)

timer = MillisTimer()
last_print = 0
count = 3

print("Starting millis-style countdown...")
while count > 0:
    current_millis = timer.millis()
    
    # Check if 1000ms (1 second) has passed
    if current_millis >= (4 - count) * 1000 and current_millis > last_print:
        print(f"{count} at {current_millis/1000:.3f}s")
        count -= 1
        last_print = current_millis
        
        # Simulate processing time
        time.sleep(0.1)
    
    # Small delay to prevent busy waiting
    time.sleep(0.001)

print(f"LIFTOFF! Total: {timer.millis()/1000:.3f}s")
