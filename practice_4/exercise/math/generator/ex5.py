def countdown(n):
    while n >= 0:
        yield n
        n -= 1

# Example
for number in countdown(5):
    print(number)