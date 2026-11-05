"""The master data a new site is loaded with, so the client can test straight away."""

import csv
import tempfile

import frappe
from frappe.tests.utils import FrappeTestCase

from zohra_trust.setup import master_data

COMPANY, ABBR = "Master Data Check", "MDC"


class TestMasterData(FrappeTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		master_data.load(COMPANY, ABBR)

	def test_load_creates_the_masters_and_is_safe_to_run_again(self):
		before = {dt: frappe.db.count(dt) for dt in ("Trust Class", "Trust Exam", "Trust School", "Trust Academic Year", "Employee")}
		master_data.load(COMPANY, ABBR)
		self.assertEqual(before, {dt: frappe.db.count(dt) for dt in before})  # nothing doubled
		self.assertEqual(frappe.db.count("Trust Class"), 10)
		self.assertEqual(sorted(frappe.get_all("Trust Exam", pluck="name")), ["Final", "Mid-term"])
		self.assertEqual(sorted(frappe.get_all("Trust School", pluck="name")), ["Zohra English Medium", "Zohra Kannada Medium"])
		self.assertTrue(frappe.db.exists("Trust Academic Year", "2026-27"))
		self.assertEqual(frappe.db.count("Employee", {"company": COMPANY}), 4)

	def test_unit_trust_and_typed_texts_are_ready_for_the_report(self):
		profile = frappe.get_doc("Trust Unit Profile", COMPANY)
		self.assertEqual((profile.sanctions[0].sanctioned_strength, profile.sanctions[0].grant_rate), (150, 850))
		self.assertIn("District Minority officer", profile.letter_text)
		self.assertIn("APPENDIX- H", profile.appendix_h_text)
		self.assertIn("Kalaburagi", profile.address)
		settings = frappe.get_single("Trust Settings")
		self.assertTrue(settings.trust_name)
		self.assertTrue(settings.officer_bearers)
		self.assertTrue(frappe.db.exists("Warehouse", f"Hostel Store - {ABBR}"))

	def test_texts_the_user_already_typed_are_not_overwritten(self):
		original = frappe.db.get_value("Trust Unit Profile", COMPANY, "letter_text")
		profile = frappe.get_doc("Trust Unit Profile", COMPANY)
		profile.letter_text = "<p>Typed by the office</p>"
		profile.save()
		master_data.load(COMPANY, ABBR)
		self.assertEqual(frappe.db.get_value("Trust Unit Profile", COMPANY, "letter_text"), "<p>Typed by the office</p>")
		profile = frappe.get_doc("Trust Unit Profile", COMPANY)
		profile.letter_text = original
		profile.save()

	def test_students_come_from_a_file_and_a_second_load_adds_nobody(self):
		with tempfile.NamedTemporaryFile("w", suffix=".csv", delete=False, newline="", encoding="utf-8") as handle:
			writer = csv.writer(handle)
			writer.writerow(["name", "class", "school"])
			writer.writerows([["Test Girl One", 5, "Zohra English Medium"], ["Test Girl Two", 10, "Zohra Kannada Medium"], ["Test Girl Three", 8, "Zohra English Medium"]])
		self.assertEqual(master_data.load_students(handle.name, COMPANY), 3)
		self.assertEqual(master_data.load_students(handle.name, COMPANY), 0)
		rows = frappe.get_all("Student Enrollment", {"unit": COMPANY}, ["register_sl_no", "trust_class", "school", "status"], order_by="register_sl_no")
		self.assertEqual([(r.register_sl_no, r.trust_class, r.status) for r in rows], [(1, "Class 5", "Enrolled"), (2, "Class 10", "Enrolled"), (3, "Class 8", "Enrolled")])

	def test_opening_balances_are_entered_once(self):
		master_data.load_opening_balances(682, 634446.84, COMPANY, ABBR)
		master_data.load_opening_balances(682, 634446.84, COMPANY, ABBR)
		self.assertEqual(frappe.db.count("Journal Entry", {"company": COMPANY, "user_remark": "Opening balances of 2026-03-31", "docstatus": 1}), 1)
		cash = frappe.db.sql("select sum(debit-credit) from `tabGL Entry` where company=%s and account=%s", (COMPANY, f"Cash - {ABBR}"))[0][0]
		self.assertEqual(cash, 682)
