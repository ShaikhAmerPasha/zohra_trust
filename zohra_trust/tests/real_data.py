"""Clear the demo hostels, then load the real hostel for a client demonstration.

    bench --site <site> execute zohra_trust.tests.real_data.clear_demo
    bench --site <site> execute zohra_trust.tests.real_data.load_masters
    bench --site <site> execute zohra_trust.tests.real_data.load_entries

The month-end documents (Boarding Attendance, Food Expenditure Statement, Result Sheet, Report Pack) are made
on screen, so the client sees the Fill buttons work. Figures are the filed June to September 2026 figures
(tests/e2e_filed_half_year.py); the girls are the first 50 names of the filed result sheet.
"""

import frappe

from zohra_trust.setup.create_unit import create_unit
from zohra_trust.tests.e2e_filed_half_year import JUNE_OLD, MONTHS, MONTH_NAMES
from zohra_trust.tests.helpers import SCHOOLS, make_masters

COMPANY, ABBR = "Zohra Minority Girls Hostel", "ZMH"
DEMO_COMPANIES = ("Demo Hostel", "Demo Hostel Two", "Practice Hostel", "Test Run Hostel", "Flow Demo Hostel")
STORE = f"Hostel Store - {ABBR}"

# (name, class, total marks, marks obtained), the first 50 rows of the filed result sheet, all Pass
GIRLS = [
	("Maheboob Bee Khadeer", 8, 480, 300), ("Tabassum Basher", 7, 480, 300), ("Wajiha Moinuddin", 10, 625, 350), ("Mubeena Ismail", 9, 480, 280),
	("Nilofer Mastan", 10, 625, 380), ("Chandni Maheboob", 10, 625, 400), ("Ruksana Maheboob", 10, 625, 350), ("Shahana Tayyab Ali", 10, 625, 400),
	("Khaja Bee Alauddin", 7, 480, 350), ("Safiya Nabi", 5, 250, 200), ("Masheeda Bee Chand Patel", 10, 625, 350), ("Muskan", 9, 480, 300),
	("Khaja Hussain", 9, 480, 250), ("Al Saba", 9, 480, 250), ("Saleha Shabbier Patel", 10, 625, 350), ("Muskan Chand Patel", 10, 625, 350),
	("Rehana Sher Ali", 9, 480, 250), ("Nasreen Abdul Razaq", 8, 480, 250), ("Sana Shafeeq", 9, 480, 300), ("Ruksana Gudu Sab", 8, 480, 300),
	("Sameera Asif", 9, 480, 300), ("Simran Nabi Rasool", 9, 480, 400), ("Sumayya Nazeer", 7, 480, 400), ("Madiha Nabi Rasool", 8, 480, 400),
	("Jasmeen Bandgi", 6, 480, 350), ("Arshiya Mashaq", 10, 625, 350), ("Karishma Rukmuddin", 9, 480, 350), ("Rabiya Nazeer Uddin", 9, 480, 350),
	("Gulnaz", 6, 480, 350), ("Tahera", 9, 480, 350), ("Seema Parveen Mahemood", 8, 480, 350), ("Heena Rukum Patel", 8, 480, 350),
	("Neha Nabi Patel", 5, 250, 220), ("Zubiya Qayyum", 5, 250, 200), ("Saniya Bawa Sab", 6, 480, 350), ("Hussain Bee Abdul Sab", 5, 250, 250),
	("Yasmeen Abbas Ali", 8, 480, 350), ("Zoya Banu Raja Sab", 6, 480, 300), ("Gousiya Moula Shaikh", 9, 480, 350), ("Suhana Ahmed", 10, 625, 350),
	("Humera Abdul Hameed", 10, 625, 350), ("Chand Bee Alauddin", 7, 480, 400), ("Mahek Anjum Moula", 8, 480, 400), ("Samreen Abdul Razaq", 9, 480, 350),
	("Madiha Dawood", 3, 250, 200), ("Tasleem Khaja Hussain", 9, 480, 350), ("Ayesha Siddiqua", 8, 480, 350), ("Baby Ayesha Shabbier Patel", 8, 480, 350),
	("Ishrat Banu Basha", 7, 480, 400), ("Shaheda Shamshuddin", 7, 480, 400),
]  # fmt: skip
STAFF = (("Najmunnisa", "House Mother", "B.A"), ("Shabnam", "House Mother", "PUC"), ("Shakeela", "Cook", "10th"), ("Asma", "Asst Cook", "PUC"))
ADDRESS = "Near Masjid-e-Umar Old Jewargi Road, Kalaburagi-585102"
LETTER = """<p>To,<br><b>The District Minority officer,<br>Kalaburagi</b></p>
<p style="margin-left:40px"><b>Sub:</b> Submission of accounts and necessary paper for the period {{ from_date }} to {{ to_date }} towards maintenance grant of Zohra minority girls' hostel.</p>
<p>Dear Sir,</p>
<p>With reference to the above we are here with submitting all the required papers for the release of grant towards maintenance of the Hostel.</p>
<p style="text-align:center"><b>Thanking you we remain</b></p>
<p style="text-align:right"><b>Yours faithfully</b></p>"""
APPENDIX_H = """<h2 style="text-align:center;text-decoration:underline">APPENDIX- H</h2>
<h3 style="text-align:center;text-decoration:underline">RULES 12 FORM OF APPLICATION FOR GRANT IN AID TO BE SUBMITTED TO THE CHIEF SECRETARY ZILLAH PANCHAYAT, GULBARGA</h3>
<table style="width:100%;border-collapse:collapse;font-size:16px" cellpadding="6">
<tr><td>1.</td><td>Name and Address of Institute/Hostel</td><td>:</td><td>ZOHRA MINORITY GIRLS HOSTEL<br>Old Jewargi Road, Opp. PWD Qrt. Gulbarga - 585 102.</td></tr>
<tr><td>2.</td><td>Name of Trust</td><td>:</td><td>Zohra Women &amp; Children Charitable Welfare Trust</td></tr>
<tr><td>3.</td><td>Name and Address of the Secretary</td><td>:</td><td>Mrs. Basheerunnissa Begum<br>Mahetab Ali Compound, Aiwan-e-Shahi Colony, Gulbarga - 585 102.</td></tr>
<tr><td>4.</td><td>a) No. and date of the order recognition by the backward classes Dept.</td><td>:</td><td>Not Applicable</td></tr>
<tr><td></td><td>b) Period of which the recognition</td><td>:</td><td>18/08/1997-98/12/04/99, 01/01/05</td></tr>
<tr><td>5.</td><td>a) Sanctioned strength at the time of recognition<br>b) Strength and attendance as on 31st March</td><td>:</td><td>150 inmates</td></tr>
<tr><td>6.</td><td>Approved expenditure for the Hostel and amount actually spent as per audit statement of A/c</td><td>:</td><td>Enclosed</td></tr>
<tr><td>7.</td><td>Amount of grant sanctioned during the previous year and during the year budget estimate for the current year should be enclosed</td><td>:</td><td>Enclosed</td></tr></table>
<p><b>Note:</b> This application for grant should be accompanied by the audit statement of account and all other relevant documents as the facilities the sanction of grant by the competent authority.</p>
<h3 style="text-align:center;text-decoration:underline">DECLARATION</h3>
<p>On behalf of the management the institution I/we hereby declare that the condition of the recognition and grant in prepared to submit all the account of the hostel. In inspection and to furnish the returns as may be required by the Dept. no money will be collected from the boarders of the Hostel towards their boarding &amp; lodging.</p>"""


def clear_company(company):
	"""Everything the demo and practice runs made for one company, and the company itself."""
	frappe.flags.in_test = True
	for dt in ("Report Pack", "Result Sheet of Inmates", "Food Expenditure Statement", "Boarding Attendance", "Material Consumption", "Cash Bank Voucher"):
		for name in frappe.get_all(dt, {"company": company}, pluck="name"):
			frappe.db.set_value(dt, name, "docstatus", 2)
			frappe.delete_doc(dt, name, force=1, ignore_permissions=True)
	for dt in ("Purchase Invoice", "Stock Entry", "Stock Reconciliation", "Journal Entry", "Payment Entry"):
		for name in frappe.get_all(dt, {"company": company}, pluck="name"):
			frappe.db.set_value(dt, name, "docstatus", 2)
			frappe.delete_doc(dt, name, force=1, ignore_permissions=True)
	abbr = frappe.db.get_value("Company", company, "abbr")
	frappe.db.delete("GL Entry", {"company": company})
	frappe.db.delete("Stock Ledger Entry", {"company": company})
	if abbr:
		frappe.db.delete("Bin", {"warehouse": ("like", f"%- {abbr}")})
	for name in frappe.get_all("Accounting Period", {"company": company}, pluck="name"):
		frappe.delete_doc("Accounting Period", name, force=1, ignore_permissions=True)
	for name in frappe.get_all("Student Enrollment", {"unit": company}, pluck="name"):
		frappe.delete_doc("Student Enrollment", name, force=1, ignore_permissions=True)
	for name in frappe.get_all("Trust Student", {"home_unit": company}, pluck="name"):
		frappe.delete_doc("Trust Student", name, force=1, ignore_permissions=True)
	for name in frappe.get_all("Employee", {"company": company}, pluck="name"):
		frappe.delete_doc("Employee", name, force=1, ignore_permissions=True)
	for name in frappe.get_all("Trust Unit Profile", {"company": company}, pluck="name"):
		frappe.delete_doc("Trust Unit Profile", name, force=1, ignore_permissions=True)
	frappe.db.delete("Item Default", {"company": company})
	frappe.db.delete("Mode of Payment Account", {"company": company})
	for name in frappe.get_all("Bank Account", {"company": company}, pluck="name"):
		frappe.delete_doc("Bank Account", name, force=1, ignore_permissions=True)
	if frappe.db.exists("Company", company):
		frappe.delete_doc("Company", company, force=1, ignore_permissions=True)


def clear_demo():
	from zohra_trust.tests.demo_data import USERS

	for company in DEMO_COMPANIES:
		if frappe.db.exists("Company", company):
			clear_company(company)
			print("cleared", company)
	for email in USERS.values():
		if frappe.db.exists("User", email):
			frappe.delete_doc("User", email, force=1, ignore_permissions=True)
	frappe.db.commit()
	print("companies left:", frappe.get_all("Company", pluck="name"))


def load_masters():
	"""The real hostel: unit, opening balances, texts, staff, 50 girls with their enrollments, opening stock."""
	frappe.flags.in_test = True
	if not frappe.db.exists("Fiscal Year", "2025-2026"):
		frappe.get_doc({"doctype": "Fiscal Year", "year": "2025-2026", "year_start_date": "2025-04-01", "year_end_date": "2026-03-31"}).insert()
	make_masters()
	create_unit(COMPANY, ABBR, sanctioned_strength=150, grant_rate=850, effective_from="2026-04-01")
	profile = frappe.get_doc("Trust Unit Profile", COMPANY)
	profile.address, profile.letter_text, profile.appendix_h_text = ADDRESS, LETTER, APPENDIX_H
	profile.save()
	opening = frappe.get_doc(
		{
			"doctype": "Journal Entry", "company": COMPANY, "posting_date": "2026-03-31", "user_remark": "Opening balances of 1 April 2026",
			"accounts": [
				{"account": f"Cash - {ABBR}", "debit_in_account_currency": 682},
				{"account": f"Bank - {ABBR}", "debit_in_account_currency": 634446.84},
				{"account": f"Temporary Opening - {ABBR}", "credit_in_account_currency": 635128.84},
			],
		}
	)
	opening.insert()
	opening.submit()
	for name, designation, qualification in STAFF:
		frappe.get_doc(
			{
				"doctype": "Employee", "first_name": name, "gender": "Female", "date_of_birth": "1985-01-01", "date_of_joining": "2020-01-01", "company": COMPANY,
				"status": "Active", "designation": frappe.get_doc({"doctype": "Designation", "designation_name": designation}).insert(ignore_if_duplicate=True).name,
				"education": [{"qualification": qualification}],
			}
		).insert()
	for n, (name, klass, _total, _marks) in enumerate(GIRLS, 1):
		student = frappe.get_doc({"doctype": "Trust Student", "student_name": name, "home_unit": COMPANY, "admission_date": "2026-04-01"}).insert()
		frappe.get_doc(
			{
				"doctype": "Student Enrollment", "student": student.name, "academic_year": "2026-27", "unit": COMPANY,
				"school": SCHOOLS[0] if n <= 30 else SCHOOLS[1], "trust_class": f"Class {klass}", "register_sl_no": n, "enrollment_date": "2026-04-01", "status": "Enrolled",
			}
		).insert()
	stock = frappe.get_doc(
		{
			"doctype": "Stock Reconciliation", "company": COMPANY, "purpose": "Opening Stock", "set_posting_time": 1, "posting_date": "2026-05-31", "posting_time": "12:00:00",
			"expense_account": f"Temporary Opening - {ABBR}",
			"items": [{"item_code": i, "warehouse": STORE, "qty": q, "valuation_rate": a / q} for i, (q, a) in JUNE_OLD.items()],
		}
	)
	stock.insert()
	stock.submit()
	frappe.db.commit()
	print("masters loaded:", frappe.db.count("Student Enrollment", {"unit": COMPANY}), "girls")


def load_entries():
	"""Purchases, kitchen use, salaries and the trust's money movements of June to September 2026."""
	frappe.flags.in_test = True
	from zohra_trust.api.material_consumption import copy_yesterday  # noqa: F401  (the same one-per-day rule applies)

	for month in (6, 7, 8, 9):
		purchases, consumed, heads = MONTHS[month]
		date = f"2026-{month:02d}-02"
		total = sum(a for _q, a in purchases.values())
		_purchase(date, [{"item_code": i, "qty": q, "rate": a / q, "warehouse": STORE} for i, (q, a) in purchases.items()], total, stock=True)
		nonstock = {h: a for h, a in heads.items() if h in ("Vegetables", "Mutton", "Fuel")}
		_purchase(f"2026-{month:02d}-03", [{"item_code": h, "qty": 1, "rate": a} for h, a in nonstock.items()], sum(nonstock.values()), stock=False)
		_voucher("Payment", "Salaries", heads["Salaries"], f"2026-{month:02d}-05", "Cash", f"{MONTH_NAMES[month]} salaries")
		first = {i: q // 2 for i, q in consumed.items()}
		_consume(f"2026-{month:02d}-15", first)
		_consume(f"2026-{month:02d}-28", {i: consumed[i] - first[i] for i in consumed})
	for kind, head, amount, date, mode in (
		("Receipt", "Zohra trust", 730000, "2026-04-05", "Cash"), ("Receipt", "Zohra trust", 500000, "2026-04-06", "Bank"),
		("Receipt", "Bank interest", 4779, "2026-09-30", "Bank"), ("Payment", "Zohra trust", 700000, "2026-08-20", "Bank"),
	):
		_voucher(kind, head, amount, date, mode, "")
	frappe.db.commit()
	print("entries loaded")


def _purchase(date, items, total, stock):
	doc = frappe.get_doc(
		{
			"doctype": "Purchase Invoice", "company": COMPANY, "supplier": "Cash purchase", "posting_date": date, "bill_date": date, "set_posting_time": 1,
			"update_stock": 1 if stock else 0, "set_warehouse": STORE if stock else None, "is_paid": 1, "mode_of_payment": "Cash",
			"cash_bank_account": f"Cash - {ABBR}", "paid_amount": total, "items": items,
		}
	)
	doc.insert()
	doc.submit()


def _voucher(kind, head, amount, date, mode, narration):
	doc = frappe.get_doc(
		{
			"doctype": "Cash Bank Voucher", "company": COMPANY, "voucher_type": kind, "posting_date": date, "mode": mode,
			"bank_account": f"{COMPANY} - Hostel Bank" if mode == "Bank" else None, "account_head": f"{head} - {ABBR}", "amount": amount, "narration": narration,
		}
	)
	doc.insert()
	doc.submit()


def _consume(date, quantities):
	doc = frappe.get_doc({"doctype": "Material Consumption", "company": COMPANY, "posting_date": date, "items": [{"item_code": i, "qty": q} for i, q in quantities.items() if q]})
	doc.insert()
	doc.submit()
