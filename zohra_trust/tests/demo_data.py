"""Dummy data for clicking through the app in the browser.

bench --site <site> execute zohra_trust.tests.demo_data.load     (commits)
bench --site <site> execute zohra_trust.tests.demo_data.remove   (deletes it again)

Users demo.principal@, demo.entry@, demo.store@example.com, password Demo@12345.
The hostel "Demo Hostel" gets masters, 10 girls, opening balances and opening stock.
"""

import frappe
from frappe.utils.password import update_password

from zohra_trust.setup.create_unit import create_unit
from zohra_trust.tests.helpers import make_masters, make_student

COMPANY, ABBR = "Demo Hostel", "DEM"
USERS = {"Principal": "demo.principal@example.com", "Data Entry": "demo.entry@example.com", "Store": "demo.store@example.com"}
PASSWORD = "Demo@12345"


def load():
	for role, email in USERS.items():
		if not frappe.db.exists("User", email):
			frappe.get_doc({"doctype": "User", "email": email, "first_name": f"Demo {role}", "send_welcome_email": 0, "roles": [{"role": role}]}).insert()
		update_password(email, PASSWORD)
	if not frappe.db.exists("Fiscal Year", "2025-2026"):
		frappe.get_doc({"doctype": "Fiscal Year", "year": "2025-2026", "year_start_date": "2025-04-01", "year_end_date": "2026-03-31"}).insert()
	make_masters()
	create_unit(COMPANY, ABBR, sanctioned_strength=150, grant_rate=850, effective_from="2026-04-01")
	settings = frappe.get_doc("Trust Settings")
	settings.update({"trust_name": "Zohra Women & Children Charitable & Welfare Trust", "current_academic_year": "2026-27", "correction_window_days": 1})
	settings.save()
	if not frappe.db.exists("Journal Entry", {"user_remark": "Demo opening balances"}):
		entry = frappe.get_doc(
			{
				"doctype": "Journal Entry", "company": COMPANY, "posting_date": "2026-03-31", "user_remark": "Demo opening balances",
				"accounts": [
					{"account": f"Cash - {ABBR}", "debit_in_account_currency": 50000},
					{"account": f"Bank - {ABBR}", "debit_in_account_currency": 200000},
					{"account": f"Temporary Opening - {ABBR}", "credit_in_account_currency": 250000},
				],
			}
		)
		entry.insert()
		entry.submit()
		stock = frappe.get_doc(
			{
				"doctype": "Stock Entry", "stock_entry_type": "Material Receipt", "company": COMPANY, "posting_date": "2026-05-31", "set_posting_time": 1,
				"to_warehouse": f"Hostel Store - {ABBR}",
				"items": [{"item_code": "Rice", "qty": 50, "basic_rate": 49, "t_warehouse": f"Hostel Store - {ABBR}"}, {"item_code": "Sugar", "qty": 6, "basic_rate": 55, "t_warehouse": f"Hostel Store - {ABBR}"}],
			}
		)
		stock.insert()
		stock.submit()
	if not frappe.db.exists("Student Enrollment", {"unit": COMPANY}):
		for n in range(1, 11):
			make_student(COMPANY, n, trust_class=("Class 9", "Class 10", "Class 8")[n % 3])
	frappe.db.commit()
	print("Demo data loaded. Login: demo.principal@example.com /", PASSWORD)


def remove():
	"""Delete everything load() and later clicking made for Demo Hostel, plus the demo users."""
	frappe.flags.in_test = True
	for dt in ("Result Sheet of Inmates", "Food Expenditure Statement", "Boarding Attendance", "Material Consumption", "Cash Bank Voucher"):
		for name in frappe.get_all(dt, {"company": COMPANY}, pluck="name"):
			frappe.db.set_value(dt, name, "docstatus", 2)
			frappe.delete_doc(dt, name, force=1, ignore_permissions=True)
	for dt in ("Purchase Invoice", "Stock Entry", "Journal Entry", "Payment Entry"):
		for name in frappe.get_all(dt, {"company": COMPANY}, pluck="name"):
			frappe.db.set_value(dt, name, "docstatus", 2)
			frappe.delete_doc(dt, name, force=1, ignore_permissions=True)
	for dt in ("GL Entry", "Stock Ledger Entry", "Bin"):
		frappe.db.delete(dt, {"company": COMPANY} if dt != "Bin" else {"warehouse": ("like", f"%- {ABBR}")})
	enrolments = frappe.get_all("Student Enrollment", {"unit": COMPANY}, pluck="name")
	for name in enrolments:
		frappe.delete_doc("Student Enrollment", name, force=1, ignore_permissions=True)
	for name in frappe.get_all("Trust Student", {"home_unit": COMPANY}, pluck="name"):
		frappe.delete_doc("Trust Student", name, force=1, ignore_permissions=True)
	for dt in ("Trust Unit Profile",):
		for name in frappe.get_all(dt, {"company": COMPANY}, pluck="name"):
			frappe.delete_doc(dt, name, force=1, ignore_permissions=True)
	if frappe.db.exists("Company", COMPANY):
		frappe.delete_doc("Company", COMPANY, force=1, ignore_permissions=True)
	for email in USERS.values():
		if frappe.db.exists("User", email):
			frappe.delete_doc("User", email, force=1, ignore_permissions=True)
	frappe.db.commit()
	print("Demo data removed.")


def add_june_purchases():
	"""Cash purchases dated June 2026 so the Food Expenditure Statement has something to show."""
	from zohra_trust.tests.helpers import purchase

	purchase(ABBR, COMPANY, "2026-06-10", {"Rice": (100, 4900), "Sugar": (20, 1100)})
	purchase(ABBR, COMPANY, "2026-06-12", {"Vegetables": (1, 1500)}, stock=False)
	frappe.db.commit()
	print("June purchases added.")
