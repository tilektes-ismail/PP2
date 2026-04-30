i = 1
while i <= 5:
    print("while:", i)
    i += 1


i = 1
while True:
    if i == 4:
        break
    print("break while:", i)
    i += 1


i = 0
while i < 5:
    i += 1
    if i == 3:
        continue
    print("continue while:", i)


for i in range(1, 6):
    print("for:", i)


for i in range(1, 6):
    if i == 2:
        continue
    if i == 5:
        break
    print("for mix:", i)
