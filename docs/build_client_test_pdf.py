"""Build Zohra_Client_Test_Guide.pdf: what the client does on the test site, and the figures to compare with.

    /home/ameer/Desktop/frappe-bench/env/bin/python apps/zohra_trust/docs/build_client_test_pdf.py

The figures come from zohra_trust.setup.filed_figures and zohra_trust.setup.client_test_data and are proved by
tests/test_client_test_data.py. Run from the bench folder with the app importable (the bench python).
"""

from html import escape
from pathlib import Path

from weasyprint import HTML

from zohra_trust.setup import client_test_data as data
from zohra_trust.setup.filed_figures import FILED_TOTALS, MONTH_NAMES

OUT = Path(__file__).parent / "Zohra_Client_Test_Guide.pdf"
CSS = """
@page { size: A4; margin: 15mm 13mm; @bottom-center { content: "Zohra Minority Girls Hostel: test guide  -  page " counter(page); font-size: 8pt; color: #777; } }
body { font-family: "Liberation Sans", Arial, sans-serif; font-size: 9.8pt; color: #222; line-height: 1.4; }
h1 { font-size: 21pt; margin: 0 0 4pt; color: #1b4d3e; } h2 { font-size: 13.5pt; color: #1b4d3e; border-bottom: 2px solid #1b4d3e; padding-bottom: 2pt; margin: 14pt 0 6pt; page-break-after: avoid; }
.sub { color: #555; font-size: 11pt; margin-bottom: 10pt; } table { border-collapse: collapse; width: 100%; margin: 4pt 0 8pt; font-size: 8.8pt; }
th, td { border: 1px solid #999; padding: 2.5pt 4pt; text-align: left; vertical-align: top; } th { background: #e6e6e6; } tr { page-break-inside: avoid; }
td.n, th.n { text-align: right; } .box { border: 1.5px solid #1b4d3e; border-radius: 4pt; padding: 4pt 8pt; margin: 6pt 0; page-break-inside: avoid; }
.see { background: #eef5f2; padding: 3pt 7pt; border-left: 4px solid #1b4d3e; margin: 4pt 0; } .warn { background: #fff3da; padding: 3pt 7pt; border-left: 4px solid #d99a2b; margin: 4pt 0; }
ol, ul { margin: 2pt 0 3pt 16pt; padding: 0; } li { margin-bottom: 1.5pt; } .break { page-break-before: always; }
"""


def inr(value):
	text = f"{abs(value):.2f}"
	whole, paise = text.split(".")
	if len(whole) > 3:
		head, tail, groups = whole[:-3], whole[-3:], []
		while len(head) > 2:
			groups.insert(0, head[-2:])
			head = head[:-2]
		whole = ",".join(([head] if head else []) + groups + [tail])
	return whole if paise == "00" else f"{whole}.{paise}"


def table(head, rows, numeric=()):
	h = "".join(f'<th class="{"n" if i in numeric else ""}">{escape(c)}</th>' for i, c in enumerate(head))
	body = "".join("<tr>" + "".join(f'<td class="{"n" if i in numeric else ""}">{c}</td>' for i, c in enumerate(r)) + "</tr>" for r in rows)
	return f"<table><tr>{h}</tr>{body}</table>"


def build():
	girls = data.girls()
	actions = {"Promote": 0, "Repeat": 0, "Complete": 0}
	for _n, _name, klass, _school, _total, _marks, result in girls:
		actions["Repeat" if result == "Fail" else ("Complete" if klass == 10 else "Promote")] += 1
	passed = sum(1 for g in girls if g[6] == "Pass")
	out = ['<h1>Zohra Minority Girls Hostel: test guide</h1><div class="sub">Do the month-end work by hand on the test site and compare each screen with the figures in this guide.</div>']
	out.append("<h2>What is already in the system</h2>")
	out.append(
		"<ul><li>The trust, its officer bearers, the hostel address, the letter text and the Appendix – H text, and the four staff.</li>"
		"<li><b>50 girls</b> (fictional names), in classes 3 to 10, with register numbers 1 to 50. Girls 1 to 30 are in Zohra English Medium and 31 to 50 in Zohra Kannada Medium.</li>"
		"<li>The opening cash (Rs 682) and bank (Rs 6,34,446.84) of 1 April 2026, and the opening stock of 31 May 2026.</li>"
		"<li>Every purchase, every day of kitchen use, the salaries, the trust's loan, the bank interest and the transfer to the trust for <b>June to September 2026</b>.</li></ul>"
		"<div class='warn'>What is <b>not</b> entered is what you do now: the four Boarding Attendances, the four Food Expenditure Statements, the Result Sheet, Promote and the Report Pack. Log in with the user you were given. Open any document with the search bar (Ctrl+G).</div>"
	)
	out.append("<h2>Step 1. Boarding Attendance, once for each month</h2>")
	out.append("<ol><li>Open <b>Boarding Attendance</b> and click <b>Add</b>.</li><li>Company: Zohra Minority Girls Hostel. Month: the month. Year is filled in.</li><li>School Days table, Add Row twice: Zohra English Medium and Zohra Kannada Medium, <b>25</b> days each.</li><li>Click <b>Fill Girls</b>. Do not change the rows. Click <b>Save</b>, then <b>Submit</b> and <b>Yes</b>.</li></ol>")
	rows = [[MONTH_NAMES[m], "50", inr(50 * d), inr(50 * 25), inr(50 * 850)] for m, d in ((6, 30), (7, 31), (8, 31), (9, 30))]
	out.append(table(("Month", "Students on roll", "Hostel attendance", "School attendance", "Total grant"), rows, (1, 2, 3, 4)))
	out.append("<h2>Step 2. Food Expenditure Statement, once for each month, in order</h2>")
	out.append("<ol><li>Open <b>Food Expenditure Statement</b>, <b>Add</b>. Company and Month. Tick <b>Is Opening</b> for June only.</li><li>Click <b>Fill</b>. Never type in the old balance columns: they come from the real stock.</li><li><b>Save</b>, then <b>Submit</b> and <b>Yes</b>. Do June, then July, August, September.</li></ol>")
	rows = [[MONTH_NAMES[m]] + [inr(v) for v in (*FILED_TOTALS[m][:4], FILED_TOTALS[m][2] - FILED_TOTALS[m][3])] for m in (6, 7, 8, 9)]  # the closing is exact, not the rounded paper figure
	out.append(table(("Month", "Opening balance", "Monthly purchase", "Total", "Monthly expenditure", "Remaining balance"), rows, (1, 2, 3, 4, 5)))
	out.append("<div class='see'>These are the totals printed on the hostel's own filed statements. September closes at 83,039.50 where the paper shows 83,040: the paper is rounded.</div>")
	out.append("<h2>Step 3. Receipts and Payments Account</h2>")
	out.append("<p>Open the report <b>Receipts and Payments Account</b>. Company: Zohra Minority Girls Hostel. From 01-04-2026, to 30-09-2026.</p>")
	out.append(table(("Receipts", "Rs", "Payments", "Rs"), [["Opening balance, cash", "682", "Food", "5,79,598"], ["Opening balance, bank", "6,34,446.84", "Fuel", "37,780"], ["Loan from Zohra trust", "12,30,000", "Detergent", "47,400"], ["Bank interest", "4,779", "Salaries", "48,000"], ["", "", "Transfer to Zohra trust", "7,00,000"], ["", "", "Closing balance, cash", "17,904"], ["", "", "Closing balance, bank", "4,39,225.84"], ["<b>Total</b>", "<b>18,69,907.84</b>", "<b>Total</b>", "<b>18,69,907.84</b>"]], (1, 3)))
	out.append("<div class='warn'>The hostel's filed receipts page shows Food 5,63,825 and closing cash 33,677. The filed food statements add up to 5,79,598, which is what the system shows. This difference of Rs 15,773 is in the filed paper itself and is to be explained by the hostel.</div>")
	out.append('<h2 class="break">Step 4. Result Sheet of Inmates</h2>')
	out.append("<ol><li>Open <b>Result Sheet of Inmates</b>, <b>Add</b>. Company; Academic Year 2026-27; Exam Final; Exam Date 12-03-2027.</li><li>Click <b>Fill Students</b>: 50 rows appear with each girl's total marks.</li><li>Type the <b>Marks Obtained</b> and the <b>Result</b> of each girl from the table below. The Promotion Action fills in when you Save.</li><li>For the girls in class 10 who passed, choose a <b>Leaving Destination</b> (Zohra Trust care). <b>Save</b>, <b>Submit</b>.</li></ol>")
	out.append(f"<div class='see'>Expected: Appeared 50, Passed {passed}, Failed {50 - passed}. Promotion actions: Promote {actions['Promote']}, Repeat {actions['Repeat']}, Complete {actions['Complete']}.</div>")
	out.append(table(("No.", "Name", "Class", "Total marks", "Marks obtained", "Result"), [[n, escape(name), k, t, m, r] for n, name, k, _s, t, m, r in girls], (0, 2, 3, 4)))
	out.append("<h2>Step 5. Promote</h2>")
	out.append(f"<p>On the submitted Result Sheet click <b>Promote</b> and <b>Yes</b>. Next year's enrollments (2027-28, status Planned) appear for the {actions['Promote'] + actions['Repeat']} girls who continue; girls who passed class 10 become Passed Out. To try <b>Left with T.C.</b>, change a failed girl's Promotion Action to it before you Submit.</p>")
	out.append("<h2>Step 6. Report Pack</h2>")
	out.append("<ol><li>Open <b>Report Pack</b>, <b>Add</b>. Company; From Date 01-04-2026; To Date 30-09-2026; Letter date 05-10-2026; Place Kalaburagi. <b>Save</b>.</li><li>Click <b>Preview</b>. Wait up to 20 seconds.</li><li>Click <b>Download PDF</b> and compare it with the hostel's filed report.</li></ol>")
	out.append("<div class='see'>Expected: 15 items listed (letter, receipts and payments, abstract, four food statements, Appendix – H, officer list, staff list, result sheet, four attendance registers) and <b>no</b> \"To fix before filing\" box. If the box lists a month, that month's attendance or statement is missing.</div>")
	out.append("<h2>If something goes wrong</h2>")
	out.append(table(("What you see", "What to do"), [["A message when you Submit", "Read it: it names the field. Nothing is saved when a document is refused."], ["Fill Girls shows no rows", "No girl is Enrolled for that hostel and year."], ["A mistake in a submitted document", "Click Cancel on it, then Amend, correct it and Submit again."], ["The report box says a month is missing", "Do that month's Boarding Attendance and Food Expenditure Statement."], ["A statement does not match the table", "Tell us the month and the line. Do not type in the old balance columns."]]))
	HTML(string=f"<html><head><meta charset='utf-8'><style>{CSS}</style></head><body>{''.join(out)}</body></html>").write_pdf(OUT)
	print("wrote", OUT)


if __name__ == "__main__":
	build()
