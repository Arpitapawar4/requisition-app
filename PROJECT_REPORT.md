# Project Report - Web-Based Student Academic Requisition Form with PDF Generation

## 1. Objective
Let a student fill in the institute's Student Academic Requisition Form online and download it as a
PDF that keeps the layout of the supplied form.

## 2. Tools
Python 3, Flask (web framework), SQLite (storage), ReportLab (PDF), HTML/CSS (UI), Pillow.

## 3. Workflow
Open app -> enter student details -> select application type -> enter purpose -> supporting
documents -> accept declaration -> Generate PDF -> Download PDF.

## 4. Features
- Inputs: department, name, roll no., semester, division, email, mobile, application type
  (Bonafide ... Other Request), purpose, documents attached Yes/No, document names, date.
- Declaration text from the form with a mandatory checkbox.
- Validation: mandatory fields, 10-digit mobile (starts 6-9), valid email, valid date, declaration
  accepted, allowed upload types (PDF/JPG/PNG, max 5 MB).
- PDF built to match the institute form: header with logo, processing-time note, sections 1-6.
  HoD signature/remarks, Forwarded to, Signature/remarks, Principal decision/remarks/signature and the
  Student Signature line are left blank. Department Outward No. is left for office use.
- File name: Requisition_RollNo_StudentName.pdf
- Storage: SQLite table `requisitions`.
- Bonus: automatic requisition number (REQ-YYYY-NNNN), automatic date, supporting document upload,
  application status tracking, admin dashboard (password), search and filter.

## 5. Database design
requisitions(id, req_no, department, student_name, roll_no, semester, division, email, mobile,
app_type, purpose, docs_attached, doc_names, req_date, status, created_at)

## 6. Modules
app.py - routes; db.py - SQLite functions; validators.py - checks; pdf_generator.py - form drawing.

## 7. Testing
Invalid email/mobile, missing fields and unticked declaration are rejected and nothing is saved.
Valid submissions get sequential numbers, store correctly, generate the PDF, appear in tracking and
admin search, and status updates work. Wrong upload types are rejected.

## 8. Conclusion
The app replaces manual form filling with a validated online form while keeping the official layout.
Future work: email notifications, per-student login, signature upload.
