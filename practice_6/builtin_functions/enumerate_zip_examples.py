#1 
fruits = ["apple", "banana", "cherry"]
for index, fruit in enumerate(fruits):
    print(index, fruit)

# enumerate() adds an automatic counter to each item while looping.

#2 
names = ["Ali", "Aruzhan", "Dana"]
for index, name in enumerate(names, start=1):
    print(index, name)

#3 
names = ["Ali", "Dana", "Nurlan"]
scores = [85, 90, 78]
for name, score in zip(names, scores):
    print(name, score)

# zip() pairs up items from two lists by position

#4 
names = ["Ali", "Dana", "Nurlan"]
scores = [85, 90, 78]
for index, (name, score) in enumerate(zip(names, scores), start=1):
    print(index, name, score)

#5 
keys = ["name", "age", "city"]
values = ["Aruzhan", 20, "Almaty"]
student = dict(zip(keys, values))
print(student)