"""Server-side validation for the requisition form."""
import re
from datetime import datetime

APPLICATION_TYPES = [
    "Bonafide", "Student Certificate", "Scholarship", "NOC",
    "Academic Permission", "Examination", "Internship", "Placement",
    "Other Request",
]
SEMESTERS = [str(i) for i in range(1, 9)]
STATUSES = [
    "Submitted", "Under HoD Review", "Forwarded", "Approved",
    "Not Approved", "Clarification Required",
]

EMAIL_RE = re.compile(r"^[A-Za-z0-9._%+\-]+@[A-Za-z0-9\-]+(\.[A-Za-z0-9\-]+)*\.[A-Za-z]{2,}$")
MOBILE_RE = re.compile(r"^[6-9]\d{9}$")        # 10-digit Indian mobile number
ROLL_RE = re.compile(r"^[A-Za-z0-9/\-]{1,20}$")
DIV_RE = re.compile(r"^[A-Za-z0-9]{1,3}$")

MAX_PURPOSE = 450


def validate(form: dict, declaration_accepted: bool, has_uploads: bool = False):
    """Return a dict {field: error message}. Empty dict means valid."""
    errors = {}

    def req(field, label):
        if not form.get(field, "").strip():
            errors[field] = f"{label} is required."
            return False
        return True

    req("department", "Department name")
    req("student_name", "Student name")
    if req("roll_no", "Roll number") and not ROLL_RE.match(form["roll_no"].strip()):
        errors["roll_no"] = "Roll number may contain only letters, digits, '-' and '/'."
    if req("semester", "Semester") and form["semester"] not in SEMESTERS:
        errors["semester"] = "Select a valid semester (1-8)."
    if req("division", "Division") and not DIV_RE.match(form["division"].strip()):
        errors["division"] = "Division must be 1-3 letters/digits."

    if req("email", "Email") and not EMAIL_RE.match(form["email"].strip()):
        errors["email"] = "Enter a valid email address."
    if req("mobile", "Mobile number") and not MOBILE_RE.match(form["mobile"].strip()):
        errors["mobile"] = "Mobile must be exactly 10 digits and start with 6-9."

    if req("app_type", "Application type") and form["app_type"] not in APPLICATION_TYPES:
        errors["app_type"] = "Select a valid application type."

    if req("purpose", "Purpose / details") and len(form["purpose"].strip()) > MAX_PURPOSE:
        errors["purpose"] = f"Purpose must be at most {MAX_PURPOSE} characters."

    if form.get("docs_attached") not in ("Yes", "No"):
        errors["docs_attached"] = "Select Yes or No."
    elif form["docs_attached"] == "Yes" and not (form.get("doc_names", "").strip() or has_uploads):
        errors["doc_names"] = "Enter the document name(s) or upload the files."
    if len(form.get("doc_names", "")) > 90:
        errors["doc_names"] = "Document names must be at most 90 characters."

    if req("date", "Date"):
        try:
            datetime.strptime(form["date"].strip(), "%Y-%m-%d")
        except ValueError:
            errors["date"] = "Enter a valid date."

    if not declaration_accepted:
        errors["declaration"] = "You must accept the declaration before submitting."
    return errors
