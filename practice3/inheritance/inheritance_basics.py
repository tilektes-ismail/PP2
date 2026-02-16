class Animal:
    def speak(self):
        print("Animal makes a sound")

class Dog(Animal):  
    def bark(self):
        print("Woof!")

my_dog = Dog()
my_dog.speak() 
my_dog.bark()   