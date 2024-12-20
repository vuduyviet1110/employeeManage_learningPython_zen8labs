class Employee:
    def __init__(self, emp_id, name, age, position, salary):
        self.emp_id = emp_id
        self.name = name
        self.age = age
        self.position = position
        self.salary = salary

    def __str__(self):
        return (f"ID: {self.emp_id}, Name: {self.name}, Age: {self.age}, "
                f"Position: {self.position}, Salary: {self.salary}")

    def to_dict(self):
        return {
            "emp_id": self.emp_id,
            "name": self.name,
            "age": self.age,
            "position": self.position,
            "salary": self.salary
        }
