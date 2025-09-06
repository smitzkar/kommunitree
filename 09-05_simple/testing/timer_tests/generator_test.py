import time

def countdown(n):
    while n > 0:
        yield n # this turns the function into a generator function
        n -= 1

def countdown_precise(n):
    """Countdown that triggers at exact 1-second intervals"""
    start_time = time.perf_counter()
    
    for i in range(n):
        current_count = n - i
        yield current_count
        
        # Calculate when the next second should occur
        target_time = start_time + (i + 1)
        
        # Wait until that exact moment
        while time.perf_counter() < target_time:
            pass  # Busy wait for demonstration

# Test the original generator
print("=== Original countdown (accumulates delays) ===")
start = time.perf_counter()
c = countdown(3)
for i in c:
    elapsed = time.perf_counter() - start
    print(f"{i} at {elapsed:.3f}s")
    time.sleep(0.2)  # Simulate some work taking 200ms
print(f"LIFTOFF at {time.perf_counter() - start:.3f}s")

print("\n=== Precise countdown (exact 1-second intervals) ===")
start = time.perf_counter()
c = countdown_precise(3)
for i in c:
    elapsed = time.perf_counter() - start
    print(f"{i} at {elapsed:.3f}s")
    time.sleep(0.2)  # Same 200ms of work
print(f"LIFTOFF at {time.perf_counter() - start:.3f}s")

# Test exhausting the generator
c = countdown(3)
print(next(c)) # 3
print(next(c)) # 2
print(next(c)) # 1

# This is where the issue is
try:
    print(next(c))
except Exception as e:
    print(f"Failed due to: {e}")
    print(f"Exception type: {type(e)}")
    print(f"Exception repr: {repr(e)}")

# Better way to catch StopIteration specifically
try:
    c2 = countdown(1)
    print(next(c2)) # 1
    print(next(c2)) # This will raise StopIteration
except StopIteration as e:
    print(f"StopIteration caught: {e}")
    print(f"StopIteration repr: {repr(e)}")
