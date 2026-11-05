"""The client test data gives, step by step, the figures the client test guide promises."""

import frappe
from frappe.tests.utils import FrappeTestCase

from zohra_trust.setup import client_test_data
from zohra_trust.setup.filed_figures import FILED_TOTALS, MONTH_NAMES
from zohra_trust.tests.helpers import make_attendance
from zohra_trust.trust_operations.report.receipts_and_payments_account.receipts_and_payments_account import execute as rp_report

COMPANY, ABBR = "Client Test Check", "CTC"


class TestClientTestData(FrappeTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		client_test_data.load(COMPANY, ABBR)

	def test_fifty_fictional_girls_across_the_classes_and_both_schools(self):
		rows = client_test_data.girls()
		self.assertEqual(len(rows), 50)
		self.assertEqual(len({r[1] for r in rows}), 50)  # no repeated name
		self.assertEqual(frappe.db.count("Student Enrollment", {"unit": COMPANY, "status": "Enrolled"}), 50)
		self.assertEqual({r[2] for r in rows}, {3, 4, 5, 6, 7, 8, 9, 10})
		self.assertEqual(sum(1 for r in rows if r[6] == "Fail"), 3)
		self.assertTrue(all(r[5] <= r[4] for r in rows))  # nobody above the total marks

	def test_it_refuses_to_run_on_a_hostel_that_already_has_girls(self):
		with self.assertRaises(frappe.ValidationError):
			client_test_data.load(COMPANY, ABBR)

	def test_the_guide_figures_come_out_month_by_month(self):
		for month in (6, 7, 8, 9):
			name = MONTH_NAMES[month]
			attendance = make_attendance(COMPANY, name, working_days=(25, 25))
			attendance.fill_rows()
			attendance.insert()
			attendance.submit()
			days = (30, 31, 31, 30)[month - 6]
			self.assertEqual((attendance.students_on_roll, attendance.total_hostel_days, attendance.total_grant), (50, 50 * days, 50 * 850), name)
			statement = frappe.get_doc({"doctype": "Food Expenditure Statement", "company": COMPANY, "month": name, "year": 2026, "is_opening": 1 if month == 6 else 0})
			statement.fill()
			statement.insert()
			statement.submit()
			got = (statement.total_opening, statement.total_purchase, statement.total_available, statement.total_expenditure, statement.total_closing)
			for a, b in zip(got, FILED_TOTALS[month]):
				self.assertAlmostEqual(a, b, delta=0.5, msg=name)
		_columns, rows = rp_report({"company": COMPANY, "from_date": "2026-04-01", "to_date": "2026-09-30"})
		by = {r["particulars"]: r for r in rows}
		self.assertEqual(by["Food"]["payments"], 579598)
		self.assertEqual(by["Closing balance (Cash)"]["payments"], 17904)
		self.assertAlmostEqual(by["Closing balance (Bank)"]["payments"], 439225.84, places=2)
		self.assertEqual(by["Total"]["receipts"], by["Total"]["payments"])
