import json
with open("ex.json", "r", encoding="utf-8") as file:
    data = json.load(file) #The file is just text right now. `json.load()` **magically converts** it into a Python dictionary — like turning a photo of a recipe into real ingredients you can use!

print(data)