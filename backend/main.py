from datetime import datetime
import secrets
import time

from fastapi import FastAPI, Header, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from sqlalchemy import text

from database import engine
from ml_predictor import predict_anomaly

app = FastAPI(title="Database Integrity Violation Prediction & Prevention System")

# Demo sessions are held in memory and expire when the server restarts.
# For a production deployment, use a persistent, secure authentication system.
sessions = {}


class LoginRequest(BaseModel):
    username: str
    password: str


class StudentUpdateRequest(BaseModel):
    student_id: int = Field(gt=0)
    name: str = Field(min_length=2, max_length=100)
    email: str = Field(min_length=5, max_length=150)
    semester: int = Field(ge=1, le=12)


def current_user(authorization: str | None):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Please log in again.")
    token = authorization.split(" ", 1)[1]
    user = sessions.get(token)
    if not user:
        raise HTTPException(status_code=401, detail="Session expired. Please log in again.")
    return user


def admin_user(authorization: str | None):
    user = current_user(authorization)
    if user["role"].lower() != "admin":
        raise HTTPException(status_code=403, detail="Admin permission required.")
    return user


def log_threat(connection, user_id, operation, reason, status, ip_address="127.0.0.1", score=1.0):
    connection.execute(
        text("""
            INSERT INTO threat_logs
            (user_id, ip_address, operation, anomaly_score, reason, action, status)
            VALUES (:user_id, :ip, :operation, :score, :reason, :action, :status)
        """),
        {
            "user_id": user_id,
            "ip": ip_address,
            "operation": operation,
            "score": score,
            "reason": reason,
            "action": "BLOCK" if status in ("BLOCKED", "DENIED") else "MONITOR",
            "status": status,
        },
    )


@app.get("/")
def home():
    return FileResponse("../frontend/login.html")


@app.get("/database-test")
def database_test():
    with engine.connect() as connection:
        result = connection.execute(text("SELECT 1"))
        return {"database": "connected", "result": result.scalar()}


@app.post("/login")
def login(payload: LoginRequest):
    with engine.connect() as connection:
        result = connection.execute(
            text("""
                SELECT user_id, username, role
                FROM users
                WHERE username = :username AND password = :password
            """),
            {"username": payload.username, "password": payload.password},
        ).fetchone()

    if result is None:
        raise HTTPException(status_code=401, detail="Invalid username or password.")

    token = secrets.token_urlsafe(32)
    user = {"user_id": result.user_id, "username": result.username, "role": result.role}
    sessions[token] = user
    return {"status": "SUCCESS", "token": token, **user}


@app.get("/students")
def get_students():
    with engine.connect() as connection:
        rows = connection.execute(text(
            "SELECT student_id, name, email, semester FROM students ORDER BY student_id"
        )).fetchall()
    return [dict(row._mapping) for row in rows]


@app.get("/admin/students")
def admin_students(authorization: str | None = Header(default=None)):
    admin_user(authorization)
    with engine.connect() as connection:
        rows = connection.execute(text(
            "SELECT student_id, name, email, semester FROM students ORDER BY student_id"
        )).fetchall()
    return [dict(row._mapping) for row in rows]


@app.post("/admin/update-student")
def update_student(payload: StudentUpdateRequest, authorization: str | None = Header(default=None)):
    user = admin_user(authorization)

    # The operation is limited to specific student columns; arbitrary SQL is never accepted.
    started = time.perf_counter()
    with engine.connect() as connection:
        existing = connection.execute(
            text("SELECT student_id FROM students WHERE student_id = :sid"),
            {"sid": payload.student_id},
        ).fetchone()
        if existing is None:
            raise HTTPException(status_code=404, detail="Student record not found.")

    execution_time = max(time.perf_counter() - started, 0.01)
    operation = "UPDATE"
    query_length = len("UPDATE students SET name, email, semester WHERE student_id")
    hour = datetime.now().hour
    prediction = predict_anomaly(query_length, execution_time, 1, 0, hour)
    anomaly_score = 1.0 if prediction == "ANOMALY" else 0.0

    # Record the activity and apply the update in one transaction.
    with engine.begin() as connection:
        connection.execute(
            text("""
                INSERT INTO query_logs
                (user_id, role, operation, query_length, execution_time,
                 rows_affected, rows_returned, hour, ip_address, anomaly_score, status)
                VALUES
                (:uid, 'admin', 'UPDATE', :ql, :et, 1, 0, :hour,
                 '127.0.0.1', :score, :status)
            """),
            {"uid": user["user_id"], "ql": query_length, "et": execution_time,
             "hour": hour, "score": anomaly_score, "status": prediction},
        )

        if prediction == "ANOMALY":
            log_threat(
                connection, user["user_id"], operation,
                "Unusual update activity flagged by the Isolation Forest model; change was not applied.",
                "ANOMALY", score=anomaly_score,
            )
            return {
                "status": "BLOCKED",
                "prediction": prediction,
                "message": "Unusual activity detected. The student record was not changed.",
            }

        result = connection.execute(
            text("""
                UPDATE students
                SET name = :name, email = :email, semester = :semester
                WHERE student_id = :sid
            """),
            {"name": payload.name.strip(), "email": payload.email.strip(),
             "semester": payload.semester, "sid": payload.student_id},
        )
        if result.rowcount != 1:
            raise HTTPException(status_code=409, detail="Student record could not be updated.")

    return {
        "status": "UPDATED",
        "prediction": prediction,
        "message": "Student record updated successfully. Activity was logged.",
        "student_id": payload.student_id,
    }


@app.get("/admin/dashboard")
def admin_dashboard(authorization: str | None = Header(default=None)):
    admin_user(authorization)
    with engine.connect() as connection:
        total_queries = connection.execute(text("SELECT COUNT(*) FROM query_logs")).scalar() or 0
        normal_queries = connection.execute(text("SELECT COUNT(*) FROM query_logs WHERE status = 'NORMAL'")).scalar() or 0
        anomalies = connection.execute(text("SELECT COUNT(*) FROM query_logs WHERE status = 'ANOMALY'")).scalar() or 0
        blocked = connection.execute(text("SELECT COUNT(*) FROM threat_logs WHERE status = 'BLOCKED'")).scalar() or 0
        denied = connection.execute(text("SELECT COUNT(*) FROM threat_logs WHERE status = 'DENIED'")).scalar() or 0
        recent = connection.execute(text("""
            SELECT threat_id, user_id, operation, anomaly_score, reason, action, status
            FROM threat_logs ORDER BY threat_id DESC LIMIT 10
        """)).fetchall()
    return {
        "total_queries": total_queries,
        "normal_queries": normal_queries,
        "anomalies": anomalies,
        "blocked_operations": blocked,
        "denied_operations": denied,
        "recent_threats": [dict(row._mapping) for row in recent],
    }


@app.get("/predict-anomaly")
def predict_anomaly_test(query_length: int, execution_time: float,
                         rows_affected: int, rows_returned: int, hour: int):
    result = predict_anomaly(query_length, execution_time, rows_affected, rows_returned, hour)
    return {"prediction": result}


@app.get("/log-activity")
def log_activity(user_id: int, role: str, operation: str, query_length: int,
                 execution_time: float, rows_affected: int, rows_returned: int,
                 hour: int, ip_address: str):
    operation = operation.upper()
    if operation in ("DROP", "TRUNCATE", "ALTER"):
        with engine.begin() as connection:
            log_threat(connection, user_id, operation,
                       "Dangerous database operation blocked by security rule.", "BLOCKED", ip_address)
        return {"status": "BLOCKED", "message": "Dangerous operation blocked."}
    if role.lower() == "student" and operation != "SELECT":
        with engine.begin() as connection:
            log_threat(connection, user_id, operation,
                       "Unauthorized operation attempted by student role.", "DENIED", ip_address)
        return {"status": "DENIED", "message": "This role cannot perform that operation."}

    prediction = predict_anomaly(query_length, execution_time, rows_affected, rows_returned, hour)
    score = 1.0 if prediction == "ANOMALY" else 0.0
    with engine.begin() as connection:
        connection.execute(text("""
            INSERT INTO query_logs
            (user_id, role, operation, query_length, execution_time, rows_affected,
             rows_returned, hour, ip_address, anomaly_score, status)
            VALUES (:uid, :role, :op, :ql, :et, :ra, :rr, :hour, :ip, :score, :status)
        """), {"uid": user_id, "role": role, "op": operation, "ql": query_length,
              "et": execution_time, "ra": rows_affected, "rr": rows_returned,
              "hour": hour, "ip": ip_address, "score": score, "status": prediction})
        if prediction == "ANOMALY":
            log_threat(connection, user_id, operation,
                       "Unusual database activity detected by ML model.", "ANOMALY", ip_address, score)
    return {"status": prediction, "message": "Activity logged."}


@app.get("/dashboard")
def dashboard():
    return FileResponse("../frontend/dashboard.html")


@app.get("/login-page")
def login_page():
    return FileResponse("../frontend/login.html")


@app.get("/student")
def student_page():
    return FileResponse("../frontend/student.html")


@app.get("/student-data")
def student_data(student_id: int):
    with engine.connect() as connection:
        row = connection.execute(text("""
            SELECT student_id, name, email, semester FROM students WHERE student_id = :sid
        """), {"sid": student_id}).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="Student not found.")
    return dict(row._mapping)


@app.get("/student-courses")
def student_courses(student_id: int):
    with engine.connect() as connection:
        rows = connection.execute(text("""
            SELECT courses.course_id, courses.course_name, courses.credits,
                   enrollment.semester, enrollment.grade
            FROM enrollment JOIN courses ON enrollment.course_id = courses.course_id
            WHERE enrollment.student_id = :sid ORDER BY courses.course_id
        """), {"sid": student_id}).fetchall()
    return [dict(row._mapping) for row in rows]


@app.get("/student-summary")
def student_summary(student_id: int):
    with engine.connect() as connection:
        row = connection.execute(text("""
            SELECT COUNT(*) AS total_courses,
                   COALESCE(SUM(courses.credits), 0) AS total_credits,
                   COUNT(CASE WHEN enrollment.grade = 'A' THEN 1 END) AS grade_a,
                   COUNT(CASE WHEN enrollment.grade = 'B' THEN 1 END) AS grade_b,
                   COUNT(CASE WHEN enrollment.grade = 'C' THEN 1 END) AS grade_c,
                   COUNT(CASE WHEN enrollment.grade = 'D' THEN 1 END) AS grade_d,
                   COUNT(CASE WHEN enrollment.grade = 'F' THEN 1 END) AS grade_f
            FROM enrollment JOIN courses ON enrollment.course_id = courses.course_id
            WHERE enrollment.student_id = :sid
        """), {"sid": student_id}).fetchone()
    return dict(row._mapping)
