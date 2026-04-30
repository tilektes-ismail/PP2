numbers = [1, 2, 3, 4, 5, 6, 7, 8]
odd_numbers = list(filter(lambda x: x % 2 != 0, numbers))
print(odd_numbers)


words = ["apple", "cat", "elephant", "dog", "giraffe", "ant"]
long_words = list(filter(lambda word: len(word) > 4, words))
print(long_words) 


values = [-5, 3, -2, 8, 0, -1, 4, -7]
positive_values = list(filter(lambda x: x > 0, values))
print(positive_values) 