class Shape:
    def area(self):
        return 0

class Square(Shape):
    def __init__(self, side):
        self.side = side
        
    def area(self):  
        return self.side * self.side

sq = Square(5)
print(f"Square area: {sq.area()}")

# Method overriding is an OOP concept 
# where a child class provides its own implementation
#  of a method that already exists in the parent class.