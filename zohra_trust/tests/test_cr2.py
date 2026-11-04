"""Change request 2: Officer Bearer address and Member; the October 2024 to March 2025 filing (132 girls, every girl present)."""

import frappe
from frappe.tests.utils import FrappeTestCase

from zohra_trust.tests.helpers import make_attendance, make_masters, make_student, make_unit
from zohra_trust.utils.report_pages import build_pages

HOSTEL, ABBR = "Test Hostel D", "THD"
YEAR_2024 = "2024-25"

# month, year, calendar days x 132, school days, school attendance (132 x school days): the filed abstract
FILED = (
	("October", 2024, 4092, 22, 2904),
	("November", 2024, 3960, 24, 3168),
	("December", 2024, 4092, 22, 2904),
	("January", 2025, 4092, 26, 3432),
	("February", 2025, 3696, 23, 3036),
	("March", 2025, 4092, 24, 3168),
)


class TestSecondFiling(FrappeTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		make_masters()
		if not frappe.db.exists("Trust Academic Year", YEAR_2024):
			frappe.get_doc(
				{"doctype": "Trust Academic Year", "academic_year_name": YEAR_2024, "start_date": "2024-04-01", "end_date": "2025-03-31"}
			).insert()
		make_unit(HOSTEL, ABBR)
		profile = frappe.get_doc("Trust Unit Profile", HOSTEL)
		profile.sanctions[0].effective_from = "2024-04-01"  # strength 150 was already in force in 2024
		profile.save()
		for n in range(1, 133):
			make_student(HOSTEL, n, enrollment_date="2024-04-01", academic_year=YEAR_2024)

	def test_132_girls_every_one_present_gives_the_filed_abstract(self):
		for month, year, hostel, school_days, school in FILED:
			doc = make_attendance(HOSTEL, month, year, working_days=(school_days, school_days))
			doc.fill_rows()
			self.assertEqual(doc.students_on_roll, 132, month)
			self.assertEqual(doc.sanctioned_strength, 150, month)
			self.assertEqual(doc.total_hostel_days, hostel, month)
			self.assertEqual(doc.total_school_days_present, school, month)

	def test_officer_bearer_address_member_and_the_page_column(self):
		settings = frappe.get_single("Trust Settings")
		before = [o.as_dict() for o in settings.officer_bearers]
		try:
			settings.officer_bearers = []
			settings.append(
				"officer_bearers",
				{"member_name": "Dr Test Member", "designation": "Member", "qualification": "B.E, M.TECH, Ph.D", "address": "12 Station Road, Kalaburagi", "sort_order": 1, "is_active": 1},
			)
			settings.save()
			pages, _warnings = build_pages(HOSTEL, "2024-10-01", "2025-03-31")
			page = next(p for p in pages if p["key"] == "officer_bearers")
			self.assertIn("ADDRESS", page["html"])
			self.assertIn("12 Station Road, Kalaburagi", page["html"])
			self.assertIn("Member", page["html"])
		finally:
			settings.officer_bearers = []
			for row in before:
				settings.append("officer_bearers", row)
			settings.save()

	def test_old_designations_are_still_options(self):
		options = frappe.get_meta("Officer Bearer").get_field("designation").options.split("\n")
		self.assertEqual([o for o in options if o], ["President", "Secretary", "Joint Secretary", "Member", "Trustee"])
