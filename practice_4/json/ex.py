import json
with open("ex.json", "r", encoding="utf-8") as file:
    data = json.load(file)
print(data)