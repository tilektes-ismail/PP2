class Car:
    def __init__(self, brand, model, year):
        self.brand = brand
        self.model = model
        self.year = year
    
    def description(self):
        return f"{self.year} {self.brand} {self.model}"

car1 = Car("Toyota", "Camry", 2022)
car2 = Car("Honda", "Civic", 2023)

print(car1.description())  
print(car2.description())  


class Person:
    def __init__(self, name, age):
        self.name = name
        self.age = age
    
    def greet(self):
        print(f"Hello, my name is {self.name}")

person1 = Person("Alice", 30)
person2 = Person("Bob", 25)

person1.greet()  
person2.greet()  



class BankAccount:
    def __init__(self, owner, balance):
        self.owner = owner
        self.balance = balance
    
    def deposit(self, amount):
        self.balance += amount
        print(f"Deposited ${amount}. New balance: ${self.balance}")
    
    def withdraw(self, amount):
        if amount <= self.balance:
            self.balance -= amount
            print(f"Withdrew ${amount}. New balance: ${self.balance}")
        else:
            print("Insufficient funds!")

account1 = BankAccount("John", 1000)
account1.deposit(500)    
account1.withdraw(200)   
account1.withdraw(2000)  