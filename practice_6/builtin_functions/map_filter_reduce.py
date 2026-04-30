numbers = [1, 2, 3, 4, 5]
result = list(map(lambda x: x ** 2, numbers))
print(result)

# map() applies that function to every item in the list.

#2 
numbers = [1, 2, 3, 4, 5, 6]
result = list(filter(lambda x: x % 2 == 0, numbers))
print(result)

#3 
from functools import reduce
numbers = [1, 2, 3, 4, 5]
result = reduce(lambda x, y: x + y, numbers)
print(result)

# reduce() is not built-in — needs to be imported from functools.

# takes first two items, applies the function, then takes that result with the next item, and so on.

#4 
from functools import reduce
numbers = [1, 2, 3, 4, 5, 6]
even_numbers = filter(lambda x: x % 2 == 0, numbers)
squares = map(lambda x: x ** 2, even_numbers)
result = reduce(lambda x, y: x + y, squares)
print(result)

# filter → keeps even numbers → [2, 4, 6]
# map → squares each one → [4, 16, 36]
# reduce → sums them all → 4+16+36 = 56