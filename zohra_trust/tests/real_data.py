"""Clear the demo hostels, then load the real hostel for a client demonstration.

    bench --site <site> execute zohra_trust.tests.real_data.clear_demo
    bench --site <site> execute zohra_trust.tests.real_data.load_masters
    bench --site <site> execute zohra_trust.tests.real_data.load_entries

The month-end documents (Boarding Attendance, Food Expenditure Statement, Result Sheet, Report Pack) are made
on screen, so the client sees the Fill buttons work. Figures are the filed June to September 2026 figures
(tests/e2e_filed_half_year.py); the girls are the first 50 names of the filed result sheet.
"""

import frappe

from zohra_trust.setup.filed_figures import JUNE_OLD

COMPANY, ABBR = "Zohra Minority Girls Hostel", "ZMH"
DEMO_COMPANIES = ("Demo Hostel", "Demo Hostel Two", "Practice Hostel", "Test Run Hostel", "Flow Demo Hostel")
STORE = f"Hostel Store - {ABBR}"

PRIVATE_GIRLS = "/home/ameer/zohra_private/girls_2026.csv"  # the first 50 names of the filed result sheet; children's names are not kept in Git


def girls():
	"""(name, class, total marks, marks obtained) from the private file."""
	import csv

	with open(PRIVATE_GIRLS, newline="", encoding="utf-8") as handle:
		return [(r["name"], int(r["class"]), int(r["total_marks"]), int(r["marks_obtained"])) for r in csv.DictReader(handle)]



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
	"""The real hostel: the masters, the opening balances, the 50 girls from the private file, the opening stock."""
	frappe.flags.in_test = True
	from zohra_trust.setup import master_data

	master_data.load(COMPANY, ABBR)
	master_data.load_opening_balances(682, 634446.84, COMPANY, ABBR)
	master_data.load_students(PRIVATE_GIRLS, COMPANY)
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
	from zohra_trust.setup import client_test_data

	client_test_data.load_entries(COMPANY, ABBR)
	frappe.db.commit()
	print("entries loaded")
