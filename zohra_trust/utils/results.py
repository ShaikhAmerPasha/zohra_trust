import frappe
from frappe import _
from frappe.utils import cint

from zohra_trust.utils.period import assert_period_open

ENROLLMENT_FIELDS = ["name", "student", "student_name", "register_sl_no", "trust_class", "school", "unit", "academic_year", "status"]


def is_final(doc):
	return cint(frappe.db.get_value("Trust Exam", doc.exam, "is_final"))


def guardian_name(student):
	"""First guardian's name when the child has a guardian, else blank."""
	if not frappe.db.get_value("Trust Student", student, "has_guardian"):
		return ""
	return frappe.db.get_value(
		"Student Guardian", {"parent": student, "parenttype": "Trust Student"}, "guardian_name", order_by="idx asc"
	) or ""


def max_marks(trust_class, exam):
	return frappe.db.get_value("Class Exam Marks", {"parent": trust_class, "parenttype": "Trust Class", "exam": exam}, "max_marks")


def fill_rows(doc):
	"""Replace rows with one per Enrolled student of the company and academic year."""
	if not (doc.company and doc.academic_year and doc.exam):
		frappe.throw(_("Set Company, Academic Year and Exam first"))
	students = frappe.get_all(
		"Student Enrollment",
		filters={"unit": doc.company, "academic_year": doc.academic_year, "status": "Enrolled"},
		fields=ENROLLMENT_FIELDS,
		order_by="register_sl_no asc",
	)
	missing = sorted({s.trust_class for s in students if max_marks(s.trust_class, doc.exam) is None})
	if missing:
		frappe.throw(_("Set maximum marks for {0} in {1}").format(doc.exam, ", ".join(missing)))
	doc.rows = []
	for s in students:
		doc.append("rows", {"enrollment": s.name})
	set_row_details(doc)


def set_row_details(doc):
	seen = set()
	for row in doc.rows:
		if row.enrollment in seen:
			frappe.throw(_("Row {0}: {1} appears twice").format(row.idx, row.enrollment))
		seen.add(row.enrollment)
		enr = frappe.db.get_value("Student Enrollment", row.enrollment, ENROLLMENT_FIELDS, as_dict=True)
		if enr.unit != doc.company or enr.academic_year != doc.academic_year:
			frappe.throw(_("Row {0}: {1} does not belong to this unit and academic year").format(row.idx, row.enrollment))
		row.register_sl_no, row.student_name, row.guardian_name = enr.register_sl_no, enr.student_name, guardian_name(enr.student)
		row.trust_class, row.school = enr.trust_class, enr.school
		row.max_marks = max_marks(enr.trust_class, doc.exam)
		if row.max_marks is None:
			frappe.throw(_("Row {0}: no maximum marks for {1} in {2}").format(row.idx, enr.trust_class, doc.exam))


def default_action(row):
	"""Pass moves up (or completes the last class); Fail repeats in every class; Absent is left to the user."""
	if row.result == "Pass":
		return "Promote" if frappe.db.get_value("Trust Class", row.trust_class, "next_class") else "Complete"
	if row.result == "Fail":
		return "Repeat"
	return None


def validate_results(doc):
	assert_period_open(doc.company, doc.exam_date or frappe.utils.today(), doc.doctype)
	set_row_details(doc)
	final = is_final(doc)
	for row in doc.rows:
		if row.marks_obtained is not None and not 0 <= row.marks_obtained <= row.max_marks:
			frappe.throw(_("Row {0}: Marks Obtained must be between 0 and {1}").format(row.idx, row.max_marks))
		if final and row.result and not row.promotion_action:
			row.promotion_action = default_action(row)
	doc.appeared = sum(1 for r in doc.rows if r.result in ("Pass", "Fail"))
	doc.passed = sum(1 for r in doc.rows if r.result == "Pass")
	doc.failed = sum(1 for r in doc.rows if r.result == "Fail")


def before_submit(doc):
	final = is_final(doc)
	for row in doc.rows:
		who = _("Row {0} ({1})").format(row.idx, row.student_name)
		if not row.result:
			frappe.throw(_("{0}: Result is required").format(who))
		if not final:
			continue
		if not row.promotion_action:
			frappe.throw(_("{0}: choose Promotion Action").format(who))
		if row.promotion_action == "Complete" and not row.leaving_destination:
			frappe.throw(_("{0}: Leaving Destination is required to complete").format(who))
		if row.promotion_action == "Promote" and not frappe.db.get_value("Trust Class", row.trust_class, "next_class"):
			frappe.throw(_("{0}: {1} has no next class to promote to").format(who, row.trust_class))


def next_academic_year(academic_year):
	end = frappe.db.get_value("Trust Academic Year", academic_year, "end_date")
	nxt = frappe.db.get_value("Trust Academic Year", {"start_date": [">", end]}, "name", order_by="start_date asc")
	if not nxt:
		frappe.throw(_("Create the Academic Year that starts after {0} first").format(academic_year))
	return nxt


def next_register_no(unit, academic_year):
	last = frappe.db.sql(
		"select max(register_sl_no) from `tabStudent Enrollment` where unit = %s and academic_year = %s", (unit, academic_year)
	)[0][0]
	return (last or 0) + 1


def promote(doc):
	"""From a submitted Final sheet: next year's enrollments, or close the student. All or nothing."""
	if not is_final(doc):
		frappe.throw(_("Only the Final exam promotes students"))
	if doc.docstatus != 1:
		frappe.throw(_("Submit the Result Sheet first"))
	if doc.promotion_done:
		frappe.throw(_("Promotion is already done for this sheet"))
	year_end = frappe.db.get_value("Trust Academic Year", doc.academic_year, "end_date")
	next_year = next_academic_year(doc.academic_year)
	next_start = frappe.db.get_value("Trust Academic Year", next_year, "start_date")
	frappe.db.savepoint("promote")
	try:
		for row in doc.rows:
			enr = frappe.db.get_value("Student Enrollment", row.enrollment, ["student", "school", "trust_class"], as_dict=True)
			action = row.promotion_action
			if action in ("Promote", "Repeat"):
				new_class = frappe.db.get_value("Trust Class", enr.trust_class, "next_class") if action == "Promote" else enr.trust_class
				entry = frappe.get_doc(
					{
						"doctype": "Student Enrollment",
						"student": enr.student,
						"academic_year": next_year,
						"unit": doc.company,
						"school": enr.school,
						"trust_class": new_class,
						"register_sl_no": next_register_no(doc.company, next_year),
						"enrollment_date": next_start,
						"status": "Planned",
						"is_repeating": 1 if action == "Repeat" else 0,
						"previous_enrollment": row.enrollment,
					}
				)
				entry.flags.ignore_permissions = True
				entry.insert()
			else:
				close_student(doc, row, enr.student, year_end, "Passed Out" if action == "Complete" else "Left")
		doc.db_set("promotion_done", 1)
	except Exception:
		frappe.db.rollback(save_point="promote")
		raise


def close_student(doc, row, student, year_end, status):
	record = frappe.get_doc("Trust Student", student)
	record.status = status
	record.leaving_date = year_end
	record.leaving_destination = row.leaving_destination
	record.leaving_reason = _("Result Sheet {0}").format(doc.name)
	record.flags.ignore_permissions = True
	record.save()
	frappe.db.set_value("Student Enrollment", row.enrollment, "status", "Completed" if status == "Passed Out" else "Left")
