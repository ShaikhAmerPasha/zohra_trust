import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.utils import add_days, now_datetime

from zohra_trust.tests.helpers import make_attendance, make_masters, make_student, make_unit
from zohra_trust.utils.sanction import get_unit_sanction

HOSTEL_A = "Test Hostel A"
HOSTEL_B = "Test Hostel B"


class TestMasters(FrappeTestCase):
	def test_academic_year_overlap_refused(self):
		make_masters()
		with self.assertRaises(frappe.ValidationError):
			frappe.get_doc(
				{"doctype": "Trust Academic Year", "academic_year_name": "2026-27b", "start_date": "2027-03-01", "end_date": "2027-12-31"}
			).insert()

	def test_leaving_date_required_unless_active(self):
		make_unit(HOSTEL_A, "THA")
		student = frappe.get_doc(
			{"doctype": "Trust Student", "student_name": "X", "home_unit": HOSTEL_A, "admission_date": "2026-04-01", "status": "Left"}
		)
		with self.assertRaises(frappe.ValidationError):
			student.insert()
		student.leaving_date = "2026-06-01"
		student.insert()

	def test_sanction_lookup_latest_effective_wins(self):
		make_unit(HOSTEL_A, "THA")
		profile = frappe.get_doc("Trust Unit Profile", HOSTEL_A)
		if len(profile.sanctions) == 1:
			profile.append("sanctions", {"effective_from": "2027-01-01", "sanctioned_strength": 160, "grant_rate": 900})
			profile.save()
		self.assertEqual(get_unit_sanction(HOSTEL_A, "2026-12-31").strength, 150)
		self.assertEqual(get_unit_sanction(HOSTEL_A, "2027-01-01").strength, 160)
		self.assertIsNone(get_unit_sanction(HOSTEL_A, "2026-03-31"))


class TestBoardingAttendance(FrappeTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		make_unit(HOSTEL_A, "THA")
		for n in range(1, 101):
			make_student(HOSTEL_A, n)
		profile = frappe.get_doc("Trust Unit Profile", HOSTEL_A)
		# a later rate and a later, lower strength; each effective on its own date
		profile.sanctions = profile.sanctions[:1]
		profile.append("sanctions", {"effective_from": "2026-11-01", "sanctioned_strength": 150, "grant_rate": 900})
		profile.append("sanctions", {"effective_from": "2026-12-01", "sanctioned_strength": 90, "grant_rate": 900})
		profile.save()

	def filled(self, month):
		doc = make_attendance(HOSTEL_A, month)
		doc.fill_rows()
		return doc

	def test_hostel_days_by_month(self):
		for month, days in (("June", 3000), ("July", 3100), ("August", 3100), ("September", 3000)):
			doc = self.filled(month)
			self.assertEqual(doc.total_hostel_days, days, month)
			self.assertEqual(doc.students_on_roll, 100)
			self.assertEqual(doc.total_grant, 100 * 850, month)
		doc.insert()
		self.assertEqual(doc.name, "BAT-THA-2026-09")

	def test_grant_follows_rate_in_force(self):
		doc = self.filled("November")
		self.assertEqual(doc.grant_rate, 900)
		self.assertEqual(doc.total_grant, 100 * 900)

	def test_above_strength_refused(self):
		with self.assertRaises(frappe.ValidationError):
			self.filled("December")

	def test_second_for_same_month_refused(self):
		self.filled("June").insert()
		with self.assertRaises(frappe.DuplicateEntryError):
			self.filled("June").insert()

	def test_days_checks(self):
		doc = self.filled("June")
		doc.rows[0].hostel_days = 31
		with self.assertRaises(frappe.ValidationError):
			doc.validate()
		doc.rows[0].hostel_days = 30
		doc.rows[0].school_days_present = 99
		with self.assertRaises(frappe.ValidationError):
			doc.validate()

	def test_school_without_working_days_refused(self):
		doc = make_attendance(HOSTEL_A, "June")
		doc.school_days = doc.school_days[:1]
		with self.assertRaises(frappe.ValidationError):
			doc.fill_rows()

	def test_mid_month_joiner_counts_from_enrollment_date(self):
		student = make_student(HOSTEL_A, 101, enrollment_date="2026-06-11", register=101)
		doc = self.filled("June")
		row = [r for r in doc.rows if r.enrollment == student.name][0]
		self.assertEqual(row.hostel_days, 20)
		self.assertEqual(doc.students_on_roll, 101)
		student.status = "Left"
		student.save()

	def test_period_closed_refused(self):
		frappe.get_doc(
			{
				"doctype": "Accounting Period",
				"period_name": "THA closed May",
				"company": HOSTEL_A,
				"start_date": "2026-05-01",
				"end_date": "2026-05-31",
				"closed_documents": [{"document_type": "Boarding Attendance", "closed": 1}],
			}
		).insert()
		with self.assertRaises(frappe.ValidationError):
			self.filled("May")

	def test_correction_window(self):
		doc = self.filled("October")
		doc.insert()
		doc.submit()
		user = "data.entry.test@example.com"
		if not frappe.db.exists("User", user):
			frappe.get_doc(
				{"doctype": "User", "email": user, "first_name": "DE", "send_welcome_email": 0, "roles": [{"role": "Data Entry"}]}
			).insert()
		frappe.db.set_value("Boarding Attendance", doc.name, "owner", user)
		frappe.db.set_value("Boarding Attendance", doc.name, "creation", add_days(now_datetime(), -3))
		frappe.set_user(user)
		try:
			with self.assertRaises(frappe.PermissionError):
				frappe.get_doc("Boarding Attendance", doc.name).cancel()
		finally:
			frappe.set_user("Administrator")
		frappe.get_doc("Boarding Attendance", doc.name).cancel()  # Administrator is not held to the window
		self.assertEqual(frappe.db.get_value("Boarding Attendance", doc.name, "docstatus"), 2)


class TestStrength(FrappeTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		make_unit(HOSTEL_B, "THB")
		for n in range(1, 151):
			make_student(HOSTEL_B, n)

	def test_strength_limit_and_dated_raise(self):
		with self.assertRaises(frappe.ValidationError) as ctx:
			make_student(HOSTEL_B, 151)
		self.assertIn("Sanctioned strength reached", str(ctx.exception))
		profile = frappe.get_doc("Trust Unit Profile", HOSTEL_B)
		profile.append("sanctions", {"effective_from": "2026-10-01", "sanctioned_strength": 160, "grant_rate": 850})
		profile.save()
		make_student(HOSTEL_B, 152, enrollment_date="2026-10-05")  # after the raise: accepted
		with self.assertRaises(frappe.ValidationError):
			make_student(HOSTEL_B, 153, enrollment_date="2026-09-15")  # before the raise: refused

	def test_duplicates_refused(self):
		enr = frappe.get_all("Student Enrollment", filters={"unit": HOSTEL_B}, fields=["student", "academic_year"], limit=1)[0]
		dup_year = frappe.get_doc(
			{
				"doctype": "Student Enrollment", "student": enr.student, "academic_year": enr.academic_year, "unit": HOSTEL_B,
				"school": "Zohra English Medium", "trust_class": "Class 8", "register_sl_no": 900,
			}
		)
		with self.assertRaises(frappe.ValidationError):
			dup_year.insert()
		with self.assertRaises(frappe.ValidationError):
			make_student(HOSTEL_B, 154, register=5)  # register number 5 is taken
