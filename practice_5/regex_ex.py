import re

# ex 1
pattern_1 = re.compile(r"ab*")

# ex 2
pattern_2 = re.compile(r"ab{2,3}")
txt = "abb"
x = pattern_2.findall(txt)
print(x)

# ex 3
pattern_3 = re.compile(r"[a-z]*_")
txt = "aokwergthjgb_cd"
print(pattern_3.findall(txt))

# ex 4
pattern_4 = re.compile(r"[A-Z][a-z]")
txt = "AAAAAAAAAAAAABBBBBBBBBBBBcdcBIDNIDJbjvbjbn"
print(pattern_4.findall(txt))

# ex 5
pattern_5 = re.compile(r"^a.*b$")
txt = "ajdifjifhiprjg0w rumgueripgupeiurpiwi0eurgpeub"
print(pattern_5.findall(txt))

# ex 6
pattern_6 = re.compile(r"[\s|,|.]")
txt = "bro furina, she is the best. She is the hydro archon"
method_6 = re.sub(pattern_6, "|", txt)
print(method_6)

# ex 7
pattern_7 = re.compile(r"_([a-zA-Z])")
txt = "my_furina"
method_7 = re.sub(pattern_7, lambda match: match.group(1).upper(), txt)
print(method_7)

# ex 8
pattern_8 = re.compile(r"[A-Z]")
txt = "BroFurina,SheIsTheBest.SheIsTheHydroArchon"
method_8 = re.split(pattern_8, txt)
print(method_8)

# ex 9
pattern_9 = re.compile(r"(?<=\w)([A-Z])") 
txt = "BroFurina,SheIsTheBest.SheIsTheHydroArchon"
method_9 = re.sub(pattern_9, r" \1", txt)
print(method_9)

# ex 10
pattern_10 = re.compile(r"(?<=\w)([A-Z])")
txt = "myFurina"
method_10 = re.sub(pattern_10, lambda match: "_" + match.group(1).lower(), txt)
print(method_10)