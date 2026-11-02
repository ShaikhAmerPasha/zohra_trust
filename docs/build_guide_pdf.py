"""Build Zohra_Trust_Flow_Guide.pdf from the text below and the screenshots in flow_run/shots.

Run from anywhere with the bench Python (it has weasyprint):

    /home/ameer/Desktop/frappe-bench/env/bin/python apps/zohra_trust/docs/build_guide_pdf.py

The numbers are from one complete run on "Demo Hostel Two" (5 girls, June to September 2026).
To refresh the guide after a change: redo the run, replace the screenshots, edit the text, run this again.
"""

from html import escape
from pathlib import Path

from weasyprint import HTML

HERE = Path(__file__).parent
SHOTS = HERE / "flow_run" / "shots"
OUT = HERE / "Zohra_Trust_Flow_Guide.pdf"

CSS = """
@page { size: A4; margin: 16mm 14mm 16mm 14mm; @bottom-center { content: "Zohra Trust ERPNext: flow guide  -  page " counter(page); font-size: 8pt; color: #777; } }
body { font-family: "Liberation Sans", Arial, sans-serif; font-size: 10pt; color: #222; line-height: 1.4; }
h1 { font-size: 22pt; margin: 0 0 4pt; color: #1b4d3e; }
h2 { font-size: 14pt; color: #1b4d3e; border-bottom: 2px solid #1b4d3e; padding-bottom: 2pt; margin: 18pt 0 6pt; page-break-after: avoid; }
h3 { font-size: 11pt; margin: 10pt 0 3pt; page-break-after: avoid; }
.sub { color: #555; font-size: 11pt; margin-bottom: 14pt; }
.when { background: #eef5f2; border-left: 4px solid #1b4d3e; padding: 5pt 8pt; margin: 4pt 0 6pt; }
ol, ul { margin: 3pt 0 6pt 18pt; padding: 0; } li { margin-bottom: 2pt; }
figure { margin: 6pt 0 10pt; page-break-inside: avoid; } figure img { width: 100%; border: 1px solid #bbb; }
figcaption { font-size: 8.5pt; color: #555; margin-top: 2pt; }
figure.small img { width: 62%; } figure.page img { width: 70%; }
table { border-collapse: collapse; width: 100%; margin: 4pt 0 8pt; } th, td { border: 1px solid #999; padding: 3pt 5pt; text-align: left; vertical-align: top; } th { background: #e6e6e6; }
.flow { font-family: "Liberation Mono", monospace; font-size: 8.5pt; background: #f4f4f4; padding: 6pt; white-space: pre; border: 1px solid #ccc; }
.note { color: #7a4b00; background: #fff6e6; padding: 4pt 7pt; border-left: 4px solid #d99a2b; margin: 5pt 0; }
.toc li { margin-bottom: 1pt; }
.cover { margin-top: 70pt; }
"""

FLOW = """Set up once        Every day              Every month           Once a year       Every half-year
-------------      ------------           -------------         ------------      ---------------
Trust Settings     Purchase Invoice       Boarding Attendance   Result Sheet      Report Pack
Unit Profile       Material Consumption   Food Statement        Promote           Preview, PDF
Students           Cash Bank Voucher      Receipts & Payments
Opening stock"""

# Each section: (title, when/who, steps, [(image file, caption, css class)], optional note)
SECTIONS = [
    (
        "1. Set up once",
        "When: when a hostel starts using the system. Who: the administrator. A developer first runs <b>create_unit</b> for the hostel (company, accounts, Hostel Store, items, sanction of 150 girls at Rs 850).",
        [
            "Open <b>Trust Settings</b>: trust name, registration number, current academic year, and the officer bearers (name, designation, qualification, phone, sort order). They print on the letterhead of the report. Untick Is Active for someone who has left.",
            "Open <b>Trust Unit Profile</b> and the hostel. Check the address, the ration warehouse and the sanction history (150 girls, Rs 850, from 1 April 2026). Type the <b>Letter Text</b> and the <b>Appendix - H Text</b>. In the letter you may write {{ from_date }}, {{ to_date }} or {{ period }}.",
            "When the department changes the strength or the rate, <b>add a new row</b> to Sanctions with the start date. Never edit the old row.",
        ],
        [("01-unit-profile.jpg", "Trust Unit Profile of Demo Hostel Two: tracks residents, food statement and results; Hostel Store; address; sanction 150 at Rs 850.", "")],
        None,
    ),
    (
        "2. Students and enrollments",
        "When: at admission, and at the start of each academic year. Who: the office. A new girl can join only at the start of an academic year.",
        [
            "Open <b>Trust Student</b> and click Add. Type the name, choose the hostel, the admission date. Tick <b>Has Guardian</b> and add the father's name if there is one: it prints after her name on the result sheet. Save.",
            "Open <b>Student Enrollment</b> and click Add. Choose the student, the academic year (2026-27), the hostel, her school (English or Kannada Medium), her class, her register number and the date. Status <b>Enrolled</b>. Save.",
            "The system refuses a girl above the sanctioned strength and a register number that is already used.",
            "In this run: 5 girls: two in class 8, one in class 9, two in class 10.",
        ],
        [
            ("02-student-form.jpg", "New Trust Student with a guardian.", "small"),
            ("03-enrollment-form.jpg", "New Student Enrollment (the dropdown is the student search).", "small"),
            ("04-enrollment-list.jpg", "All five girls enrolled.", ""),
        ],
        None,
    ),
    (
        "3. Opening stock (go-live)",
        "When: once, before the first Food Expenditure Statement. Who: the store keeper or accountant.",
        [
            "Count the food in the store on the last day before the first statement's month.",
            "Open <b>Stock Reconciliation</b>. Purpose <b>Opening Stock</b>, the date, the company. Add a row for every item with the <b>quantity and the valuation rate</b> (without a rate the opening amount is zero). Here: Rice 60 kg at Rs 52 and Sugar 8 kg at Rs 56.",
            "Save and Submit. The difference amount shows the stock value: Rs 3,568.",
        ],
        [("05-stock-draft.jpg", "Stock count, draft.", "small"), ("06-stock-submitted.jpg", "Submitted: Rs 3,568.", "small")],
        None,
    ),
    (
        "4. Every day: purchases",
        "When: each day something is bought. Who: Store or Data Entry.",
        [
            "Open <b>Purchase Invoice</b>. Supplier <b>Cash purchase</b>, the date, the company.",
            "Tick <b>Update Stock</b> and choose the warehouse <b>Hostel Store</b>. Tick <b>Is Paid</b>, mode <b>Cash</b>, the cash account.",
            "Add the items. Rice, Sugar and the other food items add to stock. Vegetables, Mutton, Milk and Fuel are not stocked: they only count as spending.",
            "Save, check the total, Submit. Here: Rice 80 x Rs 52, Sugar 15 x Rs 56, Vegetables Rs 1,800 = Rs 6,800.",
        ],
        [("07-purchase-draft.jpg", "Cash purchase, draft.", "small"), ("08-purchase-submitted.jpg", "Submitted and paid: Rs 6,800.", "small")],
        None,
    ),
    (
        "5. Every day: what the kitchen used",
        "When: every day. Who: Store. One entry per hostel per day.",
        [
            "Open <b>Material Consumption</b>, choose the hostel and the date.",
            "Click <b>Copy Yesterday</b>: it fills yesterday's items and quantities. Change the quantities if today's use differs.",
            "Save and Submit. The items leave the stock (a Stock Entry is made automatically). A second entry for the same day is refused.",
            "Here: Rice 35 kg and Sugar 4 kg on 15 June, copied to 16 June.",
        ],
        [("09-consumption-copy-yesterday.jpg", "Copy Yesterday filled the items.", "small"), ("10-consumption-submitted.jpg", "Submitted; the Stock Entry is linked.", "small")],
        None,
    ),
    (
        "6. Every day: money in and out",
        "When: for every receipt and every payment that is not a shop purchase. Who: Data Entry.",
        [
            "Open <b>Cash Bank Voucher</b>. Choose <b>Receipt</b> or <b>Payment</b>, the date, <b>Cash</b> or <b>Bank</b> (for Bank also choose the bank account).",
            "Choose the <b>Account Head</b> (Govt. grant received, Loan from Zohra trust, Salaries, and so on) and the amount. Save and Submit.",
            "The department pays the grant once every six months, as one receipt, Rs 850 per girl per month in full. Here: 5 girls x 850 x 6 months = <b>Rs 25,500</b> on Govt. grant received. Salaries Rs 9,500 were a Payment; a loan of Rs 30,000 from the Trust was a Receipt.",
            "Submitting makes the Journal Entry automatically. Never edit or cancel that entry yourself: cancel the voucher.",
        ],
        [("11-receipt-draft.jpg", "Receipt, draft.", "small"), ("12-receipt-submitted.jpg", "Submitted; the Journal Entry is made.", "small")],
        None,
    ),
    (
        "7. Every month: Boarding Attendance",
        "When: at the end of each month. Who: Data Entry.",
        [
            "Open <b>Boarding Attendance</b>, choose the hostel and the month.",
            "Under School working days add one row per school with the days it ran (here English 26, Kannada 25).",
            "Click <b>Fill Girls</b>. Every enrolled girl appears with her school days and hostel days (all days of the month). Change a girl's days only if she was absent, and write the reason. Days cannot be more than the days in the month or the days the school ran.",
            "Save, check the totals, Submit. Here: 5 girls, 150 hostel days, Rs 4,250 grant (5 x Rs 850).",
        ],
        [("13-attendance-rows.jpg", "The girls and the totals.", "small"), ("14-attendance-submitted.jpg", "Submitted.", "small")],
        None,
    ),
    (
        "8. Every month: Food Expenditure Statement",
        "When: after the month's purchases and kitchen entries are in. Who: Store. Nothing is typed: click Fill.",
        [
            "Open <b>Food Expenditure Statement</b>, choose the hostel and the month. Tick <b>Is Opening</b> only for the very first statement.",
            "Click <b>Fill</b>. <b>Old balance</b> is the real stock at the end of the day before the month, valued at the last statement's closing rate (or the stock rate for the first one). <b>Purchased</b> comes from the Purchase Invoices, <b>Expenditure</b> from Material Consumption. Vegetables, Mutton, Milk, Fuel, Salaries and GESCOM come from the money actually spent.",
            "Save, check the lines and totals, Submit. A yellow message afterwards means the statement and the stock differ: look at it before filing.",
            "Here, June: opening Rs 3,568; purchase Rs 16,300 (stock Rs 5,000, vegetables Rs 1,800, salaries Rs 9,500); spent Rs 15,388 (Rice 70 kg at Rs 52 = Rs 3,640); closing Rs 4,480.",
            "July, August and September were made the same way. The old balance of each month is the real stock, so the months chain by themselves.",
        ],
        [("15-food-lines.jpg", "June: old balance from the real stock.", "small"), ("16-food-submitted.jpg", "June submitted.", "small"), ("17-food-list.jpg", "The four monthly statements.", "")],
        "No statement is made for April and May. April's purchases are entered in March.",
    ),
    (
        "9. Receipts and Payments Account",
        "When: for the half-year (1 April to 30 September), and any time to check. Who: anyone with access.",
        [
            "Open the report <b>Receipts and Payments Account</b>. Choose the hostel and the dates.",
            "The two columns must add up to the same total. Opening cash and bank, the loan, the grant, food, salaries and the closing balances all come from the entries above.",
            "Here: both sides Rs 2,45,500. Opening cash 40,000 and bank 1,50,000; loan 30,000; grant 25,500; Food 30,200; Salaries 42,500; closing cash 22,800 and bank 1,50,000.",
        ],
        [("18-receipts-payments.jpg", "The report for 1 April to 30 September.", "")],
        None,
    ),
    (
        "10. Once a year: results and promotion",
        "When: after the Final exam. Who: the administrator (who enters all marks).",
        [
            "Open <b>Result Sheet of Inmates</b>: hostel, academic year, exam <b>Final</b>, the exam date. Click <b>Fill Students</b>: every enrolled girl appears with the maximum marks of her class (480 for classes 6 to 9, 625 for class 10).",
            "Enter the marks and the result (Pass, Fail or Absent). The <b>Promotion Action</b> fills itself: Pass becomes Promote (class 10: Complete, then choose where she goes); Fail becomes Repeat. A failed girl may instead be set to <b>Left with T.C.</b> (in any class). Absent is left for you to choose.",
            "Save, check the totals (here 5 appeared, 3 passed, 2 failed) and Submit.",
            "A <b>Promote</b> button appears. Click it and confirm. Next year's enrollments are made with status <b>Planned</b>; a girl who completed becomes <b>Passed Out</b>; a girl who left with a T.C. becomes <b>Left</b>. It can be done only once.",
            "Here: Zainab and Rukhsar move to class 9, Nazia repeats class 9, Sana (class 10) is Passed Out, Farheen (failed class 10) Left with T.C.",
            "When the Transfer Certificate is issued, open that student and fill the <b>T.C. number</b> and <b>T.C. date</b>. At the start of the new year, change each Planned enrollment to <b>Enrolled</b>.",
        ],
        [
            ("19-result-fill.jpg", "Fill Students: classes and maximum marks.", "small"),
            ("20-result-submitted.jpg", "Submitted: 3 passed, 2 failed; the Promote button.", "small"),
            ("21-promote-confirm.jpg", "Promote confirmation.", "small"),
            ("22-next-year.jpg", "Next year's enrollments (Planned).", "small"),
            ("23-student-status.jpg", "Student status after promotion.", ""),
        ],
        None,
    ),
    (
        "11. Every half-year: the Report Pack",
        "When: to file the half-yearly report. Who: the administrator or Principal.",
        [
            "Open <b>Report Pack</b> and click Add: the hostel, from date 1 April, to date 30 September. Save. It lists the pages in filing order: Letter; Receipts and payments; Abstract of attendance; Food expenditure statements; Appendix - H; List of officer bearer; List of staff; Result sheet; School: College attendance registers (Kannada).",
            "Untick <b>Include</b> to leave a page out. Drag a row to change the order. <b>Standard Pages</b> puts the list back as it was.",
            "To add a page that is not generated (the CA's balance sheet, the building plan, a signed scan): add a row, choose <b>Uploaded page</b>, give it a title and attach the PDF, PNG or JPG. Put the row where it should print.",
            "The staff list comes from the active <b>Employee</b> records of the hostel (name, designation, first qualification). The Grant Bill is not in the pack yet: its format is still to come from Zohra.",
            "Click <b>Preview</b>. The window first says it is building the PDF (up to 20 seconds), then shows the pack. The orange box lists what to fix before filing: a month with no submitted attendance or food statement, no staff records, a missing uploaded file. April and May are never listed. Fix it, click Preview again. When the box is gone, click <b>Download PDF</b> and print.",
            "Here: all four months were entered, so the pack is 19 pages and the box is empty.",
        ],
        [
            ("24-pack-pages.jpg", "The Report Pack and its pages.", "small"),
            ("25-preview-loading.jpg", "Preview: 19 pages, nothing to fix.", ""),
            ("26-preview-complete.jpg", "The PDF in the preview window.", ""),
        ],
        None,
    ),
    (
        "12. The finished report",
        "The file Zohra_half_yearly_report_HOSTEL_TWO.pdf (same folder) is the 19-page pack from this run: letter, receipts and payments, abstract, four food statements, Appendix - H, officer bearers, staff list, result sheet and eight Kannada attendance registers. Sample pages:",
        [],
        [
            ("27-report-receipts-payments.png", "Receipts and Payments page.", "page"),
            ("29-report-abstract.png", "Abstract statement of attendance.", "page"),
            ("28-report-food-june.png", "Food expenditure statement, June (landscape).", ""),
            ("30-report-result-sheet.png", "Result sheet of inmates.", "page"),
            ("31-report-register-kannada-school.png", "School: College attendance register, Kannada heading.", "page"),
        ],
        "The data is dummy: five girls and small quantities. The layouts and the way each number is built are the real ones.",
    ),
]

TAIL = [
    (
        "13. Fixing a mistake",
        None,
        [
            "<b>Draft:</b> edit and Save.",
            "<b>Submitted:</b> click <b>Cancel</b> on that document and confirm, then <b>Amend</b> to make a corrected copy. Cancelling a Material Consumption puts the food back in stock; cancelling a Cash Bank Voucher removes its journal entry.",
            "A user can cancel only their own entries, and only within the number of days set in Trust Settings (1 by default). The Principal can cancel anyone's.",
            "A month closed by the Principal (Accounting Period) refuses new entries.",
        ],
        [],
        None,
    ),
]

MESSAGES = [
    ("Sanctioned strength reached", "The hostel is full. Free a seat, or ask for a new Unit Sanction row."),
    ("Hostel Days must be between 0 and 30", "Correct that girl's days."),
    ("A document for that month, day or exam already exists", "Open the existing one instead of making another."),
    ("Statement balance differs from stock", "Check the month's consumption and purchases, or the physical count."),
    ("Leaving Destination is required", "Choose where a girl who completed class 10 goes next."),
    ("Nothing to print / No submitted ... for <month>", "Enter or submit that month's attendance or food statement, then Preview again."),
]


def figure(name, caption, css):
    path = SHOTS / name
    return f'<figure class="{css}"><img src="{path.as_uri()}"><figcaption>{escape(caption)}</figcaption></figure>'


def section(title, when, steps, images, note):
    out = [f"<h2>{escape(title)}</h2>"]
    if when:
        out.append(f'<div class="when">{when}</div>')
    if steps:
        out.append("<ol>" + "".join(f"<li>{s}</li>" for s in steps) + "</ol>")
    if note:
        out.append(f'<div class="note">{escape(note)}</div>')
    out += [figure(*i) for i in images]
    return "\n".join(out)


def build():
    toc = "".join(f"<li>{escape(s[0])}</li>" for s in SECTIONS + TAIL) + "<li>14. If the system stops you</li>"
    body = [
        '<div class="cover"><h1>Zohra Trust ERPNext</h1><div class="sub">The flow, step by step: what to do, in which order, and what you will see.<br>Zohra Minority Girls Hostel. Example run on "Demo Hostel Two", June to September 2026.</div>',
        "<h3>The rule of the whole system</h3><p>You enter each thing <b>once</b>, as it happens. The monthly sheets and the half-yearly report are built from what you entered. You never type the same number twice.</p>",
        f'<div class="flow">{escape(FLOW)}</div>',
        "<h3>Buttons used everywhere</h3><p><b>Save</b> (Ctrl+S) keeps a draft. <b>Submit</b> makes it final. <b>Cancel</b> takes a final document back. Always check a draft before you submit it.</p>",
        f'<h3>Contents</h3><ul class="toc">{toc}</ul></div>',
    ]
    body += [section(*s) for s in SECTIONS + TAIL]
    rows = "".join(f"<tr><td>{escape(m)}</td><td>{escape(a)}</td></tr>" for m, a in MESSAGES)
    body.append(f"<h2>14. If the system stops you</h2><p>The wording on screen may differ a little.</p><table><tr><th>Message</th><th>What to do</th></tr>{rows}</table>")
    html = f"<html><head><meta charset='utf-8'><style>{CSS}</style></head><body>{''.join(body)}</body></html>"
    HTML(string=html, base_url=str(HERE)).write_pdf(OUT)
    print("wrote", OUT)


if __name__ == "__main__":
    build()
