def countdown(n):
    while n > 0:
        yield n
        n -= 1

c = countdown(3)
print(next(c)) # 3
print(next(c)) # 2
print(next(c)) # 1

# Method 1: Check the exception type
try:
    print(next(c))
except Exception as e:
    print(f"Failed due to: {type(e).__name__}: {e if str(e) else 'Generator exhausted'}")

# Method 2: Catch StopIteration specifically
c = countdown(3)
next(c), next(c), next(c)  # Exhaust the generator
try:
    print(next(c))
except StopIteration:
    print("Generator is exhausted!")

# Method 3: Use repr() to see the full exception representation
c = countdown(3)
next(c), next(c), next(c)  # Exhaust the generator
try:
    print(next(c))
except Exception as e:
    print(f"Failed due to: {repr(e)}")

# Method 4: Check if the exception has a meaningful message
c = countdown(3)
next(c), next(c), next(c)  # Exhaust the generator
try:
    print(next(c))
except Exception as e:
    message = str(e) if str(e) else f"{type(e).__name__} (no message)"
    print(f"Failed due to: {message}")
