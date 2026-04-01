#1
# import shutil
# shutil.copy("data.txt", "data_copy.txt")
# print("Файл көшірілді")

# shutil is a built-in Python module for file operations.
# shutil.copy() copies the file content + permissions (read/write settings) to a new file.

#2 
import shutil
shutil.copyfile("data.txt", "backup.txt")
print("Файл copyfile арқылы көшірілді")

# # copyfile() copies only the content — no permissions copied.

# #3 
# import os
# os.remove("data.txt")
# print("Файл өшірілді")

# # os.remove() permanently deletes the file.

# #4 
# import os
# if os.path.isfile("data.txt"):
#     os.remove("data.txt")
#     print("Файл өшірілді")
# else:
#     print("Файл табылмады")

# #   os.path.isfile() checks whether the file actually exists before trying to delete it.

# #5
# import shutil
# import os
# shutil.copy("data.txt", "archive_data.txt")
# os.remove("data.txt")
# print("Файл көшірілді және бастапқы файл өшірілді")