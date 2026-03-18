with open("data.txt", "w", encoding="utf-8") as file:
    file.write("Сәлем, Python!")
# with means automatically closes the file when the block ends 


#2 
with open("data.txt", "w", encoding="utf-8") as file:
    file.write("Бірінші жол\n")
    file.write("Екінші жол\n")
    file.write("Үшінші жол\n")

#3
lines = ["Алма\n", "Алмұрт\n", "Шие\n"]
with open("data.txt", "w", encoding="utf-8") as file:
    file.writelines(lines)
# writelines() takes a list of strings and writes them all in one call. it doesn't add a new line 

#4
with open("data.txt", "a", encoding="utf-8") as file:
    file.write("\nЖаңа ақпарат қосылды.")

# Mode "a" means append — the file is NOT erased; new content is added at the end.

#5
text = input("Мәтін енгіз: ")
with open("data.txt", "w", encoding="utf-8") as file:
    file.write(text)