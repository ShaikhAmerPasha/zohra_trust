import frappe
from frappe.tests.utils import FrappeTestCase

from zohra_trust.tests.helpers import make_class, make_masters, make_student, make_unit

COMPANY, ABBR = "Test Hostel J", "THJ"


def make_classes_1_to_7():
	make_masters()
	for n in range(7, 0, -1):
		make_class(f"Class {n}", n, f"Class {n + 1}", 250)


def sheet(company, exam="Final", year="2026-27"):
	doc = frappe.get_doc({"doctype": "Result Sheet of Inmates", "company": company, "academic_year": year, "exam": exam, "exam_date": "2027-03-10"})
	doc.fill_rows()
	return doc


def mark(doc, results):
	"""results: {student_name: (marks, result, action, destination)}"""
	for row in doc.rows:
		marks, result, action, destination = results[row.student_name]
		row.marks_obtained, row.result = marks, result
		if action:
			row.promotion_action = action
		if destination:
			row.leaving_destination = destination


class TestResultSheet(FrappeTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		make_classes_1_to_7()
		make_unit(COMPANY, ABBR)
		# one girl in each of classes 1 to 10, plus a repeater in class 3, a failed last-class girl and a leaver
		cls.girls = {}
		spec = [(f"Class {n}", n) for n in range(1, 11)] + [("Class 3", 11), ("Class 10", 12), ("Class 4", 13)]
		for cls_name, n in spec:
			enr = make_student(COMPANY, n, trust_class=cls_name, guardian="Father " + str(n) if n == 1 else None)
			cls.girls[frappe.db.get_value("Student Enrollment", enr.name, "student_name")] = enr

	def setUp(self):
		frappe.db.savepoint("test_case")  # each test starts from the same roster

	def tearDown(self):
		frappe.set_user("Administrator")
		frappe.db.rollback(save_point="test_case")

	def name(self, n):
		return f"Girl {COMPANY[-1]}{n}"

	def test_fill_rows(self):
		doc = sheet(COMPANY)
		self.assertEqual(len(doc.rows), 13)
		self.assertEqual([r.register_sl_no for r in doc.rows], list(range(1, 14)))
		by_name = {r.student_name: r for r in doc.rows}
		self.assertEqual(by_name[self.name(1)].guardian_name, "Father 1")
		self.assertEqual(by_name[self.name(2)].guardian_name, "")
		self.assertEqual((by_name[self.name(9)].max_marks, by_name[self.name(10)].max_marks, by_name[self.name(1)].max_marks), (480, 625, 250))
		self.assertEqual(doc.name if doc.name else None, None)  # named on insert

	def test_marks_result_and_totals(self):
		doc = sheet(COMPANY, exam="Mid-term")
		for row in doc.rows:
			row.marks_obtained, row.result = 100, "Pass"
		doc.rows[0].result = "Fail"
		doc.rows[1].result = "Absent"
		doc.rows[1].marks_obtained = 0
		doc.insert()
		self.assertEqual((doc.appeared, doc.passed, doc.failed), (12, 11, 1))
		self.assertEqual(doc.name, "RSI-THJ-2026-27-Mid-term")
		doc.rows[2].marks_obtained = 999
		with self.assertRaises(frappe.ValidationError):
			doc.save()
		doc.reload()
		doc.rows[3].result = None
		doc.save()
		with self.assertRaises(frappe.ValidationError):  # result is required on submit
			doc.submit()

	def test_default_actions(self):
		doc = sheet(COMPANY)
		results = {self.name(n): (100, "Pass", None, None) for n in range(1, 14)}
		results[self.name(11)] = (50, "Fail", None, None)
		results[self.name(12)] = (50, "Fail", None, None)
		results[self.name(13)] = (0, "Absent", None, None)
		mark(doc, results)
		doc.validate()
		actions = {r.student_name: r.promotion_action for r in doc.rows}
		self.assertEqual(actions[self.name(1)], "Promote")
		self.assertEqual(actions[self.name(9)], "Promote")
		self.assertEqual(actions[self.name(10)], "Complete")
		self.assertEqual(actions[self.name(11)], "Repeat")
		self.assertEqual(actions[self.name(12)], "Repeat")  # a fail repeats even in the last class
		self.assertFalse(actions[self.name(13)])  # absent is left to the user

	def test_final_submit_needs_actions_and_destination(self):
		doc = sheet(COMPANY, year="2026-27")
		results = {self.name(n): (100, "Pass", None, None) for n in range(1, 14)}
		results[self.name(13)] = (0, "Absent", None, None)
		mark(doc, results)
		doc.insert()
		with self.assertRaises(frappe.ValidationError):  # absent girl has no action, class 10 has no destination
			doc.submit()

	def test_promotion(self):
		"""Class 1 to 9 pass move up, a fail repeats, class 10 pass completes, Leave closes."""
		doc = sheet(COMPANY)
		results = {self.name(n): (100, "Pass", None, None) for n in range(1, 14)}
		results[self.name(10)] = (500, "Pass", None, "Working women hostel")
		results[self.name(11)] = (50, "Fail", None, None)
		results[self.name(12)] = (50, "Fail", None, None)
		results[self.name(13)] = (100, "Pass", "Leave", "Other")
		mark(doc, results)
		doc.insert()
		doc.submit()
		before = {n: frappe.get_doc("Student Enrollment", e.name).as_dict() for n, e in self.girls.items()}
		doc.promote()
		self.assertEqual(frappe.db.get_value("Result Sheet of Inmates", doc.name, "promotion_done"), 1)

		def next_year(n):
			student = self.girls[self.name(n)].student
			return frappe.get_doc("Student Enrollment", f"ENR-2027-28-{student}")

		for n in range(1, 10):  # classes 1 to 9 move up
			new = next_year(n)
			self.assertEqual((new.trust_class, new.status, new.is_repeating), (f"Class {n + 1}", "Planned", 0), n)
			self.assertEqual(new.previous_enrollment, self.girls[self.name(n)].name)
		repeat = next_year(11)
		self.assertEqual((repeat.trust_class, repeat.is_repeating, repeat.status), ("Class 3", 1, "Planned"))
		self.assertEqual(next_year(12).trust_class, "Class 10")  # failed in the last class: repeats
		self.assertEqual(sorted(e.register_sl_no for e in [next_year(n) for n in (1, 2, 3, 4, 5, 6, 7, 8, 9, 11, 12)]), list(range(1, 12)))
		# class 10 pass completes
		done = frappe.get_doc("Trust Student", self.girls[self.name(10)].student)
		self.assertEqual((done.status, str(done.leaving_date), done.leaving_destination), ("Passed Out", "2027-03-31", "Working women hostel"))
		self.assertEqual(frappe.db.get_value("Student Enrollment", self.girls[self.name(10)].name, "status"), "Completed")
		self.assertFalse(frappe.db.exists("Student Enrollment", f"ENR-2027-28-{done.name}"))
		# Leave closes
		left = frappe.get_doc("Trust Student", self.girls[self.name(13)].student)
		self.assertEqual((left.status, left.leaving_destination), ("Left", "Other"))
		self.assertEqual(frappe.db.get_value("Student Enrollment", self.girls[self.name(13)].name, "status"), "Left")
		# last year's enrollments are unchanged, except the status of those who completed or left
		for n in (1, 5, 9, 11, 12):
			after = frappe.get_doc("Student Enrollment", self.girls[self.name(n)].name).as_dict()
			for field in ("student", "academic_year", "unit", "school", "trust_class", "register_sl_no", "status", "is_repeating", "modified"):
				self.assertEqual(after[field], before[self.name(n)][field], f"{n} {field}")
		# cannot be done twice or undone
		with self.assertRaises(frappe.ValidationError):
			doc.reload()
			doc.promote()
		with self.assertRaises(frappe.ValidationError):
			doc.cancel()

	def test_only_final_submitted_sheet_promotes(self):
		mid = sheet(COMPANY, exam="Mid-term")
		mark(mid, {self.name(n): (100, "Pass", None, None) for n in range(1, 14)})
		mid.insert()
		mid.submit()
		with self.assertRaises(frappe.ValidationError):
			mid.promote()
		draft = sheet(COMPANY)
		with self.assertRaises(frappe.ValidationError):
			draft.promote()

	def test_data_entry_can_enter_and_submit_a_sheet(self):
		user = "result.entry@example.com"
		if not frappe.db.exists("User", user):
			frappe.get_doc({"doctype": "User", "email": user, "first_name": "RE", "send_welcome_email": 0, "roles": [{"role": "Data Entry"}]}).insert()
		frappe.set_user(user)
		try:
			doc = sheet(COMPANY, exam="Mid-term")
			mark(doc, {self.name(n): (100, "Pass", None, None) for n in range(1, 14)})
			doc.insert()
			doc.submit()
			self.assertEqual(doc.docstatus, 1)
		finally:
			frappe.set_user("Administrator")


class TestPromotionLimit(FrappeTestCase):
	def test_refused_above_strength_and_nothing_is_saved(self):
		company, abbr = "Test Hostel K", "THK"
		make_masters()
		make_unit(company, abbr, strength=3)
		girls = [make_student(company, n, trust_class="Class 8") for n in (1, 2, 3)]
		doc = sheet(company)
		mark(doc, {r.student_name: (200, "Pass", None, None) for r in doc.rows})
		doc.insert()
		doc.submit()
		# a fourth girl already holds a seat next year, so three more do not fit in a strength of 3
		other = make_student(company, 4, status="Left", trust_class="Class 8", enrollment_date="2026-04-01")
		frappe.db.set_value("Student Enrollment", other.name, "status", "Left")
		holder = frappe.get_doc(
			{
				"doctype": "Student Enrollment", "student": other.student, "academic_year": "2027-28", "unit": company, "school": "Zohra English Medium",
				"trust_class": "Class 9", "register_sl_no": 1, "enrollment_date": "2027-04-01", "status": "Planned",
			}
		).insert()
		with self.assertRaises(frappe.ValidationError) as ctx:
			doc.promote()
		self.assertIn("Sanctioned strength reached", str(ctx.exception))
		self.assertEqual(frappe.db.count("Student Enrollment", {"unit": company, "academic_year": "2027-28"}), 1)
		self.assertEqual(frappe.db.get_value("Result Sheet of Inmates", doc.name, "promotion_done"), 0)
		# the user frees a seat first (the holder's enrollment is cancelled), then promotion works
		holder.status = "Left"
		holder.save()
		doc.reload()
		doc.promote()
		self.assertEqual(frappe.db.count("Student Enrollment", {"unit": company, "academic_year": "2027-28", "status": "Planned"}), 3)
		self.assertEqual(len(girls), 3)
