class Employee:
    def __init__(self, name, salary):
        self.name = name
        self.salary = salary

class Developer(Employee):
    def __init__(self, name, salary, language):
        
        super().__init__(name, salary)
        self.language = language

dev = Developer("Alice", 90000, "Python")
print(f"{dev.name} codes in {dev.language}")