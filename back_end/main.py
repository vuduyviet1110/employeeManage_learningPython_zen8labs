from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect, Body, HTTPException
from fastapi.responses import StreamingResponse, JSONResponse
from io import BytesIO
import xmlrpc.client
import pandas as pd
from pydantic import BaseModel, ValidationError
from typing import List, Dict, Any
from datetime import datetime
from fastapi.middleware.cors import CORSMiddleware
import json
import asyncio

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

# Login odoo
logged_in_users = {}

@app.post("/odoo-login")
def login(
    username: str = Body(..., title="Username", description="The username for Odoo"),
    password: str = Body(..., title="Password", description="The password for Odoo"),
    db_name: str = Body(..., title="Database Name", description="The database name for Odoo")
):
    url = 'http://localhost:8069'
    try:
        # Gọi API common để lấy UID
        common = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/common')
        uid = common.authenticate(db_name, username, password, {})
        
        if uid:
            # Lưu thông tin người dùng đã đăng nhập
            logged_in_users[username] = {"uid": uid, "password": password, "db_name": db_name}
            return {"message": "Login successful", "uid": uid}
        else:
            raise HTTPException(status_code=401, detail="Login failed")
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/search-odoo")
def search(
    payload: dict = Body(...)
):
    username = payload.get("username")
    url = 'http://localhost:8069'
    if username not in logged_in_users:
        raise HTTPException(status_code=401, detail="User not logged in")

    # thông tin đăng nhập
    user_info = logged_in_users[username]
    uid = user_info["uid"]
    password = user_info["password"]
    db_name = user_info["db_name"]

    try:
        models = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/object')
        ActiveStudentId = models.execute_kw(
            db_name, uid, password,
            'education.student', 'search',
            [[
                '|',  
                ['state', '=', 'studying'],
                ['state', '=', 'new']
            ]]
        )
        students= models.execute_kw(
            db_name, uid, password,
            'education.student', 'read',
            [ActiveStudentId],{'fields': ['id', 'name', 'school_id', 'age', 'total_score', 'mobile']}
        )
        
        return {"students": students}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
@app.post("/search-created-student-odoo")
def searchCreated(payload: dict = Body(...)):
    username = payload.get("username")
    student_id = payload.get("student_id")
    url = 'http://localhost:8069'
    
    if username not in logged_in_users:
        raise HTTPException(status_code=401, detail="User not logged in")

    user_info = logged_in_users[username]
    uid = user_info["uid"]
    password = user_info["password"]
    db_name = user_info["db_name"]

    if not isinstance(student_id, int):
        raise HTTPException(status_code=400, detail="Invalid student ID")

    try:
        models = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/object')
        ActiveStudentId = models.execute_kw(
            db_name, uid, password,
            'education.student', 'search',
            [[['id', '=', student_id]]]
        )

        if not ActiveStudentId:
            raise HTTPException(status_code=404, detail="Student not found")

        students = models.execute_kw(
            db_name, uid, password,
            'education.student', 'read',
            [ActiveStudentId], {'fields': ['id', 'name', 'school_id', 'age', 'total_score', 'mobile']}
        )
        
        return {"students": students}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/create-odoo")
def create(
    username: str = Body(..., title="username", description="The username for Odoo"),
    student_name: str = Body(..., title="student_name", description="The username for Odoo"),
    dob: str = Body(..., title="dob", description="The student age for Odoo"),
    mobile: str = Body(..., title="mobile", description="The student mobile for Odoo"),
    total_score: str = Body(..., title="total_score", description="The student total score for Odoo"),
):
    url = 'http://localhost:8069'
    if username not in logged_in_users:
        raise HTTPException(status_code=401, detail="User not logged in")

    print(username, student_name, dob, mobile, total_score)

    student_info = {
        "name": student_name,
        "mobile": mobile,
        "total_score": total_score,
        "date_of_birth": dob,
    }
    # thông tin đăng nhập
    user_info = logged_in_users[username]
    uid = user_info["uid"]
    password = user_info["password"]
    db_name = user_info["db_name"]

    try:
        odoo_url = f'{url}/xmlrpc/2/object'
        models = xmlrpc.client.ServerProxy(odoo_url)
        new_student_id = models.execute_kw(
            db_name, uid, password,
            'education.student', 'create',
            [student_info]
        )
        return {"id": new_student_id}
    except xmlrpc.client.Fault as e:
        raise HTTPException(status_code=500, detail=f"Odoo error: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")


# WebSocket
connected_clients: Dict[str, WebSocket] = {}

event_queue = asyncio.Queue()
@app.post("/webhook")
async def webhook_handler(request: Request):
    """
    Nhận webhook từ Odoo và gửi sự kiện qua WebSocket
    """
    try:
        body = await request.json()
        student = StudentSchema(**body)
        timestamp = datetime.now().isoformat()

        # Thêm sự kiện vào hàng đợi
        await event_queue.put({
            "message": "New webhook received",
            "data": student.dict(),
            "timestamp": timestamp,
        })

        return JSONResponse(content={"message": "Webhook received successfully"})
    except ValidationError as e:
        print("Validation error:", e.errors())
        return JSONResponse(content={"error": e.errors()}, status_code=400)
    except Exception as e:
        print("Unexpected error:", str(e))
        return JSONResponse(content={"error": str(e)}, status_code=500)


@app.websocket("/ws/{username}")
async def websocket_endpoint(websocket: WebSocket, username: str):
    """
    Kết nối WebSocket và gửi dữ liệu real-time.
    """
    await websocket.accept()
    connected_clients[username] = websocket
    print(f"WebSocket connected: {username}")

    try:
        while True:
            # Ping để kiểm tra kết nối (heartbeat)
            await websocket.send_json({"type": "heartbeat", "timestamp": datetime.now().isoformat()})
            await asyncio.sleep(10)  # Ping mỗi 10 giây
    except WebSocketDisconnect:
        # Xóa client khi ngắt kết nối
        connected_clients.pop(username, None)
        print(f"WebSocket disconnected: {username}")


async def event_broadcaster():
    """
    Xử lý và gửi sự kiện từ event_queue đến các client qua WebSocket.
    """
    while True:
        event = await event_queue.get()  # Lấy sự kiện từ hàng đợi
        if connected_clients:
            for username, websocket in connected_clients.items():
                try:
                    await websocket.send_json({"events": [event]})
                except Exception as e:
                    print(f"Error sending event to {username}: {str(e)}")

        # Đánh dấu sự kiện đã xử lý
        event_queue.task_done()


# Khởi chạy task xử lý sự kiện
@app.on_event("startup")
async def startup_event():
    asyncio.create_task(event_broadcaster())


@app.get("/requests")
async def get_webhook_requests():
    """
    Lấy danh sách sự kiện đã nhận (dành cho debug).
    """
    return {"requests": list(event_queue._queue)}