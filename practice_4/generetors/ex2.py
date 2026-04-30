numbers = [10, 20, 30]
it = iter(numbers)

for num in numbers:
    print(num)

#or

while True:
    try:
        x = next(it)
        print(x)
    except StopIteration:
        break