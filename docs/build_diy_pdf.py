"""Build Zohra_Trust_Do_It_Yourself.pdf: a hands-on workbook for doing the whole flow by hand in an empty hostel.

    /home/ameer/Desktop/frappe-bench/env/bin/python apps/zohra_trust/docs/build_diy_pdf.py

The empty hostel is made by:  bench --site <site> execute zohra_trust.tests.demo_data.setup_site --kwargs "{'company':'Practice Hostel','abbr':'PRH'}"
Every figure below is checked by tests/test_workbook.py, so the workbook and the system cannot drift apart.
"""

from html import escape
from pathlib import Path

from weasyprint import HTML

HERE = Path(__file__).parent
SHOTS = HERE / "flow_run" / "shots"
OUT = HERE / "Zohra_Trust_Do_It_Yourself.pdf"

CSS = """
@page { size: A4; margin: 15mm 13mm; @bottom-center { content: "Zohra Trust: do it yourself  -  page " counter(page); font-size: 8pt; color: #777; } }
body { font-family: "Liberation Sans", Arial, sans-serif; font-size: 9.6pt; color: #222; line-height: 1.38; }
h1 { font-size: 22pt; margin: 0 0 4pt; color: #1b4d3e; } h2 { font-size: 14pt; color: #1b4d3e; border-bottom: 2px solid #1b4d3e; padding-bottom: 2pt; margin: 16pt 0 6pt; page-break-after: avoid; }
h3 { font-size: 11pt; margin: 8pt 0 3pt; page-break-after: avoid; } .sub { color: #555; font-size: 11pt; margin-bottom: 12pt; }
table { border-collapse: collapse; width: 100%; margin: 4pt 0 6pt; font-size: 8.8pt; } th, td { border: 1px solid #999; padding: 2.5pt 4pt; vertical-align: top; text-align: left; } th { background: #e6e6e6; } tr { page-break-inside: avoid; }
.step { border: 1.5px solid #1b4d3e; border-radius: 5pt; margin: 10pt 0; padding: 0 0 4pt; page-break-inside: avoid; }
.step .head { background: #1b4d3e; color: #fff; padding: 4pt 8pt; font-weight: bold; font-size: 10.5pt; border-radius: 3pt 3pt 0 0; }
.step .body { padding: 2pt 9pt; } .lab { font-weight: bold; color: #1b4d3e; margin-top: 4pt; }
.see { background: #eef5f2; padding: 3pt 7pt; border-left: 4px solid #1b4d3e; margin: 3pt 0; }
.went { background: #eef1fb; padding: 3pt 7pt; border-left: 4px solid #5a72c9; margin: 3pt 0; }
.next { background: #fff3da; padding: 3pt 7pt; border-left: 4px solid #d99a2b; margin: 3pt 0; font-weight: bold; }
.warn { background: #fdeaea; padding: 3pt 7pt; border-left: 4px solid #c44; margin: 3pt 0; }
ol, ul { margin: 2pt 0 3pt 16pt; padding: 0; } li { margin-bottom: 1.5pt; }
figure { margin: 4pt 0; } figure img { width: 60%; border: 1px solid #bbb; } figcaption { font-size: 8pt; color: #555; }
.flow { font-family: "Liberation Mono", monospace; font-size: 8.3pt; background: #f4f4f4; padding: 6pt; white-space: pre; border: 1px solid #ccc; }
.break { page-break-before: always; } code { font-family: "Liberation Mono", monospace; background: #f0f0f0; padding: 0 2pt; }
"""

ROUTE = """START
  |
  v
 1 Trust Settings        2 Unit Profile
  |
  v
 3 Trust Student  ->  4 Student Enrollment      (repeat for each girl)
  |
  v
 5 Employee (staff)   6 Stock Reconciliation (opening stock)
  |
  v                            THE MONTH (June first, then July, August, September)
 7 Purchase Invoice  ->  8 Material Consumption  ->  9 Cash Bank Voucher
  |                                                            |
  v                                                            v
 10 Boarding Attendance  ->  11 Food Expenditure Statement  -> 12 Receipts and Payments (report)
  |
  v                            AT YEAR END
 13 Result Sheet of Inmates  ->  14 Promote  ->  15 confirm next year's enrollments
  |
  v                            EVERY HALF-YEAR
 16 Report Pack  ->  Preview  ->  Download PDF  (the report for the Minority department)"""


def img(name, caption):
    p = SHOTS / name
    return f'<figure><img src="{p.as_uri()}"><figcaption>{escape(caption)}</figcaption></figure>' if p.exists() else ""


def table(rows, head=("Field", "Type this")):
    h = "".join(f"<th>{escape(x)}</th>" for x in head)
    r = "".join("<tr>" + "".join(f"<td>{c}</td>" for c in row) + "</tr>" for row in rows)
    return f"<table><tr>{h}</tr>{r}</table>"


def step(num, title, open_how, fill, actions, see, went, nxt, shot=None, extra=""):
    parts = [f'<div class="step"><div class="head">Step {num}. {escape(title)}</div><div class="body">']
    parts.append(f'<div class="lab">Open it</div><div>{open_how}</div>')
    if fill:
        parts.append('<div class="lab">Fill in</div>' + (fill if fill.startswith("<") else f"<div>{fill}</div>"))
    if actions:
        parts.append('<div class="lab">Then</div><ol>' + "".join(f"<li>{a}</li>" for a in actions) + "</ol>")
    if extra:
        parts.append(extra)
    parts.append(f'<div class="see"><b>You should see:</b> {see}</div>')
    parts.append(f'<div class="went"><b>Where the data went:</b> {went}</div>')
    if shot:
        parts.append(img(*shot))
    parts.append(f'<div class="next">NEXT: {nxt}</div></div></div>')
    return "".join(parts)


def build():
    out = []
    out.append('<h1>Zohra Trust ERPNext: do it yourself</h1><div class="sub">Do the whole flow once, by hand, in an empty hostel. Every step says how to open the document, what to type, what you should see, where the data went, and which document to open next.</div>')
    out.append("<h2>Before you start</h2>")
    out.append(
        "<ol><li>Open <b>http://localhost:8000</b> and log in as the Administrator. (Roles for other users come later.)</li>"
        "<li>You will work in the hostel <b>Practice Hostel</b> (abbreviation PRH). It is empty: no girls, no stock, only opening cash Rs 50,000 and bank Rs 2,00,000. Whenever a form has a <b>Company</b> field, choose <b>Practice Hostel</b>. ERPNext may fill in another company first: change it.</li>"
        "<li>Dates are written <b>dd-mm-yyyy</b> on screen. Academic year is <b>2026-27</b>.</li></ol>"
    )
    out.append("<h3>How to open any document (three ways)</h3>")
    out.append(
        table(
            [
                ["Search bar", "Click the search bar at the top (or press <b>Ctrl+G</b>), type the document's name, for example <code>Trust Student</code>, and choose it. You see its list. Click the black <b>Add ...</b> button at the top right to make a new one."],
                ["Address bar", "Type <code>localhost:8000/app/trust-student/new</code>: the name with dashes instead of spaces, then <code>/new</code>."],
                ["From another document", "Some documents have a link field (for example the Student on an enrollment): click the small arrow in the field to open the linked record."],
            ],
            ("Way", "How"),
        )
    )
    out.append("<h3>Buttons and habits</h3><ul><li><b>Save</b> (Ctrl+S) keeps a draft. Documents with a coloured <b>Draft</b> label can still be changed.</li><li><b>Submit</b> (top right, then <b>Yes</b>) makes it final and does the automatic work (stock, accounts). A submitted document shows <b>Submitted</b> and has a <b>Cancel</b> button.</li><li>A date field: click it and type the date, then press Escape or click elsewhere. A link field (like Company): type a few letters, then click the matching line in the list.</li><li>If something is refused, read the message: it names the field.</li></ul>")
    out.append("<h2>The route: from which document to which</h2>")
    out.append(f'<div class="flow">{escape(ROUTE)}</div>')
    out.append("<p>Rule of the whole system: you enter each thing <b>once</b>. The later documents (Boarding Attendance, Food Statement, Receipts and Payments, Result Sheet, Report Pack) are <b>filled by buttons</b> from what you entered before. If a later document looks empty, an earlier step is missing.</p>")

    out.append('<h2 class="break">The data to type (keep this page open)</h2>')
    out.append("<h3>The four girls</h3>")
    out.append(
        table(
            [
                ["1", "Ayesha Begum", "Class 8", "Zohra English Medium", "Abdul Karim (Father)"],
                ["2", "Fouzia Sultana", "Class 9", "Zohra English Medium", "none"],
                ["3", "Gousia Bano", "Class 10", "Zohra Kannada Medium", "Gouse Pasha (Father)"],
                ["4", "Hajira Khatoon", "Class 10", "Zohra Kannada Medium", "none"],
            ],
            ("Register no.", "Name", "Class", "School", "Guardian"),
        )
        + "<p>Admission date and enrollment date for all four: <b>01-04-2026</b>.</p>"
    )
    out.append("<h3>The staff</h3>" + table([["Najmunnisa", "House Mother", "B.A"], ["Shakeela", "Cook", "10th"]], ("First name", "Designation", "Qualification")) + "<p>Both: gender Female, date of birth 01-01-1990, date of joining 01-01-2020, company Practice Hostel.</p>")
    out.append("<h3>Opening stock (count of 31 May 2026)</h3>" + table([["Rice", "50", "50"], ["Sugar", "10", "55"]], ("Item", "Quantity", "Valuation rate")))
    out.append("<h3>Each month</h3>")
    months = [
        ["June", "10-06", "Rice 100 x 50 = 5,000<br>Sugar 10 x 55 = 550<br>Vegetables 1 x 1,500", "15 and 16 June: Rice 40, Sugar 4", "9,000", "26 / 25", "120"],
        ["July", "03-07", "Rice 100 x 50 = 5,000<br>Sugar 10 x 60 = 600<br>Vegetables 1 x 2,000", "15 and 16 July: Rice 45, Sugar 5", "9,000", "26 / 25", "124"],
        ["August", "03-08", "same as July", "15 and 16 August: Rice 45, Sugar 5", "9,000", "26 / 25", "124"],
        ["September", "03-09", "same as July", "15 and 16 September: Rice 45, Sugar 5", "9,000", "26 / 25", "120"],
    ]
    out.append(table(months, ("Month", "Buy on", "Purchase Invoice lines", "Kitchen use (two days)", "Salaries (28th)", "School days Eng / Kan", "Hostel days (4 girls)")))
    out.append("<p>Every purchase is paid in cash. Salaries are a <b>Payment</b> on <b>Salaries</b> on the 28th of the month.</p>")
    out.append("<h3>Money, besides salaries</h3>" + table([["05-04-2026", "Receipt", "Cash", "Zohra trust", "20,000", "Loan from the Trust"], ["30-06-2026", "Receipt", "Cash", "Govt. grant received", "20,400", "4 girls x Rs 850 x 6 months"]], ("Date", "Type", "Mode", "Account head", "Amount", "Narration")))
    out.append("<h3>What each month's Food Statement must show (use it to check yourself)</h3>")
    out.append(table([["June (Is Opening)", "3,050", "16,050", "19,100", "14,940", "4,160"], ["July", "4,160", "16,600", "20,760", "16,100", "4,660"], ["August", "4,660", "16,600", "21,260", "16,100", "5,160"], ["September", "5,160", "16,600", "21,760", "16,100", "5,660"]], ("Month", "Opening balance", "Monthly purchase", "Total", "Monthly expenditure", "Remaining balance")))
    out.append("<h3>Marks, Final exam</h3>" + table([["Ayesha Begum (class 8, total 480)", "330", "Pass", "Promote (automatic)"], ["Fouzia Sultana (class 9, total 480)", "100", "Fail", "Repeat (automatic)"], ["Gousia Bano (class 10, total 625)", "440", "Pass", "Complete, destination Zohra Trust care"], ["Hajira Khatoon (class 10, total 625)", "150", "Fail", "change to Left with T.C."]], ("Girl", "Marks obtained", "Result", "Promotion action")))

    out.append('<h2 class="break">PART A. Set up once</h2>')
    out.append(step(1, "Trust Settings: the trust and its officer bearers", "Search bar: <code>Trust Settings</code>. (It is a single page: there is no list and no Add button.)", "Check the trust name and the officer bearers already there. You may add a bearer: click <b>Add Row</b> in the table and type name, designation, sort order, tick Is Active.", ["Click <b>Save</b>."], "the trust name and the four officer bearers, each ticked Is Active.", "the letterhead on every report page. The officer bearers print down the left of the letter, the receipts page and the staff list.", "Step 2: open the hostel's own profile."))
    out.append(step(2, "Trust Unit Profile: the hostel's address and typed texts", "Search bar: <code>Trust Unit Profile</code>, then click <b>Practice Hostel</b>.", table([["Address", "Near Masjid-e-Umar, Old Jewargi Road, Kalaburagi-585102"], ["Letter Text", "To, The District Minority Officer, Kalaburagi. Sub: Submission of accounts for the period {{ from_date }} to {{ to_date }}. Dear Sir, with reference to the above we submit the required papers for release of grant. Yours faithfully."], ["Appendix H Text", "1. Name of hostel: Zohra Minority Girls Hostel. 2. Sanctioned strength: 150 inmates."]]), ["Look at <b>Sanctions</b>: one row, from 01-04-2026, strength 150, rate Rs 850. Do not change it.", "Click <b>Save</b>."], "Tracks Residents, Food Statement and Results ticked; Ration Warehouse is Hostel Store - PRH; your texts saved.", "the report. The address prints on the letterhead and food statements; the Letter and Appendix H pages print your texts; the sanction (150, Rs 850) is what Boarding Attendance uses.", "Step 3: add the girls. Start with the student record.", ("01-unit-profile.jpg", "A Trust Unit Profile (another hostel's, for orientation).")))
    out.append(step(3, "Trust Student: the girl herself", "Search bar: <code>Trust Student</code>, click <b>Add Trust Student</b>.", table([["Student Name", "Ayesha Begum"], ["Home Unit", "Practice Hostel"], ["Admission Date", "01-04-2026"], ["Has Guardian", "tick it"], ["Guardians table", "Add Row: Guardian Name Abdul Karim, Relation Father"]]), ["Click <b>Save</b>. Note the number she gets (STU-000nn)."], "the name at the top with a green <b>Active</b> label.", "Trust Student is the permanent record of the girl. Her class and register number are NOT here; they go on the enrollment (next step) because they change every year.", "Step 4: enroll her for 2026-27. Repeat steps 3 and 4 for the other three girls.", ("02-student-form.jpg", "A new Trust Student with a guardian.")))
    out.append(step(4, "Student Enrollment: her class this year", "Search bar: <code>Student Enrollment</code>, click <b>Add Student Enrollment</b>.", table([["Student", "Ayesha Begum (choose from the list)"], ["Academic Year", "2026-27"], ["Unit", "Practice Hostel"], ["School", "Zohra English Medium"], ["Trust Class", "Class 8"], ["Register Sl No", "1"], ["Enrollment Date", "01-04-2026"], ["Status", "Enrolled"]]), ["Click <b>Save</b>.", "Go back to step 3 for Fouzia (register 2), Gousia (3) and Hajira (4) with the data page."], "the enrollment named ENR-2026-27-STU-000nn. After all four, the Student Enrollment list filtered by Practice Hostel shows 4 rows, Enrolled.", "'Enrolled' is what the monthly Boarding Attendance and the Result Sheet read to know who is in the hostel. The system also checks the number of girls never goes above the sanctioned strength (150).", "Step 5: the staff, then the opening stock.", ("04-enrollment-list.jpg", "The enrollment list.")))
    out.append(step(5, "Employee: the staff for the staff list", "Search bar: <code>Employee</code>, click <b>Add Employee</b>.", table([["First Name", "Najmunnisa"], ["Gender", "Female"], ["Date of Birth", "01-01-1990"], ["Date of Joining", "01-01-2020"], ["Company", "Practice Hostel"], ["Designation", "House Mother (create it if it is not in the list)"], ["Education table", "Add Row, Qualification B.A"]]), ["Click <b>Save</b>.", "Repeat for Shakeela: Cook, qualification 10th."], "Status Active.", "the 'List of staff' page of the report: name, qualification, designation.", "Step 6: tell the system what is in the store today."))
    out.append(step(6, "Stock Reconciliation: the opening stock", "Search bar: <code>Stock Reconciliation</code>, click <b>Add Stock Reconciliation</b>.", table([["Company", "Practice Hostel"], ["Purpose", "Opening Stock"], ["Edit Posting Date and Time", "tick it"], ["Posting Date", "31-05-2026"], ["Posting Time", "12:00:00"], ["Items table", "Add Row: Item Code Rice, Warehouse Hostel Store - PRH, Quantity 50, Valuation Rate 50"], ["", "Add Row: Sugar, Hostel Store - PRH, Quantity 10, Valuation Rate 55"]]), ["If it asks for a Difference Account choose <b>Temporary Opening - PRH</b>.", "Click <b>Save</b>, then <b>Submit</b> and <b>Yes</b>."], "Submitted. Difference Amount Rs 3,050 (2,500 + 550).", "the Stock Ledger: Rice 50 kg and Sugar 10 kg in the Hostel Store, with their rate. The first Food Statement reads this as its <b>old balance</b>. (Without a valuation rate the opening amount would be zero.)", "Step 7: the first purchase of June.", ("06-stock-submitted.jpg", "A submitted opening stock.")))
    out.append('<h2 class="break">PART B. The month: June first, then repeat for July, August and September</h2>')
    out.append(step(7, "Purchase Invoice: the shopping", "Search bar: <code>Purchase Invoice</code>, click <b>Add Purchase Invoice</b>.", table([["Supplier", "Cash purchase"], ["Company", "Practice Hostel"], ["Edit Posting Date and Time", "tick it"], ["Posting Date", "10-06-2026"], ["Update Stock", "tick it"], ["Set Accepted Warehouse", "Hostel Store - PRH"], ["Is Paid", "tick it"], ["Items table", "Add Row: Rice, quantity 100, rate 50"], ["", "Add Row: Sugar, quantity 10, rate 55"], ["", "Add Row: Vegetables, quantity 1, rate 1,500"], ["Payments tab", "Mode of Payment Cash; Cash/Bank Account Cash - PRH; Paid Amount equal to the total (7,050). If it shows 0, type 7050."]]), ["Click <b>Save</b>, check the Total, then <b>Submit</b> and <b>Yes</b>."], "Submitted, label Paid, total Rs 7,050.", "Two places. <b>Stock Ledger:</b> Rice +100 and Sugar +10 (Vegetables is not a stock item, so no quantity). <b>General Ledger:</b> expenses Food (Rice, Sugar) and Vegetables debited, Cash credited. Check it now: search <code>Stock Balance</code> report, company Practice Hostel: Rice 150, Sugar 20.", "Step 8: the kitchen uses some of it.", ("08-purchase-submitted.jpg", "A submitted cash purchase.")))
    out.append(step(8, "Material Consumption: what the kitchen used", "Search bar: <code>Material Consumption</code>, click <b>Add Material Consumption</b>.", table([["Company", "Practice Hostel"], ["Posting Date", "15-06-2026"], ["Items table", "Add Row: Rice, qty 40"], ["", "Add Row: Sugar, qty 4"]]), ["Click <b>Save</b>, <b>Submit</b>, <b>Yes</b>.", "Now make the next day's: Add Material Consumption, Company Practice Hostel, Posting Date <b>16-06-2026</b>, then click <b>Copy Yesterday</b>. The same items and quantities appear. <b>Save</b>, <b>Submit</b>, <b>Yes</b>."], "after the second one the items Rice 40 and Sugar 4 filled by the button, and a <b>Stock Entry</b> number at the bottom.", "a <b>Stock Entry</b> (Material Issue) made by the system, which takes the quantity out of the Stock Ledger: Rice 150 - 80 = 70, Sugar 20 - 8 = 12. No money moves. The Food Statement reads these as the month's <b>consumed</b> quantities.", "Step 9: record the money in and out.", ("09-consumption-copy-yesterday.jpg", "Copy Yesterday.")))
    out.append(step(9, "Cash Bank Voucher: receipts and payments", "Search bar: <code>Cash Bank Voucher</code>, click <b>Add Cash Bank Voucher</b>. Make three vouchers, one after the other:", table([["1. Voucher Type", "Receipt"], ["Posting Date / Mode", "05-04-2026 / Cash"], ["Account Head", "Zohra trust - PRH"], ["Amount", "20000"], ["Narration", "Loan from Zohra trust"], ["2. Receipt, 30-06-2026, Cash", "Account Head Govt. grant received - PRH, Amount 20400"], ["3. Payment, 30-06-2026, Cash", "Account Head Salaries - PRH, Amount 9000, narration June salaries"]]), ["For each: click <b>Save</b>, then <b>Submit</b> and <b>Yes</b>."], "each voucher Submitted, with a <b>Journal Entry</b> number at the bottom.", "a <b>Journal Entry</b> made by the system: a receipt debits Cash and credits the head; a payment does the opposite. Never edit that Journal Entry; if you made a mistake, cancel the voucher. The <b>Receipts and Payments</b> report and the Food Statement (for Salaries) read it.", "Step 10: at the end of June, record how many days the girls stayed.", ("12-receipt-submitted.jpg", "A submitted receipt.")))
    out.append(step(10, "Boarding Attendance: hostel and school days", "Search bar: <code>Boarding Attendance</code>, click <b>Add Boarding Attendance</b>.", table([["Company", "Practice Hostel"], ["Month", "June"], ["School Days table", "Add Row: School Zohra English Medium, Days school ran 26"], ["", "Add Row: Zohra Kannada Medium, 25"]]), ["Click the <b>Fill Girls</b> button at the top.", "Look at the four rows. Do not change them (nobody was absent). <b>Save</b>, <b>Submit</b>, <b>Yes</b>."], "4 students on roll, hostel attendance 120, school attendance 102, Total Grant Rs 3,400 (4 x 850). Sanction strength 150 and rate Rs 850 are filled in by themselves.", "this is the only place that holds each girl's days. The abstract page and the Kannada registers of the report are built from it. The grant shown is for the month; the department pays six months at once (voucher in step 9).", "Step 11: build the month's food sheet.", ("13-attendance-rows.jpg", "Fill Girls: one row per enrolled girl.")))
    out.append(step(11, "Food Expenditure Statement: the monthly sheet", "Search bar: <code>Food Expenditure Statement</code>, click <b>Add Food Expenditure Statement</b>.", table([["Company", "Practice Hostel"], ["Month", "June"], ["Is Opening", "tick it (only for the very first statement)"]]), ["Click <b>Fill</b>. Never type in the old balance columns: they are read-only.", "Scroll down and read the Rice and Sugar rows and the totals. <b>Save</b>, then <b>Submit</b> and <b>Yes</b>."], "Opening balance 3,050; Monthly purchase 16,050; Total 19,100; Monthly expenditure 14,940; Remaining balance 4,160. Rice: old 50, purchased 100, used 80, left 70 = Rs 3,500.", "it reads FOUR places: <b>Stock Ledger</b> (old balance quantity), <b>Purchase Invoices</b> (purchased), <b>Material Consumption</b> (used), <b>General Ledger</b> (Vegetables 1,500 and Salaries 9,000 appear as amount-only rows). Next month's old rate is this month's closing rate.", "June is done. Repeat steps 7 to 11 for July, August and September using the monthly table (a Purchase Invoice, two Material Consumptions, a Salaries voucher, Boarding Attendance, a Food Statement WITHOUT Is Opening). Check each statement against the 'must show' table. Then step 12.", ("15-food-lines.jpg", "Fill: the lines.")))
    out.append('<h2 class="break">PART C. Check the money</h2>')
    out.append(step(12, "Receipts and Payments Account (report)", "Search bar: <code>Receipts and Payments Account</code>. Choose Company Practice Hostel, From Date 01-04-2026, To Date 30-09-2026.", "", [], "Receipts: Opening balance Cash 50,000, Bank 2,00,000; Loan from Zohra trust 20,000; Govt. grant received 20,400. Payments: Food 29,850; Salaries 36,000; Closing balance Cash 24,550, Bank 2,00,000. Both totals <b>2,90,400</b>.", "nothing new is stored: the report reads the General Ledger (everything the vouchers and purchase invoices posted). If your two totals differ, an entry is missing or has a wrong date: compare with the data pages.", "Part D: the year end. Open the Result Sheet.", ("18-receipts-payments.jpg", "The report (another hostel's figures).")))
    out.append('<h2 class="break">PART D. Year end: results and promotion</h2>')
    out.append(step(13, "Result Sheet of Inmates", "Search bar: <code>Result Sheet of Inmates</code>, click <b>Add</b>.", table([["Company", "Practice Hostel"], ["Academic Year", "2026-27"], ["Exam", "Final"], ["Exam Date", "12-03-2027"]]), ["Click <b>Fill Students</b>. Four rows appear with the maximum marks of each class (480, 480, 625, 625).", "In each row (open it with the pencil icon or click the cells) type <b>Marks Obtained</b> and choose <b>Result</b> from the data page. The <b>Promotion Action</b> fills itself.", "For Gousia (class 10, Pass): choose a <b>Leaving Destination</b>, Zohra Trust care. For Hajira (Fail): change the action from Repeat to <b>Left with T.C.</b>.", "<b>Save</b>, then <b>Submit</b> and <b>Yes</b>."], "Appeared 4, Passed 2, Failed 2. Actions: Promote, Repeat, Complete, Left with T.C.", "the result of each girl and what should happen to her next. Nothing has changed in the enrollments yet.", "Step 14: press Promote.", ("19-result-fill.jpg", "Fill Students.")))
    out.append(step(14, "Promote: make next year's enrollments", "On the submitted Result Sheet, click the <b>Promote</b> button at the top, then <b>Yes</b>.", "", [], "the Promote button disappears and <b>Promotion Done</b> is ticked.", "<b>Student Enrollment</b> for 2027-28 (status <b>Planned</b>): Ayesha in class 9, and Fouzia again in class 9 with <b>Is Repeating</b> ticked. <b>Trust Student</b>: Gousia becomes <b>Passed Out</b>, Hajira becomes <b>Left</b> with reason Left with T.C. Last year's enrollments are never edited. Open Student Enrollment, filter Academic Year 2027-28 and Trust Student to see it.", "Step 15: confirm next year, and fill Hajira's T.C. number.", ("22-next-year.jpg", "Next year's enrollments, status Planned.")))
    out.append(step(15, "Confirm next year, and the T.C. number", "Search bar: <code>Student Enrollment</code>, filter Academic Year 2027-28.", "", ["Open each Planned enrollment, change <b>Status</b> to <b>Enrolled</b>, Save. (This is the person confirming the girl is back, at the start of the year.)", "Open <b>Trust Student</b>, Hajira Khatoon. Fill <b>T.C. number</b> (TC/2027/01) and <b>T.C. date</b>. Save. (These show only when the status is Left.)"], "the girls Enrolled in 2027-28, Hajira with her T.C. details.", "the new year's roll. Next April's Boarding Attendance Fill Girls will list exactly these girls.", "Part E: the report for the department.", ("23-student-status.jpg", "Student status after promotion.")))
    out.append('<h2 class="break">PART E. Every half-year: the Report Pack</h2>')
    out.append(step(16, "Report Pack: preview and download", "Search bar: <code>Report Pack</code>, click <b>Add Report Pack</b>.", table([["Company", "Practice Hostel"], ["From Date", "01-04-2026"], ["To Date", "30-09-2026"]]), ["Click <b>Save</b>. Nine pages are listed.", "Click <b>Preview</b>. Wait up to 20 seconds. The window shows the page list and the PDF. An orange box lists anything to fix.", "Fix what it says (for example a month not submitted), close the window, Preview again.", "When the box is gone, click <b>Download PDF</b> and open it.", "Optional: Add Row, choose <b>Uploaded page</b>, a title (CA balance sheet) and attach a PDF, then Save and Preview again: it is added to the pack."], "19 pages: letter, receipts and payments, abstract, four food statements, Appendix - H, officer bearers, staff, result sheet and eight attendance registers.", "nothing is stored except the page list: the PDF is built from all the records at the moment you click.", "Done. The whole flow, once.", ("24-pack-pages.jpg", "The Report Pack."), extra=""))
    out.append('<h2 class="break">If you get stuck</h2>')
    out.append(
        table(
            [
                ["Fill Girls / Fill Students shows no rows", "No enrollments with status Enrolled for that company and year. Do steps 3 and 4."],
                ["The Food Statement shows zero old balance", "No opening stock (step 6), or the Stock Reconciliation has no valuation rate."],
                ["Fill on the Food Statement shows no purchases", "The Purchase Invoice is a draft, is for another company, or has a date outside the month."],
                ["The report says 'No submitted ... for July'", "That month's Boarding Attendance or Food Statement is still a draft or missing."],
                ["Material Consumption: 'already exists'", "Only one per hostel per day. Open the existing one."],
                ["I made a mistake in a submitted document", "Click <b>Cancel</b> on it (then <b>Amend</b>). Cancelling a Material Consumption puts the food back in stock; cancelling a Cash Bank Voucher removes its Journal Entry."],
            ],
            ("What you see", "What it means"),
        )
    )
    html = f"<html><head><meta charset='utf-8'><style>{CSS}</style></head><body>{''.join(out)}</body></html>"
    HTML(string=html, base_url=str(HERE)).write_pdf(OUT)
    print("wrote", OUT)


if __name__ == "__main__":
    build()
