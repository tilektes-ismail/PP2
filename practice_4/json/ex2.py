import json

data = {
    "name": "Alice",
    "age": 25
}

json_string = json.dumps(data)

print(json_string)
print(type(json_string))  # str