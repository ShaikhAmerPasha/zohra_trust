"""Load the filed June to September 2026 half-year through the desk's own entry points and compare.

Run: bench --site <site> execute zohra_trust.tests.e2e_filed_half_year.run

Records are saved and submitted with frappe.desk.form.save.savedocs (what the form's Save and Submit
call) and the Fill buttons are run with frappe.handler.run_doc_method, as real Principal, Data Entry
and Store users. Everything is rolled back at the end. The 100 girls are synthetic: the filed report
gives their number (100) and the hostel attendance, not a roster that matches the result sheet.
"""

import json

import frappe

from zohra_trust.setup.create_unit import create_unit
from zohra_trust.tests.helpers import SCHOOLS, make_masters
from zohra_trust.trust_operations.report.receipts_and_payments_account.receipts_and_payments_account import execute as rp_report

COMPANY, ABBR = "Zohra Minority Girls Hostel", "ZMH"
USERS = {"Principal": "e2e.principal@example.com", "Data Entry": "e2e.entry@example.com", "Store": "e2e.store@example.com"}
STORE = f"Hostel Store - {ABBR}"
LINES = []

# item: (old_qty, old_amount) of the paper June opening
JUNE_OLD = {"Rice": (50, 2450), "Jawar": (35, 1050), "S. Oil": (3, 450), "Daal": (3, 240), "Sugar": (6, 330), "Salt": (1, 20),
	"Condiments": (11, 2200), "Onion": (20, 400), "C. Oil": (2, 400)}  # fmt: skip
ITEMS = ["Rice", "Jawar", "S. Oil", "Daal", "Sugar", "Tamarind", "Salt", "G. Nut", "Chilli", "Condiments", "Onion", "C. Oil", "T. Soap", "W. Soap"]

# month: (purchases {item: (qty, amount)}, consumed {item: qty}, heads {account: amount}) as printed on the filed statements
MONTHS = {
	6: ({"Rice": (1200, 58800), "Jawar": (600, 18000), "S. Oil": (30, 4500), "Daal": (30, 2400), "Sugar": (30, 1650), "Tamarind": (30, 2250),
		"Salt": (30, 600), "G. Nut": (30, 3600), "Chilli": (30, 4500), "Condiments": (20, 4000), "Onion": (50, 1000), "C. Oil": (40, 8000),
		"T. Soap": (300, 4800), "W. Soap": (300, 4200)},
		{"Rice": 1050, "Jawar": 450, "S. Oil": 30, "Daal": 30, "Sugar": 32, "Tamarind": 28, "Salt": 30, "G. Nut": 30, "Chilli": 30,
		"Condiments": 15, "Onion": 60, "C. Oil": 24, "T. Soap": 300, "W. Soap": 300},
		{"Vegetables": 15370, "Mutton": 22700, "Fuel": 11780, "Salaries": 11000}),
	7: ({"Rice": (1000, 49000), "Jawar": (300, 9000), "S. Oil": (30, 4500), "Daal": (30, 2400), "Sugar": (30, 1650), "Tamarind": (30, 2250),
		"Salt": (30, 600), "G. Nut": (40, 4800), "Chilli": (40, 6000), "Condiments": (10, 2000), "Onion": (60, 1200), "C. Oil": (10, 2000),
		"T. Soap": (300, 4800), "W. Soap": (300, 4200)},
		{"Rice": 1085, "Jawar": 465, "S. Oil": 30, "Daal": 30, "Sugar": 32, "Tamarind": 30, "Salt": 31, "G. Nut": 32, "Chilli": 32,
		"Condiments": 16, "Onion": 64, "C. Oil": 24, "T. Soap": 300, "W. Soap": 300},
		{"Vegetables": 8300, "Mutton": 16000, "Fuel": 8000, "Salaries": 11000}),
	8: ({"Rice": (1100, 53900), "Jawar": (800, 24000), "S. Oil": (30, 4500), "Daal": (30, 2400), "Sugar": (32, 1760), "Tamarind": (30, 2250),
		"Salt": (32, 640), "G. Nut": (30, 3600), "Chilli": (30, 4500), "Condiments": (20, 4000), "Onion": (60, 1200), "C. Oil": (24, 4800),
		"T. Soap": (300, 4800), "W. Soap": (300, 4200)},
		{"Rice": 1085, "Jawar": 465, "S. Oil": 32, "Daal": 32, "Sugar": 32, "Tamarind": 32, "Salt": 31, "G. Nut": 32, "Chilli": 32,
		"Condiments": 16, "Onion": 64, "C. Oil": 24, "T. Soap": 300, "W. Soap": 300},
		{"Vegetables": 11990, "Mutton": 20000, "Fuel": 10000, "Salaries": 13000}),
	9: ({"Rice": (1200, 58800), "Jawar": (600, 19998), "S. Oil": (70, 14000), "Daal": (70, 5600), "Sugar": (70, 4375), "Tamarind": (70, 5425),
		"Salt": (65, 1300), "G. Nut": (65, 7800), "Chilli": (65, 11375), "Condiments": (65, 13000), "Onion": (200, 4500), "C. Oil": (60, 12000),
		"T. Soap": (600, 10800), "W. Soap": (600, 9600)},
		{"Rice": 1050, "Jawar": 450, "S. Oil": 30, "Daal": 30, "Sugar": 32, "Tamarind": 30, "Salt": 30, "G. Nut": 30, "Chilli": 30,
		"Condiments": 15, "Onion": 60, "C. Oil": 24, "T. Soap": 600, "W. Soap": 600},
		{"Vegetables": 8815, "Mutton": 16000, "Fuel": 8000, "Salaries": 13000}),
}  # fmt: skip
# month: item: (expenditure, balance_qty, balance_amount) as printed
FILED = {
	6: {"Rice": (51450, 200, 9800), "Jawar": (13500, 185, 5550), "S. Oil": (4500, 3, 450), "Daal": (2400, 3, 240), "Sugar": (1760, 4, 220),
		"Tamarind": (2100, 2, 150), "Salt": (600, 1, 20), "G. Nut": (3600, 0, 0), "Chilli": (4500, 0, 0), "Condiments": (3000, 16, 3200),
		"Onion": (1200, 10, 200), "C. Oil": (4800, 18, 3600), "T. Soap": (4800, 0, 0), "W. Soap": (4200, 0, 0)},
	7: {"Rice": (53165, 115, 5635), "Jawar": (13950, 20, 600), "S. Oil": (4500, 3, 450), "Daal": (2400, 3, 240), "Sugar": (1760, 2, 110),
		"Tamarind": (2250, 2, 150), "Salt": (620, 0, 0), "G. Nut": (3840, 8, 960), "Chilli": (4800, 8, 1200), "Condiments": (3200, 10, 2000),
		"Onion": (1280, 6, 120), "C. Oil": (4800, 4, 800), "T. Soap": (4800, 0, 0), "W. Soap": (4200, 0, 0)},
	8: {"Rice": (53165, 130, 6370), "Jawar": (13950, 355, 10650), "S. Oil": (4800, 1, 150), "Daal": (2560, 1, 80), "Sugar": (1760, 2, 110),
		"Tamarind": (2400, 0, 0), "Salt": (620, 1, 20), "G. Nut": (3840, 6, 720), "Chilli": (4800, 6, 900), "Condiments": (3200, 14, 2800),
		"Onion": (1280, 2, 40), "C. Oil": (4800, 4, 800), "T. Soap": (4800, 0, 0), "W. Soap": (4200, 0, 0)},
	9: {"Rice": (51450, 280, 13720), "Jawar": (14998.5, 505, 15649.5), "S. Oil": (6000, 41, 8150), "Daal": (2400, 41, 3280), "Sugar": (2000, 40, 2485),
		"Tamarind": (2325, 40, 3100), "Salt": (600, 36, 720), "G. Nut": (3600, 41, 4920), "Chilli": (5250, 41, 7025), "Condiments": (3000, 64, 12800),
		"Onion": (1350, 142, 3190), "C. Oil": (4800, 40, 8000), "T. Soap": (10800, 0, 0), "W. Soap": (9600, 0, 0)},
}  # fmt: skip
# month: (opening, purchase, available, expenditure, closing) as printed
FILED_TOTALS = {6: (7540, 179150, 186690, 163260, 23430), 7: (23430, 137700, 161130, 148865, 12265),
	8: (12265, 171540, 183805, 161165, 22640), 9: (22640, 224388, 247028, 163988.5, 83040)}  # fmt: skip
FILED_HOSTEL_DAYS = {6: 3000, 7: 3100, 8: 3100, 9: 3000}
MONTH_NAMES = {6: "June", 7: "July", 8: "August", 9: "September"}
HEAD_ACCOUNT = {"Vegetables": "Vegetables", "Mutton": "Mutton", "Fuel": "Fuel"}


def note(ok, label, detail=""):
	LINES.append((ok, label, detail))
	print(("OK    " if ok else "DIFF  ") + label + (f"   {detail}" if detail else ""))


def compare(label, got, want, tolerance=0.005):
	note(abs(got - want) <= tolerance, label, f"system {got:,.2f} | filed {want:,.2f}")


def desk(user, action, doc, doctype=None):
	"""What the form's Save, Submit and Cancel buttons do."""
	from frappe.desk.form.save import savedocs

	if doctype:
		doc = {"doctype": doctype, **doc}
	doc.setdefault("__islocal", 1) if not doc.get("name") or str(doc["name"]).startswith("new-") else None
	if doc.get("__islocal") and not doc.get("name"):
		doc["name"] = "new-" + doc["doctype"].lower().replace(" ", "-") + "-1"
	frappe.set_user(USERS[user])
	frappe.local.response.docs = []
	try:
		savedocs(json.dumps(doc, default=str), action)
	finally:
		frappe.set_user("Administrator")
	return json.loads(json.dumps(frappe.local.response.docs[-1], default=str))


def button(user, doc, method):
	"""What a form button does: run a whitelisted controller method on the unsaved form."""
	from frappe.handler import run_doc_method

	frappe.set_user(USERS[user])
	frappe.local.response.docs = []
	try:
		run_doc_method(method, docs=json.dumps(doc, default=str))
	finally:
		frappe.set_user("Administrator")
	return json.loads(json.dumps(frappe.local.response.docs[-1].as_dict(), default=str))


def save_submit(user, doctype, doc):
	saved = desk(user, "Save", doc, doctype)
	return desk(user, "Submit", saved)


def setup():
	frappe.flags.in_test = True
	frappe.local.request = frappe._dict(method="POST")  # the desk posts these calls
	for role, email in USERS.items():
		frappe.get_doc({"doctype": "User", "email": email, "first_name": role, "send_welcome_email": 0, "roles": [{"role": role}]}).insert()
	if not frappe.db.exists("Fiscal Year", "2025-2026"):
		frappe.get_doc({"doctype": "Fiscal Year", "year": "2025-2026", "year_start_date": "2025-04-01", "year_end_date": "2026-03-31"}).insert()
	make_masters()
	create_unit(COMPANY, ABBR, sanctioned_strength=150, grant_rate=850, effective_from="2026-04-01")
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
	# the paper June opening stock
	entry = frappe.get_doc(
		{
			"doctype": "Stock Entry", "stock_entry_type": "Material Receipt", "company": COMPANY, "posting_date": "2026-05-31", "set_posting_time": 1,
			"to_warehouse": STORE,
			"items": [{"item_code": i, "qty": q, "basic_rate": a / q, "t_warehouse": STORE} for i, (q, a) in JUNE_OLD.items()],
		}
	)
	entry.insert()
	entry.submit()


def enter_students():
	for n in range(1, 101):
		student = desk("Principal", "Save", {"student_name": f"Student {n:03d}", "home_unit": COMPANY, "admission_date": "2026-04-01"}, "Trust Student")
		desk(
			"Principal", "Save",
			{
				"student": student["name"], "academic_year": "2026-27", "unit": COMPANY, "school": SCHOOLS[0] if n <= 60 else SCHOOLS[1],
				"trust_class": f"Class {8 + n % 3}", "register_sl_no": n, "enrollment_date": "2026-04-01", "status": "Enrolled",
			},
			"Student Enrollment",
		)
	note(frappe.db.count("Student Enrollment", {"unit": COMPANY, "status": "Enrolled"}) == 100, "100 students enrolled by the Principal")


def month_attendance(month):
	doc = {"company": COMPANY, "month": MONTH_NAMES[month], "year": 2026, "school_days": [{"school": SCHOOLS[0], "working_days": 25}, {"school": SCHOOLS[1], "working_days": 25}]}
	doc.update(__islocal=1, name="new-boarding-attendance-1", doctype="Boarding Attendance")
	filled = button("Data Entry", doc, "fill_rows")  # the Fill Girls button
	sheet = desk("Data Entry", "Save", filled)
	sheet = desk("Data Entry", "Submit", sheet)
	compare(f"{MONTH_NAMES[month]}: hostel attendance (abstract)", sheet["total_hostel_days"], FILED_HOSTEL_DAYS[month])
	return sheet


def month_purchases(month):
	purchases, consumed, heads = MONTHS[month]
	date = f"2026-{month:02d}-02"
	stock_items = [{"item_code": i, "qty": q, "rate": a / q, "warehouse": STORE} for i, (q, a) in purchases.items()]
	total = sum(a for _q, a in purchases.values())
	pi = {"company": COMPANY, "supplier": "Cash purchase", "posting_date": date, "bill_date": date, "set_posting_time": 1, "update_stock": 1,
		"set_warehouse": STORE, "is_paid": 1, "mode_of_payment": "Cash", "cash_bank_account": f"Cash - {ABBR}", "paid_amount": total, "items": stock_items}  # fmt: skip
	save_submit("Store", "Purchase Invoice", pi)
	nonstock = {h: a for h, a in heads.items() if h in HEAD_ACCOUNT}
	total2 = sum(nonstock.values())
	pi2 = {"company": COMPANY, "supplier": "Cash purchase", "posting_date": f"2026-{month:02d}-03", "bill_date": f"2026-{month:02d}-03", "set_posting_time": 1,
		"update_stock": 0, "is_paid": 1, "mode_of_payment": "Cash", "cash_bank_account": f"Cash - {ABBR}", "paid_amount": total2,
		"items": [{"item_code": h, "qty": 1, "rate": a} for h, a in nonstock.items()]}  # fmt: skip
	save_submit("Store", "Purchase Invoice", pi2)
	# salaries through a Cash Bank Voucher
	save_submit("Data Entry", "Cash Bank Voucher", {"company": COMPANY, "voucher_type": "Payment", "posting_date": f"2026-{month:02d}-05", "mode": "Cash",
		"account_head": f"Salaries - {ABBR}", "amount": heads["Salaries"], "narration": f"{MONTH_NAMES[month]} salaries"})  # fmt: skip


def month_consumption(month):
	_p, consumed, _h = MONTHS[month]
	first = {i: q // 2 for i, q in consumed.items()}
	day1 = {"company": COMPANY, "posting_date": f"2026-{month:02d}-15", "items": [{"item_code": i, "qty": q} for i, q in first.items() if q]}
	save_submit("Store", "Material Consumption", day1)
	# the second day opens with Copy Yesterday, then the cook corrects the quantities
	from zohra_trust.api.material_consumption import copy_yesterday

	frappe.set_user(USERS["Store"])
	copied = copy_yesterday(COMPANY, f"2026-{month:02d}-28")
	frappe.set_user("Administrator")
	note(len(copied) == len([q for q in first.values() if q]), f"{MONTH_NAMES[month]}: Copy Yesterday brought the earlier day's lines")
	day2 = {"company": COMPANY, "posting_date": f"2026-{month:02d}-28", "items": [{"item_code": r["item_code"], "qty": consumed[r["item_code"]] - first[r["item_code"]]} for r in copied]}
	save_submit("Store", "Material Consumption", day2)


def month_statement(month):
	doc = {"company": COMPANY, "month": MONTH_NAMES[month], "year": 2026, "is_opening": 1 if month == 6 else 0, "doctype": "Food Expenditure Statement",
		"__islocal": 1, "name": "new-food-expenditure-statement-1"}  # fmt: skip
	filled = button("Store", doc, "fill")  # the Fill button
	if month == 6:  # the first statement: the paper old balances are typed
		for line in filled["lines"]:
			if line.get("item_code") in JUNE_OLD:
				line["old_qty"], line["old_amount"] = JUNE_OLD[line["item_code"]]
		filled = button("Store", filled, "fill")  # filling again must keep what was typed
	saved = desk("Store", "Save", filled)
	statement = desk("Store", "Submit", saved)
	lines = {l.get("item_code"): l for l in statement["lines"] if l["line_type"] == "Item"}
	heads = {l["account"].split(" - ")[0]: l for l in statement["lines"] if l["line_type"] == "Expense Head"}
	name = MONTH_NAMES[month]
	for item in ITEMS:
		exp, bq, ba = FILED[month][item]
		l = lines[item]
		ok = abs(l["expenditure_amount"] - exp) < 0.005 and abs(l["balance_qty"] - bq) < 0.0005 and abs(l["balance_amount"] - ba) < 0.005
		note(ok, f"{name} {item}: expenditure, balance qty, balance amount", f"system {l['expenditure_amount']:g}/{l['balance_qty']:g}/{l['balance_amount']:g} | filed {exp:g}/{bq:g}/{ba:g}")
	for head, amount in MONTHS[month][2].items():
		compare(f"{name} {head} (amount-only row)", heads[head]["purchased_amount"], amount)
	opening, purchase, available, expenditure, closing = FILED_TOTALS[month]
	for label, got, want in (("opening", statement["total_opening"], opening), ("monthly purchase", statement["total_purchase"], purchase),
			("total", statement["total_available"], available), ("monthly expenditure", statement["total_expenditure"], expenditure),
			("remaining balance", statement["total_closing"], closing)):  # fmt: skip
		compare(f"{name} total {label}", got, want, tolerance=0.5 if (month == 9 and label == "remaining balance") else 0.005)


def receipts_and_payments():
	for voucher_type, head, amount, date, mode in (
		("Receipt", "Zohra trust", 730000, "2026-04-05", "Cash"), ("Receipt", "Zohra trust", 500000, "2026-04-06", "Bank"),
		("Receipt", "Bank interest", 4779, "2026-09-30", "Bank"), ("Payment", "Zohra trust", 700000, "2026-08-20", "Bank"),
	):
		save_submit("Data Entry", "Cash Bank Voucher", {"company": COMPANY, "voucher_type": voucher_type, "posting_date": date, "mode": mode,
			"bank_account": f"{COMPANY} - Hostel Bank" if mode == "Bank" else None, "account_head": f"{head} - {ABBR}", "amount": amount})  # fmt: skip
	_c, rows = rp_report({"company": COMPANY, "from_date": "2026-04-01", "to_date": "2026-09-30"})
	got = {r["particulars"]: r for r in rows}
	filed = {"Opening balance (Cash)": 682, "Opening balance (Bank)": 634446.84, "Loan from Zohra trust": 1230000, "Bank interest": 4779,
		"Food": 563825, "Fuel": 37780, "Detergent": 47400, "Salaries": 48000, "Transfer to Zohra trust": 700000,
		"Closing balance (Cash)": 33677, "Closing balance (Bank)": 439225}  # fmt: skip
	for row, want in filed.items():
		r = got.get(row, {})
		compare(f"R&P {row}", (r.get("receipts") or r.get("payments") or 0), want, tolerance=1 if "Bank" in row else 0.005)
	total = got["Total"]
	note(total["receipts"] == total["payments"], "R&P receipts total equals payments total", f"{total['receipts']:,.2f} | {total['payments']:,.2f} (filed 18,69,907.84 | 18,69,907)")


def run():
	LINES.clear()
	try:
		setup()
		enter_students()
		for month in (6, 7, 8, 9):
			print(f"--- {MONTH_NAMES[month]}")
			month_attendance(month)
			month_purchases(month)
			month_consumption(month)
			month_statement(month)
		print("--- Receipts and Payments, 1 April to 30 September 2026")
		receipts_and_payments()
	finally:
		frappe.set_user("Administrator")
		frappe.db.rollback()
	left = frappe.db.count("Company", {"name": COMPANY}) + frappe.db.count("User", {"email": ["in", list(USERS.values())]})
	note(left == 0, "cleanup: nothing left in the database")
	diffs = [l for l in LINES if not l[0]]
	print(f"{len(LINES) - len(diffs)} of {len(LINES)} comparisons match the filed numbers; {len(diffs)} differ")
