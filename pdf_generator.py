"""Draws the institute's Student Academic Requisition Form as a PDF.

Coordinates below were measured from the supplied form rendered at 80 dpi
(1 px = 0.9 pt, origin top-left) so the PDF keeps the same sections, order,
headings and blank official-use fields (HoD / Principal / Student signature).
"""
import io
import os
from datetime import datetime

from reportlab.lib.enums import TA_JUSTIFY
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.utils import simpleSplit
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.pdfgen import canvas
from reportlab.platypus import Paragraph

K = 0.9                      # px -> pt
PAGE_W, PAGE_H = A4
LOGO = os.path.join(os.path.dirname(__file__), "static", "logo.png")

DECLARATION = ("I certify that the information provided above is correct and that the request "
               "is being submitted for academic purposes. I understand that the request will be "
               "processed as per applicable Institute/University rules and within the stipulated "
               "processing time.")
PROCESSING = ("<b>Processing Time:</b> The request will normally be processed within 4 working days "
              "after receiving the completed form and all required supporting documents. Students "
              "are advised to apply in advance, as incomplete applications may require additional "
              "processing time.")


def _fmt_date(iso: str) -> str:
    try:
        return datetime.strptime(iso, "%Y-%m-%d").strftime("%d/%m/%Y")
    except ValueError:
        return iso


def build_pdf(d: dict) -> bytes:
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    c.setTitle(f"Requisition {d.get('req_no', '')}")
    c.setAuthor("Student Academic Requisition System")

    def X(px): return px * K
    def Y(py): return PAGE_H - py * K

    def text(px, py, s, font="Helvetica", size=10, align="left"):
        c.setFont(font, size)
        x, y = X(px), Y(py) - 3.5
        if align == "center":
            c.drawCentredString(x, y, s)
        else:
            c.drawString(x, y, s)

    def hline(x1, x2, py, w=0.6, gray=0):
        c.setLineWidth(w)
        c.setStrokeGray(gray)
        c.line(X(x1), Y(py), X(x2), Y(py))

    def fit(px, py, s, max_px, size=10):
        """Value text sitting on a line, shrunk to fit the line's width."""
        while size > 6 and stringWidth(s, "Helvetica", size) > max_px * K:
            size -= 0.5
        text(px, py - 3, s, size=size)

    def box(px, py, ticked=False):
        c.setLineWidth(0.8)
        c.setStrokeGray(0)
        c.rect(X(px), Y(py) - 8, 14 * K, 14 * K)
        if ticked:
            c.setLineWidth(1.6)
            c.line(X(px) + 2.5, Y(py) - 1.5, X(px) + 5.5, Y(py) - 5.5)
            c.line(X(px) + 5.5, Y(py) - 5.5, X(px) + 11, Y(py) + 3)

    def para(s, px, py_top, width_px, size, leading):
        style = ParagraphStyle("p", fontName="Helvetica", fontSize=size, leading=leading,
                               alignment=TA_JUSTIFY)
        p = Paragraph(s, style)
        w, h = p.wrapOn(c, width_px * K, 200)
        p.drawOn(c, X(px), Y(py_top) - h)
        return h

    L, R = 55, 608          # left / right margins (px)

    # ---- requisition number (auto) printed above the form ----
    if d.get("req_no"):
        c.setFont("Helvetica", 8)
        c.setFillGray(0.35)
        c.drawRightString(X(R), Y(31), f"Requisition No.: {d['req_no']}")
        c.setFillGray(0)

    # ---- header box ----
    c.setLineWidth(0.8)
    c.rect(X(L), Y(97), X(R - L), 57 * K)
    c.line(X(237), Y(40), X(237), Y(97))
    try:
        c.drawImage(LOGO, X(L + 12), Y(92), width=(237 - L - 24) * K,
                    height=(237 - L - 24) * K * 73 / 199, mask="auto",
                    preserveAspectRatio=True, anchor="c")
    except Exception:
        pass
    text(422, 51, "STUDENT ACADEMIC REQUISITION", "Helvetica-Bold", 14.5, "center")
    text(422, 75, "FORM", "Helvetica-Bold", 14.5, "center")

    # ---- department / outward no. / date row ----
    text(L, 120, "Name of the Department.:", "Helvetica-Bold", 9.5)
    dept_x = L + stringWidth("Name of the Department.:", "Helvetica-Bold", 9.5) / K + 4
    fit(dept_x, 122, d["department"], 285 - dept_x - 6, 9)
    text(288, 120, "Department Outward No.:", "Helvetica-Bold", 9.5)   # left blank (office use)
    text(515, 120, "Date:", "Helvetica-Bold", 9.5)
    text(546, 118, _fmt_date(d["date"]), size=9)

    hline(L, R, 143, 0.8)
    para(PROCESSING, L, 146, R - L, 9, 10.8)
    hline(L, R, 185, 0.8, 0.75)

    # ---- 1. student details ----
    text(L, 204, "1. STUDENT DETAILS", "Helvetica-Bold", 9.5)
    text(L, 225, "Name of Student:", size=9.5)
    hline(160, 498, 234); fit(164, 232, d["student_name"], 330)
    text(L, 254, "Roll No.:", size=9.5)
    hline(105, 212, 263); fit(108, 261, d["roll_no"], 100)
    text(222, 254, "Semester:", size=9.5)
    hline(272, 306, 263); fit(276, 261, d["semester"], 30)
    text(332, 254, "Division:", size=9.5)
    hline(375, 400, 263); fit(378, 261, d["division"], 22)
    text(L, 283, "Email / Mobile:", size=9.5)
    hline(132, 560, 292); fit(135, 290, f"{d['email']}  /  {d['mobile']}", 420)

    # application type: all options listed, the chosen one is ticked and bold
    text(L, 312, "Application for –", size=9.5)
    types = ["Bonafide", "Student Certificate", "Scholarship", "NOC", "Academic Permission",
             "Examination", "Internship", "Placement", "Other Request"]
    x, row = 138, 0
    y = 312
    for i, t in enumerate(types):
        chosen = (t == d["app_type"])
        font = "Helvetica-Bold" if chosen else "Helvetica"
        label = t + (" /" if i < len(types) - 1 else "")
        wpx = stringWidth(label, font, 9.5) / K + 6
        if x + wpx + 14 > R and row == 0:
            row, x, y = 1, L, 332
        if chosen:
            box(x, y - 1, True); x += 19
        text(x, y, label, font, 9.5)
        x += wpx

    # ---- 2. purpose (grows if text is long) ----
    text(L, 361, "2. PURPOSE / BRIEF DETAILS OF REQUEST", "Helvetica-Bold", 9.5)
    hdr_end = L + stringWidth("2. PURPOSE / BRIEF DETAILS OF REQUEST", "Helvetica-Bold", 9.5) / K + 6
    purpose = " ".join(d["purpose"].split())
    size = 9.5
    first_w = (R - hdr_end - 6) * K
    first_fit = simpleSplit(purpose, "Helvetica", size, first_w)
    first = first_fit[0]
    rest = purpose[len(first):].strip()
    rest_lines = simpleSplit(rest, "Helvetica", size, (R - L - 6) * K) if rest else []
    n_lines = 1 + len(rest_lines)
    extra = max(0, n_lines - 3) * 26
    hline(hdr_end, R, 371)
    text(hdr_end + 3, 367, first, size=size)
    for i in range(1, max(3, n_lines)):
        ly = 371 + 26 * i
        hline(L, R, ly)
        if i - 1 < len(rest_lines):
            text(L + 3, ly - 4, rest_lines[i - 1], size=size)

    def dy(v): return v + extra       # everything below shifts down if purpose is long

    # ---- 3. supporting documents ----
    text(L, dy(439), "3. SUPPORTING DOCUMENTS", "Helvetica-Bold", 9.5)
    text(L, dy(463), "Documents attached:", size=9.5)
    yes = d["docs_attached"] == "Yes"
    box(175, dy(463), yes);  text(199, dy(463), "Yes", size=9.5)
    box(224, dy(463), not yes);  text(248, dy(463), "No", size=9.5)
    text(L, dy(487), "Document name(s), if applicable:", size=9.5)
    docs_x = L + stringWidth("Document name(s), if applicable:", "Helvetica", 9.5) / K + 6
    hline(docs_x, 560, dy(496))
    if yes and d.get("doc_names"):
        fit(docs_x + 3, dy(494), d["doc_names"], 560 - docs_x - 6, 9)

    # ---- 4. declaration (student signature line is left blank to sign by hand) ----
    text(L, dy(512), "4. STUDENT DECLARATION", "Helvetica-Bold", 9.5)
    para(DECLARATION, L, dy(524), R - L, 9, 11.2)
    text(L, dy(586), "Student Signature:", size=9.5)
    hline(162, 265, dy(595))
    text(300, dy(586), "Date:", size=9.5)
    hline(325, 413, dy(595)); fit(328, dy(593), _fmt_date(d["date"]), 82, 9)

    # ---- 5. HoD (blank - institute use) ----
    text(L, dy(621), "5. HoD Signature:", "Helvetica-Bold", 9.5)
    hline(160, 262, dy(630))
    text(275, dy(621), "Remarks:", "Helvetica-Bold", 9.5)
    hline(326, R, dy(630))
    c.setFont("Helvetica", 9.5)
    para("Forwarded to <b>(</b>VICE PRINCIPAL/ CHIEF ACADEMIC OFFICER/ ACCOUNTS/ SPORTS/ PLACEMENT "
         "CELL/ SCHOLARSHIP CELL/ EXAM CELL) (if required)", L, dy(639), R - L, 9.5, 14)
    text(L, dy(710), "Signature:", "Helvetica-Bold", 9.5)
    hline(120, 224, dy(719))
    text(263, dy(710), "Remarks:", "Helvetica-Bold", 9.5)
    hline(319, R, dy(719))

    # ---- 6. principal office use only (blank) ----
    text(L, dy(734), "6. PRINCIPAL OFFICE USE ONLY", "Helvetica-Bold", 9.5)
    text(L, dy(759), "Decision by Principal.:", size=9.5)
    box(185, dy(759));  text(212, dy(759), "Approved", size=9.5)
    box(300, dy(759));  text(327, dy(759), "Not Approved", size=9.5)
    box(405, dy(759));  text(432, dy(759), "Clarification Required", size=9.5)
    text(L, dy(783), "Remarks (if any):", size=9.5)
    hline(145, R, dy(792))
    text(L, dy(810), "Principal Signature:", size=9.5)
    hline(150, 250, dy(819))

    c.showPage()
    c.save()
    return buf.getvalue()
