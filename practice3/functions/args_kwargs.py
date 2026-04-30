def add_numbers(*args):
    total = 0
    for num in args:
        total += num
    return total

print(add_numbers(1, 2, 3))        # 6
print(add_numbers(5, 10, 15, 20))  # 50

def print_user_info(**kwargs):
    for key, value in kwargs.items():
        print(key, ":", value)

print_user_info(name="Ali", age=20, country="Kazakhstan")
