def even_numbers(n):
    for i in range(n + 1):
        if i % 2 == 0:
            yield i

# Input from console
n = int(input("Enter number: "))

result = ",".join(str(num) for num in even_numbers(n))
print(result)