"""Test data for the client: the Zohra Minority Girls Hostel with fictional girls and the filed June to September 2026 figures.

    bench --site <site> execute zohra_trust.setup.client_test_data.load
    bench --site <site> execute zohra_trust.setup.client_test_data.remove      # to start again

It loads the masters (see master_data), 50 fictional girls, the opening balances and stock of the filed report,
and every purchase, kitchen entry, salary and trust money movement of June to September 2026.
The client then does the month-end part by hand and compares with CLIENT_TEST_GUIDE.pdf:
Boarding Attendance, Food Expenditure Statement, Receipts and Payments, Result Sheet, Promote, Report Pack.

Nothing here runs on install. `load` refuses to run on a hostel that already has students or entries,
so it cannot touch real records by mistake.
"""

import frappe

from zohra_trust.setup import master_data
from zohra_trust.setup.filed_figures import JUNE_OLD, MONTH_NAMES, MONTHS

COMPANY, ABBR = master_data.COMPANY, master_data.ABBR

# Fictional names. Class and school are given; the marks follow from MARK_SHARES.
NAMES = (
	"Aaliya Parveen", "Afreen Tabassum", "Alina Sultana", "Amreen Taj", "Anjum Ara", "Arfa Naz", "Asiya Khatoon", "Atiya Begum", "Azra Jabeen", "Bushra Anjum",
	"Dilshad Banu", "Farhana Kausar", "Farzana Bi", "Firdous Ara", "Ghazala Parveen", "Gulshan Taj", "Habiba Noor", "Hafsa Sultana", "Halima Begum", "Huma Fatima",
	"Iqra Jabeen", "Irfana Khanum", "Jasmin Taj", "Jaweria Naz", "Kausar Banu", "Khadija Tabassum", "Kulsum Begum", "Laiba Fatima", "Lubna Parveen", "Mahira Sultana",
	"Maryam Noor", "Misbah Ara", "Mubashira Bi", "Nadia Khatoon", "Nafisa Banu", "Naila Anjum", "Nazia Taj", "Nikhat Jabeen", "Noorjahan Begum", "Quratulain Fatima",
	"Rabia Sultana", "Rehmat Bi", "Rukhsar Banu", "Sabeena Taj", "Sadaf Parveen", "Saira Khatoon", "Salma Noor", "Shabana Anjum", "Shagufta Begum", "Sidra Fatima",
)  # fmt: skip
CLASSES = (3, 4, 5, 6, 7, 8, 9, 10)  # cycled, so every class has girls
MARK_SHARES = (0.62, 0.55, 0.7, 0.48, 0.66, 0.8, 0.58, 0.74)  # share of the total marks, cycled
FAIL_ROWS = (7, 19, 44)  # three girls fail, so Repeat and Left with T.C. can be shown
TOTAL_MARKS = {1: 250, 2: 250, 3: 250, 4: 250, 5: 250, 6: 480, 7: 480, 8: 480, 9: 480, 10: 625}


def girls():
	"""(register number, name, class, school, total marks, marks obtained, result) for the 50 girls."""
	out = []
	for n, name in enumerate(NAMES, 1):
		klass = CLASSES[(n - 1) % len(CLASSES)]
		total = TOTAL_MARKS[klass]
		fail = n in FAIL_ROWS
		marks = round(total * (0.3 if fail else MARK_SHARES[(n - 1) % len(MARK_SHARES)]))
		out.append((n, name, klass, "Zohra English Medium" if n <= 30 else "Zohra Kannada Medium", total, marks, "Fail" if fail else "Pass"))
	return out


def load(company=COMPANY, abbr=ABBR):
	if frappe.db.count("Trust Student", {"home_unit": company}) or frappe.db.count("Boarding Attendance", {"company": company}):
		frappe.throw(f"{company} already has students or entries. Client test data is loaded into an empty hostel only; run `remove` first.")
	master_data.load(company, abbr)
	master_data.load_opening_balances(682, 634446.84, company, abbr)
	master_data.add_students([(name, klass, school) for _n, name, klass, school, *_rest in girls()], company)
	store = f"Hostel Store - {abbr}"
	stock = frappe.get_doc(
		{
			"doctype": "Stock Reconciliation", "company": company, "purpose": "Opening Stock", "set_posting_time": 1, "posting_date": "2026-05-31", "posting_time": "12:00:00",
			"expense_account": f"Temporary Opening - {abbr}",
			"items": [{"item_code": i, "warehouse": store, "qty": q, "valuation_rate": a / q} for i, (q, a) in JUNE_OLD.items()],
		}
	)
	stock.insert()
	stock.submit()
	load_entries(company, abbr)
	print("Client test data is ready. Now do the month-end documents by hand (see CLIENT_TEST_GUIDE).")


def load_entries(company=COMPANY, abbr=ABBR):
	"""Purchases, kitchen use, salaries and the trust's money movements of June to September 2026."""
	store = f"Hostel Store - {abbr}"
	for month in (6, 7, 8, 9):
		purchases, consumed, heads = MONTHS[month]
		date = f"2026-{month:02d}-02"
		purchase(company, abbr, date, [{"item_code": i, "qty": q, "rate": a / q, "warehouse": store} for i, (q, a) in purchases.items()], sum(a for _q, a in purchases.values()), True)
		nonstock = {h: a for h, a in heads.items() if h in ("Vegetables", "Mutton", "Fuel")}
		purchase(company, abbr, f"2026-{month:02d}-03", [{"item_code": h, "qty": 1, "rate": a} for h, a in nonstock.items()], sum(nonstock.values()), False)
		voucher(company, abbr, "Payment", "Salaries", heads["Salaries"], f"2026-{month:02d}-05", "Cash", f"{MONTH_NAMES[month]} salaries")
		first = {i: q // 2 for i, q in consumed.items()}
		consume(company, f"2026-{month:02d}-15", first)
		consume(company, f"2026-{month:02d}-28", {i: consumed[i] - first[i] for i in consumed})
	for kind, head, amount, date, mode in (
		("Receipt", "Zohra trust", 730000, "2026-04-05", "Cash"), ("Receipt", "Zohra trust", 500000, "2026-04-06", "Bank"),
		("Receipt", "Bank interest", 4779, "2026-09-30", "Bank"), ("Payment", "Zohra trust", 700000, "2026-08-20", "Bank"),
	):
		voucher(company, abbr, kind, head, amount, date, mode, "")


def purchase(company, abbr, date, items, total, stock):
	doc = frappe.get_doc(
		{
			"doctype": "Purchase Invoice", "company": company, "supplier": "Cash purchase", "posting_date": date, "bill_date": date, "set_posting_time": 1,
			"update_stock": 1 if stock else 0, "set_warehouse": f"Hostel Store - {abbr}" if stock else None, "is_paid": 1, "mode_of_payment": "Cash",
			"cash_bank_account": f"Cash - {abbr}", "paid_amount": total, "items": items,
		}
	)
	doc.insert()
	doc.submit()


def voucher(company, abbr, kind, head, amount, date, mode, narration):
	doc = frappe.get_doc(
		{
			"doctype": "Cash Bank Voucher", "company": company, "voucher_type": kind, "posting_date": date, "mode": mode,
			"bank_account": f"{company} - Hostel Bank" if mode == "Bank" else None, "account_head": f"{head} - {abbr}", "amount": amount, "narration": narration,
		}
	)
	doc.insert()
	doc.submit()


def consume(company, date, quantities):
	doc = frappe.get_doc({"doctype": "Material Consumption", "company": company, "posting_date": date, "items": [{"item_code": i, "qty": q} for i, q in quantities.items() if q]})
	doc.insert()
	doc.submit()


def remove(company=COMPANY):
	"""Delete the hostel and everything entered for it, to load the test data again. Only for a test site."""
	from zohra_trust.tests.real_data import clear_company

	clear_company(company)
	print(f"{company} removed.")
