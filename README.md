# Student Academic Requisition Form - PDF Generator

Flask web app: a student fills in the institute's Student Academic Requisition Form online,
the data is stored in SQLite and the completed form is downloaded as a PDF that follows the
institute's layout. HoD, Principal and Student-signature fields stay blank for manual use.

## Run
    pip install -r requirements.txt
    python app.py            # open http://127.0.0.1:5000

Environment variables: ADMIN_PASSWORD (required on a server: admin login is disabled without it),
SECRET_KEY (random text), PORT. When run locally with `python app.py` and no ADMIN_PASSWORD, the
test password `admin123` is used. Admin login blocks a client for 5 minutes after 5 wrong attempts.

## Pages
- /        student form -> Generate PDF -> result page with Download PDF
- /track   check status by requisition number
- /admin   (login) dashboard: counts, search/filter, change status, view uploaded files

## Files
app.py (routes) | db.py (SQLite) | validators.py | pdf_generator.py (ReportLab, form layout)
templates/ static/ | uploads/ (supporting documents) | requisitions.db (created on first run)

## Deploy (Render or any host)
Build: pip install -r requirements.txt     Start: gunicorn app:app
Set ADMIN_PASSWORD (strong) and SECRET_KEY. Free hosts may reset the SQLite file/uploads on restart.
