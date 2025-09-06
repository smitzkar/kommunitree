import time

# Your original version (imprecise)
def countdown_original(n):
    while n > 0:
        yield n
        time.sleep(1.0)  # This doesn't account for execution time
        n -= 1

# Precise version using absolute timing
def countdown_precise(n):
    start_time = time.perf_counter()
    current = n
    
    while current > 0:
        yield current
        current -= 1
        
        # Calculate when the next yield should happen
        target_time = start_time + (n - current + 1)
        
        # Sleep only for the remaining time
        remaining = target_time - time.perf_counter()
        if remaining > 0:
            time.sleep(remaining)

# Arduino-style millis() approach
class MillisTimer:
    def __init__(self):
        self.start_time = time.perf_counter() * 1000  # Convert to milliseconds
    
    def millis(self):
        """Returns milliseconds since timer creation (like Arduino millis())"""
        return int((time.perf_counter() * 1000) - self.start_time)

def countdown_millis_style(n):
    timer = MillisTimer()
    last_second = 0
    current = n
    
    while current > 0:
        current_millis = timer.millis()
        current_second = current_millis // 1000
        
        # Check if a full second has passed
        if current_second > last_second:
            yield current
            current -= 1
            last_second = current_second
        
        # Small delay to prevent busy waiting
        time.sleep(0.001)

# Test comparison
if __name__ == "__main__":
    print("=== Original (imprecise) countdown ===")
    start = time.perf_counter()
    for i in countdown_original(3):
        print(f"{i} at {time.perf_counter() - start:.3f}s")
        # Simulate some processing time
        time.sleep(0.1)  # 100ms of "work"
    print(f"Total time: {time.perf_counter() - start:.3f}s")
    print("LIFTOFF")
    
    print("\n=== Precise countdown ===")
    start = time.perf_counter()
    for i in countdown_precise(3):
        print(f"{i} at {time.perf_counter() - start:.3f}s")
        # Same processing time
        time.sleep(0.1)  # 100ms of "work"
    print(f"Total time: {time.perf_counter() - start:.3f}s")
    print("LIFTOFF")
    
    print("\n=== Arduino millis() style ===")
    start = time.perf_counter()
    for i in countdown_millis_style(3):
        print(f"{i} at {time.perf_counter() - start:.3f}s")
        # Same processing time
        time.sleep(0.1)  # 100ms of "work"
    print(f"Total time: {time.perf_counter() - start:.3f}s")
    print("LIFTOFF")
