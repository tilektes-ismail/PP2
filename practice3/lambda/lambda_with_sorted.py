students = [("Emil", 25), ("Tobias", 22), ("Linus", 28)]
sorted_students = sorted(students, key=lambda x: x[1])
print(sorted_students)

words = ["python", "java", "javascript", "c", "golang"]
sorted_words = sorted(words, key=lambda word: len(word))
print(sorted_words)


scores = [("Alice", 85), ("Bob", 95), ("Charlie", 78), ("Diana", 92)]
sorted_scores = sorted(scores, key=lambda x: x[1], reverse=True)
print(sorted_scores)
