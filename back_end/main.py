from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from io import BytesIO
import pandas as pd
from pydantic import BaseModel
from typing import List, Dict
from fastapi.middleware.cors import CORSMiddleware
import json

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Hoặc chỉ định domain cụ thể, ví dụ: ["http://127.0.0.1:5500"]
    allow_credentials=True,
    allow_methods=["*"],  # Hoặc ["GET", "POST", "PUT", "DELETE"]
    allow_headers=["*"],  # Hoặc chỉ định cụ thể, ví dụ: ["Content-Type"]
)



employees = {}


class Employee(BaseModel):
    emp_id: int
    name: str
    age: int
    position: str
    salary: float

@app.post("/employees/")
def add_employee(employee: Employee):
    employees[employee.emp_id] = employee
    return {"message": f"Employee {employee.name} added successfully!"}

@app.get("/employees/")
def get_employees():
    return employees

@app.get("/employees/{emp_id}")
def get_employee(emp_id: int):
    employee = employees.get(emp_id)
    if not employee:
        return {"error": "Employee not found"}
    return employee

@app.put("/employees/{emp_id}")
def update_employee(emp_id: int, updated_employee: Employee):
    if emp_id not in employees:
        return {"error": "Employee not found"}
    employees[emp_id] = updated_employee
    return {"message": f"Employee {updated_employee.name} updated successfully!"}

@app.delete("/employees/{emp_id}")
def delete_employee(emp_id: int):
    if emp_id not in employees:
        return {"error": "Employee not found"}
    del employees[emp_id]
    return {"message": f"Employee with ID {emp_id} deleted successfully!"}

@app.get("/employees/search")
def search_employee(query: str):
    results = [
        {"emp_id": emp_id, **employee.dict()}
        for emp_id, employee in employees.items()
        if query.lower() in employee.name.lower() or query.lower() in employee.position.lower()
    ]
    if not results:
        return {"message": "No employees found"}
    return {"employees": results}



@app.get("/employees/export/excel/")
def export_employees_to_excel():
    df = pd.DataFrame.from_records(
        [employee.dict() for employee in employees.values()], 
        columns=Employee.__annotations__.keys()
    )

    excel_file = BytesIO()
    df.to_excel(excel_file, index=False, engine="openpyxl")
    excel_file.seek(0)

    return StreamingResponse(
        excel_file, 
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", 
        headers={"Content-Disposition": "attachment; filename=employees.xlsx"}
    )
