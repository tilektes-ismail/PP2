# #1
# import os
# os.mkdir("my_folder")
# print("Папка құрылды")

# os.mkdir() creates one folder called my_folder in the current directory.

# #2 
# import os
# os.makedirs("projects/python/files", exist_ok=True)
# print("Ішкі папкалармен бірге құрылды")

# # os.makedirs() creates all folders in the path at once — projects, then python inside it, then files inside that.
# # exist_ok=True — if the folder already exists, don't crash

# #3 
# import os
# items = os.listdir(".")
# print(items)

# # "." means the current directory (where the script is running).
# # os.listdir() returns a list of all files and folders in that location.

# #4 
# import os
# folders = [item for item in os.listdir(".") if os.path.isdir(item)]
# print(folders)

# # os.path.isdir(item) — returns True if the item is a folder, False if it's a file.

# #5
# from pathlib import Path
# folder = Path("new_folder")
# folder.mkdir(exist_ok=True)
# for item in Path(".").iterdir():
#     print(item)

# pathlib is a modern alternative to os — more readable and object-oriented.
# Path("new_folder") — creates a Path object (not the folder yet, just a reference to it).
# folder.mkdir(exist_ok=True) — actually creates the folder
# Path(".").iterdir() — loops through everything in the current directory, similar to
