def square_generator(n):
    for i in range(n + 1):
        yield i * i

# Example
N = 5
for value in square_generator(N):
    print(value)