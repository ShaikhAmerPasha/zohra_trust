"""End-to-end flow check, run as real role users, then rolled back.

Run: bench --site <site> execute zohra_trust.tests.flow.run

Each phase adds one step function. Nothing stays in the database: the run ends with a
rollback and then confirms that no test record is left.
"""

import contextlib

import frappe

from zohra_trust.tests.helpers import SCHOOLS, consume, make_attendance, make_student, make_unit, pay_expense, purchase, seed_stock

COMPANY, ABBR = "Flow Hostel", "FLH"
USERS = {"Principal": "flow.principal@example.com", "Data Entry": "flow.entry@example.com", "Store": "flow.store@example.com"}
RESULTS = []


@contextlib.contextmanager
def as_user(role):
	frappe.set_user(USERS[role])
	try:
		yield
	finally:
		frappe.set_user("Administrator")


def check(label, condition):
	RESULTS.append((label, bool(condition)))
	print(("PASS  " if condition else "FAIL  ") + label)


def setup_users():
	for role, email in USERS.items():
		frappe.get_doc({"doctype": "User", "email": email, "first_name": role, "send_welcome_email": 0, "roles": [{"role": role}]}).insert()


def phase_1():
	"""Masters, students, enrollments, monthly Boarding Attendance."""
	make_unit(COMPANY, ABBR)
	with as_user("Principal"):
		for n in range(1, 6):
			make_student(COMPANY, n)
	with as_user("Data Entry"):
		doc = make_attendance(COMPANY, "June")
		doc.fill_rows()
		doc.insert()
		doc.submit()
		check("1: Data Entry fills, saves and submits June Boarding Attendance", doc.docstatus == 1 and doc.students_on_roll == 5)
		check("1: hostel days 5 girls x 30 = 150, grant 5 x 850", (doc.total_hostel_days, doc.total_grant) == (150, 4250))
		check("1: Data Entry can cancel own sheet inside the window", doc.cancel() and doc.docstatus == 2)
	with as_user("Principal"):
		check("1: Principal reads the sheet", frappe.has_permission("Boarding Attendance", "read", doc=doc.name))


def phase_2():
	"""Cash purchases, daily Material Consumption, monthly Food Expenditure Statement."""
	seed_stock(ABBR, COMPANY, "2026-05-31", {"Rice": (50, 2450)})
	with as_user("Store"):
		purchase(ABBR, COMPANY, "2026-06-02", {"Rice": (100, 4900)})
		purchase(ABBR, COMPANY, "2026-06-03", {"Vegetables": (1, 1500)}, stock=False)
		mc = consume(COMPANY, "2026-06-15", {"Rice": 40})
		check("2: Store submits Material Consumption, Stock Entry is made", frappe.db.get_value("Stock Entry", mc.stock_entry, "docstatus") == 1)
		check("2: stock is 110 after consuming 40 of 150", frappe.db.get_value("Bin", {"item_code": "Rice", "warehouse": f"Hostel Store - {ABBR}"}, "actual_qty") == 110)
	pay_expense(ABBR, COMPANY, "2026-06-04", "Salaries", 3000)
	with as_user("Data Entry"):
		fes = frappe.get_doc({"doctype": "Food Expenditure Statement", "company": COMPANY, "month": "June", "year": 2026, "is_opening": 1})
		fes.fill()
		rice = [l for l in fes.lines if l.item_code == "Rice"][0]
		rice.old_qty, rice.old_amount = 50, 2450
		fes.insert()
		fes.submit()
		rice = [l for l in fes.lines if l.item_code == "Rice"][0]
		check("2: Rice line: 150 available, 40 used = 1,960, balance 110 = 5,390", (rice.total_qty, rice.expenditure_amount, rice.balance_amount) == (150, 1960, 5390))
		heads = {l.account.split(" - ")[0]: l.purchased_amount for l in fes.lines if l.line_type == "Expense Head"}
		check("2: amount-only rows pick up vegetables and salary", (heads["Vegetables"], heads["Salaries"]) == (1500, 3000))
		check("2: closing = available - expenditure", fes.total_closing == fes.total_available - fes.total_expenditure)
	with as_user("Store"):
		mc.cancel()
		check("2: Store cancels own consumption, stock restored to 150", frappe.db.get_value("Bin", {"item_code": "Rice", "warehouse": f"Hostel Store - {ABBR}"}, "actual_qty") == 150)


def phase_3():
	"""Cash Bank Vouchers and the Receipts and Payments Account."""
	from zohra_trust.trust_operations.report.receipts_and_payments_account.receipts_and_payments_account import execute

	def voucher(voucher_type, head, amount, date, mode="Cash"):
		doc = frappe.get_doc(
			{
				"doctype": "Cash Bank Voucher", "company": COMPANY, "voucher_type": voucher_type, "posting_date": date, "mode": mode,
				"bank_account": f"{COMPANY} - Hostel Bank" if mode == "Bank" else None,
				"account_head": f"{head} - {ABBR}", "amount": amount,
			}
		)
		doc.insert()
		doc.submit()
		return doc

	with as_user("Data Entry"):
		grant = voucher("Receipt", "Govt. grant received", 85000, "2026-06-10")
		bank = voucher("Receipt", "Zohra trust", 50000, "2026-06-11", mode="Bank")
		pay = voucher("Payment", "Salaries", 11000, "2026-06-12")
		check("3: Data Entry submits vouchers, each makes a Journal Entry", all(frappe.db.get_value("Journal Entry", d.journal_entry, "docstatus") == 1 for d in (grant, bank, pay)))
		try:
			frappe.get_doc("Journal Entry", pay.journal_entry).cancel()
			direct = False
		except (frappe.ValidationError, frappe.PermissionError):
			direct = True
		check("3: cancelling the Journal Entry directly is refused", direct)
	with as_user("Principal"):
		_c, rows = execute({"company": COMPANY, "from_date": "2026-06-01", "to_date": "2026-06-30"})
		got = {r["particulars"]: r for r in rows}
		check("3: report shows grant, loan and salaries on their rows", (got["Govt. grant received"]["receipts"], got["Loan from Zohra trust"]["receipts"], got["Salaries"]["payments"]) == (85000, 50000, 14000))  # 14,000 = 11,000 here + 3,000 paid in phase 2
		check("3: receipts equal payments", got["Total"]["receipts"] == got["Total"]["payments"])
	with as_user("Data Entry"):
		pay.cancel()
		check("3: cancelling the voucher cancels its Journal Entry", frappe.db.get_value("Journal Entry", pay.journal_entry, "docstatus") == 2)


def phase_5():
	"""Final exam result sheet and promotion to next year."""
	with as_user("Data Entry"):
		doc = frappe.get_doc({"doctype": "Result Sheet of Inmates", "company": COMPANY, "academic_year": "2026-27", "exam": "Final", "exam_date": "2027-03-10"})
		doc.fill_rows()
		check("5: Fill Students lists the 5 enrolled girls with maximum marks for their class", len(doc.rows) == 5 and {r.max_marks for r in doc.rows} == {250, 480, 625})
		marks = {1: (400, "Pass", None, None), 2: (500, "Pass", None, "Working women hostel"), 3: (60, "Fail", None, None), 4: (410, "Pass", None, None), 5: (0, "Absent", "Leave", "Other")}
		for row in doc.rows:
			row.marks_obtained, row.result, action, destination = marks[row.register_sl_no]
			row.promotion_action = action or row.promotion_action
			row.leaving_destination = destination
		doc.insert()
		doc.submit()
		check("5: totals 4 appeared, 3 passed, 1 failed", (doc.appeared, doc.passed, doc.failed) == (4, 3, 1))
		doc.promote()
	planned = frappe.get_all("Student Enrollment", {"unit": COMPANY, "academic_year": "2027-28"}, ["trust_class", "status", "is_repeating"], order_by="register_sl_no")
	check("5: girls 1, 3 and 4 get Planned enrollments next year (two promoted, one repeating)", [(p.trust_class, p.status, p.is_repeating) for p in planned] == [("Class 10", "Planned", 0), ("Class 8", "Planned", 1), ("Class 10", "Planned", 0)])
	statuses = frappe.get_all("Trust Student", {"home_unit": COMPANY}, ["status"], order_by="name")
	check("5: one girl Passed Out, one Left, three Active", sorted(s.status for s in statuses) == ["Active", "Active", "Active", "Left", "Passed Out"])
	with as_user("Principal"):
		enrollment = frappe.get_doc("Student Enrollment", {"unit": COMPANY, "academic_year": "2027-28", "is_repeating": 0})
		enrollment.status = "Enrolled"
		enrollment.save()
		check("5: Principal confirms a Planned enrollment to Enrolled", enrollment.status == "Enrolled")


PHASES = [phase_1, phase_2, phase_3, phase_5]


def run(upto=None):
	RESULTS.clear()
	frappe.flags.in_test = True
	try:
		setup_users()
		for phase in PHASES[:upto]:
			print(f"--- {phase.__name__}: {phase.__doc__}")
			phase()
	finally:
		frappe.set_user("Administrator")
		frappe.db.rollback()
	left = frappe.db.count("Company", {"name": COMPANY}) + frappe.db.count("Trust Student", {"home_unit": COMPANY})
	left += frappe.db.count("User", {"email": ["in", list(USERS.values())]})
	check("cleanup: no flow data left in the database", left == 0)
	failed = [label for label, ok in RESULTS if not ok]
	print(f"{len(RESULTS) - len(failed)}/{len(RESULTS)} flow checks passed")
	return {"passed": not failed, "failed": failed}
