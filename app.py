"""Web-Based Student Academic Requisition Form with PDF generation (Flask)."""
import hmac
import os
import re
import secrets
import time
from datetime import date
from functools import wraps
from io import BytesIO

from flask import (Flask, abort, flash, redirect, render_template, request,
                   send_file, session, url_for)
from werkzeug.utils import secure_filename

import db
from pdf_generator import DECLARATION, build_pdf
from validators import APPLICATION_TYPES, SEMESTERS, STATUSES, validate

BASE = os.path.dirname(os.path.abspath(__file__))
UPLOAD_DIR = os.environ.get("UPLOAD_DIR", os.path.join(BASE, "uploads"))
ALLOWED_EXT = {"pdf", "jpg", "jpeg", "png"}
MAX_FILE_MB = 5

app = Flask(__name__)
# No hard-coded secrets: without SECRET_KEY a random one is used (sessions reset on restart).
app.secret_key = os.environ.get("SECRET_KEY") or secrets.token_hex(32)
app.config["MAX_CONTENT_LENGTH"] = 25 * 1024 * 1024
# Admin login is DISABLED unless ADMIN_PASSWORD is set (see the __main__ block for local use).
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "")

MAX_ATTEMPTS = 5            # wrong passwords allowed ...
LOCK_SECONDS = 5 * 60       # ... before that client is blocked for 5 minutes
_failed = {}                # client ip -> (count, locked_until)


def client_ip() -> str:
    fwd = request.headers.get("X-Forwarded-For", "")
    return fwd.split(",")[-1].strip() if fwd else (request.remote_addr or "?")

db.init_db()
os.makedirs(UPLOAD_DIR, exist_ok=True)

FIELDS = ["department", "student_name", "roll_no", "semester", "division", "email",
          "mobile", "app_type", "purpose", "docs_attached", "doc_names", "date"]


def pdf_filename(row) -> str:
    clean = lambda s: re.sub(r"[^A-Za-z0-9]+", "_", s).strip("_")
    return f"Requisition_{clean(row['roll_no'])}_{clean(row['student_name'])}.pdf"


def row_to_pdf_data(row) -> dict:
    return {
        "req_no": row["req_no"], "department": row["department"],
        "student_name": row["student_name"], "roll_no": row["roll_no"],
        "semester": row["semester"], "division": row["division"],
        "email": row["email"], "mobile": row["mobile"], "app_type": row["app_type"],
        "purpose": row["purpose"], "docs_attached": row["docs_attached"],
        "doc_names": row["doc_names"] or "", "date": row["req_date"],
    }


def valid_uploads(files):
    return [f for f in files if f and f.filename]


@app.route("/", methods=["GET", "POST"])
def index():
    form = {k: "" for k in FIELDS}
    form["date"] = date.today().isoformat()           # automatic date (editable)
    form["docs_attached"] = "No"
    errors = {}
    if request.method == "POST":
        form = {k: request.form.get(k, "").strip() for k in FIELDS}
        declared = request.form.get("declaration") == "on"
        files = valid_uploads(request.files.getlist("documents"))

        errors = validate(form, declared, has_uploads=bool(files))
        for f in files:                                 # validate uploads
            ext = f.filename.rsplit(".", 1)[-1].lower() if "." in f.filename else ""
            f.stream.seek(0, os.SEEK_END)
            size = f.stream.tell()
            f.stream.seek(0)
            if ext not in ALLOWED_EXT:
                errors["documents"] = "Only PDF, JPG and PNG files are allowed."
            elif size > MAX_FILE_MB * 1024 * 1024:
                errors["documents"] = f"Each file must be at most {MAX_FILE_MB} MB."

        if not errors:
            saved = []
            if form["docs_attached"] == "Yes":
                saved = [secure_filename(f.filename) for f in files]
            names = [n.strip() for n in form["doc_names"].split(",") if n.strip()]
            for s in saved:                             # auto-fill names from uploads
                if s not in names:
                    names.append(s)
            form["doc_names"] = ", ".join(names) if form["docs_attached"] == "Yes" else ""
            req_no = db.add_requisition(form)
            if saved:
                folder = os.path.join(UPLOAD_DIR, req_no)
                os.makedirs(folder, exist_ok=True)
                for f in files:
                    f.save(os.path.join(folder, secure_filename(f.filename)))
            return redirect(url_for("result", req_no=req_no))
        flash("Please correct the highlighted errors.", "error")
    return render_template("form.html", form=form, errors=errors, types=APPLICATION_TYPES,
                           semesters=SEMESTERS, declaration=DECLARATION,
                           declared=request.form.get("declaration") == "on")


@app.route("/result/<req_no>")
def result(req_no):
    row = db.get(req_no) or abort(404)
    return render_template("result.html", r=row, filename=pdf_filename(row))


@app.route("/download/<req_no>")
def download(req_no):
    row = db.get(req_no) or abort(404)
    pdf = build_pdf(row_to_pdf_data(row))
    return send_file(BytesIO(pdf), mimetype="application/pdf", as_attachment=True,
                     download_name=pdf_filename(row))


@app.route("/track", methods=["GET", "POST"])
def track():
    row, searched = None, False
    req_no = request.values.get("req_no", "").strip().upper()
    if req_no:
        searched = True
        row = db.get(req_no)
    return render_template("track.html", r=row, searched=searched, req_no=req_no,
                           statuses=STATUSES)


# ----------------------------- admin ---------------------------------------
def admin_required(fn):
    @wraps(fn)
    def wrapper(*a, **kw):
        if not session.get("admin"):
            return redirect(url_for("admin_login"))
        return fn(*a, **kw)
    return wrapper


@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if not ADMIN_PASSWORD:
        return render_template("admin_login.html", disabled=True)
    ip = client_ip()
    count, locked_until = _failed.get(ip, (0, 0))
    wait = int(locked_until - time.time())
    if wait > 0:
        flash(f"Too many failed attempts. Try again in {wait // 60 + 1} minute(s).", "error")
        return render_template("admin_login.html", disabled=False), 429
    if request.method == "POST":
        given = request.form.get("password", "")
        if hmac.compare_digest(given.encode(), ADMIN_PASSWORD.encode()):
            _failed.pop(ip, None)
            session["admin"] = True
            return redirect(url_for("admin"))
        count += 1
        if count >= MAX_ATTEMPTS:
            _failed[ip] = (0, time.time() + LOCK_SECONDS)
            flash("Too many failed attempts. Login blocked for 5 minutes.", "error")
        else:
            _failed[ip] = (count, 0)
            flash(f"Incorrect password. {MAX_ATTEMPTS - count} attempt(s) left.", "error")
    return render_template("admin_login.html", disabled=False)


@app.route("/admin/logout")
def admin_logout():
    session.pop("admin", None)
    return redirect(url_for("index"))


@app.route("/admin")
@admin_required
def admin():
    q = request.args.get("q", "").strip()
    status = request.args.get("status", "")
    app_type = request.args.get("app_type", "")
    rows = db.search(q, status, app_type)
    counts = db.status_counts()
    return render_template("admin.html", rows=rows, counts=counts, total=sum(counts.values()),
                           q=q, status=status, app_type=app_type, statuses=STATUSES,
                           types=APPLICATION_TYPES)


@app.route("/admin/status/<req_no>", methods=["POST"])
@admin_required
def admin_status(req_no):
    new = request.form.get("status")
    if new in STATUSES and db.get(req_no):
        db.update_status(req_no, new)
        flash(f"{req_no} marked as {new}.", "ok")
    return redirect(request.referrer or url_for("admin"))


@app.route("/admin/files/<req_no>/<name>")
@admin_required
def admin_file(req_no, name):
    path = os.path.join(UPLOAD_DIR, secure_filename(req_no), secure_filename(name))
    if not os.path.isfile(path):
        abort(404)
    return send_file(path)


@app.context_processor
def inject_helpers():
    def uploaded_files(req_no):
        folder = os.path.join(UPLOAD_DIR, req_no)
        return sorted(os.listdir(folder)) if os.path.isdir(folder) else []
    return {"uploaded_files": uploaded_files}


if __name__ == "__main__":
    if not ADMIN_PASSWORD:      # local testing only; gunicorn on a server never runs this block
        ADMIN_PASSWORD = "admin123"
        print("WARNING: using local test password 'admin123'. Set ADMIN_PASSWORD before deploying.")
    app.run(debug=True, host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
