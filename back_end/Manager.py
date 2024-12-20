from Employee import Employee  
import json
from tabulate import tabulate  


class Manager:
    def __init__(self):
        self.employees = {}

    def add_employee(self, emp_id, name, age, position, salary):
        if emp_id in self.employees:
            print(f"Employee ID {emp_id} already exists!")
            return
        self.employees[emp_id] = Employee(emp_id, name, age, position, salary)
        print(f"Employee {name} added successfully!")

    def display_employees(self):
        if not self.employees:
            print("No employees to display.")
            return
        table = [emp.to_dict().values() for emp in self.employees.values()]
        print(tabulate(table, headers=["ID", "Name", "Age", "Position", "Salary"], tablefmt="grid"))

    def save_to_file(self, filename):
        with open(filename, "w") as file:
            json.dump([emp.to_dict() for emp in self.employees.values()], file)
        print(f"Employees saved to {filename}.")

    def load_from_file(self, filename):
        try:
            with open(filename, "r") as file:
                data = json.load(file)
                for emp in data:
                    self.add_employee(emp["emp_id"], emp["name"], emp["age"], emp["position"], emp["salary"])
            print(f"Employees loaded from {filename}.")
        except FileNotFoundError:
            print(f"File {filename} not found!")

    def find_employee(self, search_term):
        found = [emp for emp in self.employees.values() if search_term.lower() in emp.name.lower()]
        if not found:
            print(f"No employees found with name containing '{search_term}'.")
        else:
            table = [emp.to_dict().values() for emp in found]
            print(tabulate(table, headers=["ID", "Name", "Age", "Position", "Salary"], tablefmt="grid"))

    def delete_employee(self, emp_id):
        if emp_id in self.employees:
            del self.employees[emp_id]
            print(f"Employee ID {emp_id} deleted successfully!")
        else:
            print(f"Employee ID {emp_id} not found.")

    def update_employee(self, emp_id, name=None, age=None, position=None, salary=None):
        if emp_id not in self.employees:
            print(f"Employee ID {emp_id} not found!")
            return
        emp = self.employees[emp_id]
        emp.name = name if name else emp.name
        emp.age = age if age else emp.age
        emp.position = position if position else emp.position
        emp.salary = salary if salary else emp.salary
        print(f"Employee ID {emp_id} updated successfully!")
