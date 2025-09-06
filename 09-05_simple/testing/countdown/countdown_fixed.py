import time

def countdown_basic(n):
    """Original - accumulates timing errors"""
    while n > 0:
        yield n
        time.sleep(1.0)  # Always sleeps 1 second, regardless of other delays
        n -= 1

def countdown_precise(n):
    """Precise - compensates for execution time"""
    start_time = time.perf_counter()
    count = 0
    
    while n > 0:
        yield n
        count += 1
        n -= 1
        
        # Calculate exactly when the next yield should happen
        target_time = start_time + count
        current_time = time.perf_counter()
        
        # Sleep only for the remaining time
        remaining = target_time - current_time
        if remaining > 0:
            time.sleep(remaining)

# Quick test
print("Basic countdown:")
start = time.time()
for i in countdown_basic(3):
    print(f"{i} - elapsed: {time.time() - start:.2f}s")
    time.sleep(0.1)  # Simulate 100ms of work

print(f"Total time: {time.time() - start:.2f}s")

print("\nPrecise countdown:")
start = time.time()
for i in countdown_precise(3):
    print(f"{i} - elapsed: {time.time() - start:.2f}s")
    time.sleep(0.1)  # Same 100ms of work

print(f"Total time: {time.time() - start:.2f}s")
