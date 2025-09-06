import time

def countdown_precise(n):
    """Countdown that triggers at exact 1-second intervals"""
    start_time = time.perf_counter()
    
    for i in range(n):
        current_count = n - i
        yield current_count
        
        # Calculate when the next second should start
        next_second = start_time + (i + 1)
        
        # Wait until that exact time
        while time.perf_counter() < next_second:
            time.sleep(0.001)  # Small sleep to avoid busy waiting

# Simple test
print("Precise countdown (should be exactly 1 second apart):")
start = time.perf_counter()

for count in countdown_precise(5):
    elapsed = time.perf_counter() - start
    print(f"{count} at {elapsed:.3f}s")
    
    # Simulate some work that takes variable time
    time.sleep(0.1 + (count * 0.02))  # Variable processing time

total_time = time.perf_counter() - start
print(f"LIFTOFF! Total time: {total_time:.3f}s")
print(f"Should be ~5.000s, actual drift: {abs(total_time - 5.0):.3f}s")
