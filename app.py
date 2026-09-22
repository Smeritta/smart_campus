from flask import Flask, render_template, request, redirect,session
import sqlite3
import os

app = Flask(__name__)
app.secret_key = "college_project_secret"
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE = os.path.join(BASE_DIR, "database", "electricity.db")
os.makedirs(os.path.dirname(DATABASE), exist_ok=True)


def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def create_tables():

    conn = get_db()

    conn.execute("""
        CREATE TABLE IF NOT EXISTS rooms (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            room_no TEXT NOT NULL,
            block TEXT NOT NULL,
            department TEXT NOT NULL,
            room_type TEXT NOT NULL,
            status TEXT DEFAULT 'Active'
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS complaints (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            room_no TEXT NOT NULL,
            complaint TEXT NOT NULL,
            priority TEXT NOT NULL,
            status TEXT DEFAULT 'Open'
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS waste_alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            room_no TEXT NOT NULL,
            occupancy TEXT NOT NULL,
            power_usage REAL NOT NULL,
            message TEXT NOT NULL,
            status TEXT DEFAULT 'Active'
        )
    """)

    conn.commit()
    conn.close()


def check_waste(room_no, occupancy, power_usage):

    if occupancy == "Empty" and power_usage >= 2.0:

        conn = get_db()

        message = (
            f"High electricity usage detected "
            f"while {room_no} is empty."
        )

        conn.execute("""
            INSERT INTO waste_alerts
            (room_no, occupancy, power_usage, message)
            VALUES (?, ?, ?, ?)
        """, (
            room_no,
            occupancy,
            power_usage,
            message
        ))

        conn.commit()
        conn.close()

        return True

    return False


@app.route("/")
def login():
    return render_template("login.html")

@app.route("/login", methods=["POST"])
def login_user():

    email = request.form["email"]
    password = request.form["password"]
    role = request.form["role"]

    users = {
        "Admin": {
            "email": "admin@college.com",
            "password": "admin123"
        },
        "Staff": {
            "email": "staff@college.com",
            "password": "staff123"
        },
        "Student": {
            "email": "student@college.com",
            "password": "student123"
        }
    }

    if role in users:
        if (email == users[role]["email"] and
                password == users[role]["password"]):

            session["role"] = role
            session["email"] = email

            return redirect("/dashboard")

    return "Invalid email, password or role"
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")
def check_role(allowed_roles):

    if "role" not in session:
        return False

    return session["role"] in allowed_roles

@app.route("/dashboard")
def dashboard():
    if "role" not in session:
        return redirect("/")
    

    conn = get_db()

    total_rooms = conn.execute(
        "SELECT COUNT(*) FROM rooms"
    ).fetchone()[0]

    total_complaints = conn.execute(
        "SELECT COUNT(*) FROM complaints"
    ).fetchone()[0]

    total_alerts = conn.execute(
        "SELECT COUNT(*) FROM waste_alerts"
    ).fetchone()[0]

    active_rooms = conn.execute(
        "SELECT COUNT(*) FROM rooms WHERE status = 'Active'"
    ).fetchone()[0]

    alerts = conn.execute("""
        SELECT * FROM waste_alerts
        ORDER BY id DESC
        LIMIT 5
    """).fetchall()

    conn.close()

    return render_template(
        "dashboard.html",
        total_rooms=total_rooms,
        active_rooms=active_rooms,
        total_complaints=total_complaints,
        total_alerts=total_alerts,
        alerts=alerts
    )

@app.route("/rooms")
def rooms():
    if not check_role(["Admin"]):
        return "Access Denied", 403

    conn = get_db()

    rooms = conn.execute(
        "SELECT * FROM rooms ORDER BY id DESC"
    ).fetchall()

    conn.close()

    return render_template(
        "rooms.html",
        rooms=rooms
    )


@app.route("/add_room", methods=["POST"])
def add_room():

    room_no = request.form["room_no"]
    block = request.form["block"]
    department = request.form["department"]
    room_type = request.form["room_type"]

    conn = get_db()

    conn.execute("""
        INSERT INTO rooms
        (room_no, block, department, room_type)
        VALUES (?, ?, ?, ?)
    """, (
        room_no,
        block,
        department,
        room_type
    ))

    conn.commit()
    conn.close()

    return redirect("/rooms")


@app.route("/complaints")
def complaints():
    if not check_role(["Admin", "Staff", "Student"]):
        return "Access Denied", 403

    conn = get_db()

    complaints = conn.execute(
        "SELECT * FROM complaints ORDER BY id DESC"
    ).fetchall()

    conn.close()

    return render_template(
        "complaints.html",
        complaints=complaints
    )


@app.route("/add_complaint", methods=["POST"])
def add_complaint():
    if not check_role(["Admin", "Staff", "Student"]):
        return "Access Denied", 403

    room_no = request.form["room_no"]
    complaint = request.form["complaint"]
    priority = request.form["priority"]

    conn = get_db()

    conn.execute("""
        INSERT INTO complaints
        (room_no, complaint, priority)
        VALUES (?, ?, ?)
    """, (
        room_no,
        complaint,
        priority
    ))

    conn.commit()
    conn.close()

    return redirect("/complaints")


@app.route("/monitoring")
def monitoring():
    if not check_role(["Admin", "Staff"]):
        return "Access Denied", 403

    conn = get_db()

    alerts = conn.execute("""
        SELECT * FROM waste_alerts
        ORDER BY id DESC
    """).fetchall()

    conn.close()

    return render_template(
        "monitoring.html",
        alerts=alerts
    )


@app.route("/simulate", methods=["POST"])
def simulate():
    if not check_role(["Admin", "Staff"]):
        return "Access Denied", 403

    room_no = request.form["room_no"]
    occupancy = request.form["occupancy"]
    power_usage = float(request.form["power_usage"])

    check_waste(
        room_no,
        occupancy,
        power_usage
    )

    return redirect("/monitoring")

@app.route("/update_complaint/<int:complaint_id>",
           methods=["POST"])
def update_complaint(complaint_id):
    if not check_role(["Admin", "Staff"]):
        return "Access Denied", 403

    status = request.form["status"]

    conn = get_db()

    conn.execute("""
        UPDATE complaints
        SET status = ?
        WHERE id = ?
    """, (status, complaint_id))

    conn.commit()
    conn.close()

    return redirect("/complaints")
@app.route("/reports")
def reports():
    if not check_role(["Admin", "Staff"]):
        return "Access Denied", 403

    conn = get_db()

    total_rooms = conn.execute(
        "SELECT COUNT(*) FROM rooms"
    ).fetchone()[0]

    total_complaints = conn.execute(
        "SELECT COUNT(*) FROM complaints"
    ).fetchone()[0]

    total_alerts = conn.execute(
        "SELECT COUNT(*) FROM waste_alerts"
    ).fetchone()[0]

    alerts = conn.execute("""
        SELECT * FROM waste_alerts
        ORDER BY id DESC
    """).fetchall()

    conn.close()

    return render_template(
        "reports.html",
        total_rooms=total_rooms,
        total_complaints=total_complaints,
        total_alerts=total_alerts,
        alerts=alerts
    )


if __name__ == "__main__":
    app.run(debug=True)
