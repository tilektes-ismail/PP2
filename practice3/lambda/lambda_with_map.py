numbers = [1, 2, 3, 4, 5]
squared = list(map(lambda x: x ** 2, numbers))
print(squared) 


words = ["hello", "world", "python", "lambda"]
uppercase_words = list(map(lambda word: word.upper(), words))
print(uppercase_words)  


prices = [10, 25, 50, 100]
with_tax = list(map(lambda price: price * 1.10, prices))
print(with_tax)  