from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse, JSONResponse
from io import BytesIO
import pandas as pd
from pydantic import BaseModel, ValidationError
from typing import List, Dict, Any
from datetime import datetime
from fastapi.middleware.cors import CORSMiddleware
import json

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],  
    allow_headers=["*"], 
)



employees = {}

class StudentSchema(BaseModel):
    id: int
    age: int
    name: str
    mobile: str
    school_id: Any 
    total_score: float

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




# phần webhook
webhook_requests = []

class WebhookRequest(BaseModel):
    headers: dict
    body: dict
    timestamp: str
# Danh sách WebSocket kết nối
connected_clients: List[WebSocket] = []

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """Xử lý kết nối WebSocket."""
    await websocket.accept()
    connected_clients.append(websocket)
    try:
        while True:
            # Lắng nghe tin nhắn từ client
            await websocket.receive_text()
    except WebSocketDisconnect:
        connected_clients.remove(websocket)
        print("Client disconnected")

@app.post("/webhook")
async def webhook_handler(request: Request):
    """Xử lý khi nhận webhook từ bên thứ ba."""
    try:
        body = await request.json()
        student = StudentSchema(**body)
        headers = dict(request.headers)
        timestamp = datetime.now().isoformat()

        # Lưu vào danh sách webhook_requests
        webhook_requests.append({
            "headers": headers,
            "body": student.dict(),
            "timestamp": timestamp
        })

        # Gửi thông báo real-time tới tất cả WebSocket clients
        for client in connected_clients:
            await client.send_json({"message": "New webhook received", "data": student.dict()})

        print("Webhook received and validated:", student)
        return JSONResponse(content={"message": "Webhook received successfully"})
    except ValidationError as e:
        print("Validation error:", e.errors())
        return JSONResponse(content={"error": e.errors()}, status_code=400)
    except Exception as e:
        print("Unexpected error:", str(e))
        return JSONResponse(content={"error": str(e)}, status_code=500)

@app.get("/requests")
async def get_webhook_requests():
    return webhook_requests

@app.delete("/requests")
async def clear_webhook_requests():
    webhook_requests.clear()
    return JSONResponse(content={"message": "All requests cleared"})