"""The numbers in docs/Zohra_Trust_Do_It_Yourself.pdf.

The workbook tells a person to enter this exact data in an empty hostel and says what every sheet will show. This test enters
the same data and checks those figures, so the workbook cannot drift from the system.
"""

import frappe
from frappe.tests.utils import FrappeTestCase

from zohra_trust.tests.helpers import consume, make_attendance, make_student, make_unit, purchase
from zohra_trust.trust_operations.report.receipts_and_payments_account.receipts_and_payments_account import execute as rp

COMPANY, ABBR = "Test Hostel W", "THW"

# month: (Rice rate, Sugar rate paid, vegetables, salaries, school days English, Kannada)
MONTHS = {6: ("June", 55, 1500, 9000), 7: ("July", 60, 2000, 9000), 8: ("August", 60, 2000, 9000), 9: ("September", 60, 2000, 9000)}

# expected statement totals: opening, purchase, available, expenditure, closing
STATEMENTS = {
	"June": (3050, 16050, 19100, 14940, 4160),
	"July": (4160, 16600, 20760, 16100, 4660),
	"August": (4660, 16600, 21260, 16100, 5160),
	"September": (5160, 16600, 21760, 16100, 5660),
}


def voucher(kind, head, amount, date):
	doc = frappe.get_doc({"doctype": "Cash Bank Voucher", "company": COMPANY, "voucher_type": kind, "posting_date": date, "mode": "Cash", "account_head": f"{head} - {ABBR}", "amount": amount})
	doc.insert()
	doc.submit()


class TestWorkbookNumbers(FrappeTestCase):
	def test_the_workbook_data_gives_the_workbook_figures(self):
		make_unit(COMPANY, ABBR)
		opening = frappe.get_doc(
			{"doctype": "Journal Entry", "company": COMPANY, "posting_date": "2026-03-31", "accounts": [
				{"account": f"Cash - {ABBR}", "debit_in_account_currency": 50000}, {"account": f"Bank - {ABBR}", "debit_in_account_currency": 200000},
				{"account": f"Temporary Opening - {ABBR}", "credit_in_account_currency": 250000}]}
		)
		opening.insert()
		opening.submit()
		girls = [("Ayesha Begum", "Class 8", 0, "Abdul Karim"), ("Fouzia Sultana", "Class 9", 0, None), ("Gousia Bano", "Class 10", 1, "Gouse Pasha"), ("Hajira Khatoon", "Class 10", 1, None)]
		for n, (name, cls, kannada, father) in enumerate(girls, 1):
			enrollment = make_student(COMPANY, n, trust_class=cls, guardian=father)
			if kannada:
				frappe.db.set_value("Student Enrollment", enrollment.name, "school", "Zohra Kannada Medium")
		from zohra_trust.tests.helpers import seed_stock

		stock = frappe.get_doc(
			{"doctype": "Stock Reconciliation", "company": COMPANY, "purpose": "Opening Stock", "posting_date": "2026-05-31", "posting_time": "12:00:00", "set_posting_time": 1,
			 "expense_account": f"Temporary Opening - {ABBR}", "items": [
				{"item_code": "Rice", "warehouse": f"Hostel Store - {ABBR}", "qty": 50, "valuation_rate": 50}, {"item_code": "Sugar", "warehouse": f"Hostel Store - {ABBR}", "qty": 10, "valuation_rate": 55}]}
		)
		stock.insert()
		stock.submit()
		voucher("Receipt", "Zohra trust", 20000, "2026-04-05")
		voucher("Receipt", "Govt. grant received", 20400, "2026-06-30")
		days = {6: 30, 7: 31, 8: 31, 9: 30}
		for m, (month, sugar_rate, vegetables, salaries) in MONTHS.items():
			stamp = f"2026-{m:02d}"
			if m == 6:
				purchase(ABBR, COMPANY, f"{stamp}-10", {"Rice": (100, 5000), "Sugar": (10, 550)})
				purchase(ABBR, COMPANY, f"{stamp}-10", {"Vegetables": (1, vegetables)}, stock=False)
				consume(COMPANY, f"{stamp}-15", {"Rice": 40, "Sugar": 4})
				consume(COMPANY, f"{stamp}-16", {"Rice": 40, "Sugar": 4})
			else:
				purchase(ABBR, COMPANY, f"{stamp}-03", {"Rice": (100, 5000), "Sugar": (10, 600)})
				purchase(ABBR, COMPANY, f"{stamp}-04", {"Vegetables": (1, vegetables)}, stock=False)
				consume(COMPANY, f"{stamp}-15", {"Rice": 45, "Sugar": 5})
				consume(COMPANY, f"{stamp}-16", {"Rice": 45, "Sugar": 5})
			voucher("Payment", "Salaries", salaries, f"{stamp}-28")
			attendance = make_attendance(COMPANY, month, 2026, working_days=(26, 25))
			attendance.fill_rows()
			attendance.insert()
			attendance.submit()
			self.assertEqual((attendance.students_on_roll, attendance.total_hostel_days, attendance.total_grant), (4, 4 * days[m], 3400))
			statement = frappe.get_doc({"doctype": "Food Expenditure Statement", "company": COMPANY, "month": month, "year": 2026, "is_opening": 1 if m == 6 else 0})
			statement.fill()
			statement.insert()
			statement.submit()
			got = (statement.total_opening, statement.total_purchase, statement.total_available, statement.total_expenditure, statement.total_closing)
			self.assertEqual(got, STATEMENTS[month], month)
		_c, rows = rp({"company": COMPANY, "from_date": "2026-04-01", "to_date": "2026-09-30"})
		by = {r["particulars"]: r for r in rows}
		self.assertEqual(by["Opening balance (Cash)"]["receipts"], 50000)
		self.assertEqual(by["Opening balance (Bank)"]["receipts"], 200000)
		self.assertEqual(by["Loan from Zohra trust"]["receipts"], 20000)
		self.assertEqual(by["Govt. grant received"]["receipts"], 20400)
		self.assertEqual(by["Food"]["payments"], 29850)
		self.assertEqual(by["Salaries"]["payments"], 36000)
		self.assertEqual(by["Closing balance (Cash)"]["payments"], 24550)
		self.assertEqual(by["Closing balance (Bank)"]["payments"], 200000)
		self.assertEqual((by["Total"]["receipts"], by["Total"]["payments"]), (290400, 290400))
