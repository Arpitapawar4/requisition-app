"""SQLite storage for requisitions."""
import os
import sqlite3
from datetime import datetime

DB_PATH = os.environ.get("REQ_DB", os.path.join(os.path.dirname(__file__), "requisitions.db"))

SCHEMA = """
CREATE TABLE IF NOT EXISTS requisitions (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    req_no        TEXT UNIQUE NOT NULL,
    department    TEXT NOT NULL,
    student_name  TEXT NOT NULL,
    roll_no       TEXT NOT NULL,
    semester      TEXT NOT NULL,
    division      TEXT NOT NULL,
    email         TEXT NOT NULL,
    mobile        TEXT NOT NULL,
    app_type      TEXT NOT NULL,
    purpose       TEXT NOT NULL,
    docs_attached TEXT NOT NULL,
    doc_names     TEXT,
    req_date      TEXT NOT NULL,
    status        TEXT NOT NULL DEFAULT 'Submitted',
    created_at    TEXT NOT NULL
);
"""


def connect():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with connect() as conn:
        conn.executescript(SCHEMA)


def add_requisition(d: dict) -> str:
    """Insert a requisition and return its automatic number, e.g. REQ-2026-0001."""
    year = datetime.now().year
    with connect() as conn:
        conn.execute("BEGIN IMMEDIATE")
        row = conn.execute(
            "SELECT COUNT(*) FROM requisitions WHERE req_no LIKE ?", (f"REQ-{year}-%",)
        ).fetchone()
        req_no = f"REQ-{year}-{row[0] + 1:04d}"
        conn.execute(
            """INSERT INTO requisitions (req_no, department, student_name, roll_no,
               semester, division, email, mobile, app_type, purpose, docs_attached,
               doc_names, req_date, status, created_at)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (req_no, d["department"], d["student_name"], d["roll_no"], d["semester"],
             d["division"], d["email"], d["mobile"], d["app_type"], d["purpose"],
             d["docs_attached"], d["doc_names"], d["date"], "Submitted",
             datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
        )
    return req_no


def get(req_no: str):
    with connect() as conn:
        return conn.execute("SELECT * FROM requisitions WHERE req_no = ?", (req_no,)).fetchone()


def search(q: str = "", status: str = "", app_type: str = ""):
    sql, args = "SELECT * FROM requisitions WHERE 1=1", []
    if q:
        sql += " AND (req_no LIKE ? OR student_name LIKE ? OR roll_no LIKE ? OR department LIKE ?)"
        args += [f"%{q}%"] * 4
    if status:
        sql += " AND status = ?"
        args.append(status)
    if app_type:
        sql += " AND app_type = ?"
        args.append(app_type)
    sql += " ORDER BY id DESC"
    with connect() as conn:
        return conn.execute(sql, args).fetchall()


def status_counts():
    with connect() as conn:
        rows = conn.execute("SELECT status, COUNT(*) c FROM requisitions GROUP BY status").fetchall()
    return {r["status"]: r["c"] for r in rows}


def update_status(req_no: str, status: str):
    with connect() as conn:
        conn.execute("UPDATE requisitions SET status = ? WHERE req_no = ?", (status, req_no))
