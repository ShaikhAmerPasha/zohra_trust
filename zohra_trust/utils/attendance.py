import frappe
from frappe import _
from frappe.utils import cint, flt, getdate

from zohra_trust.utils.dates import get_academic_year, month_bounds
from zohra_trust.utils.period import assert_period_open
from zohra_trust.utils.sanction import get_unit_sanction

STUDENT_FIELDS = ["name", "register_sl_no", "student_name", "trust_class", "school", "enrollment_date"]


def set_period(doc):
	doc.period_start, doc.period_end, doc.calendar_days = month_bounds(doc.month, doc.year)
	doc.academic_year = get_academic_year(doc.period_start)


def set_sanction(doc):
	sanction = get_unit_sanction(doc.company, doc.period_end)
	if not sanction:
		frappe.throw(_("No sanctioned strength is set for {0} on {1}").format(doc.company, doc.period_end))
	doc.sanctioned_strength = sanction.strength
	doc.grant_rate = sanction.rate
	doc.grant_rule = sanction.rule


def working_days_by_school(doc):
	days = {}
	for row in doc.school_days:
		if row.school in days:
			frappe.throw(_("School {0} appears twice in School Working Days").format(row.school))
		days[row.school] = cint(row.working_days)
	return days


def grant_for(doc, hostel_days):
	rate = flt(doc.grant_rate)
	if doc.grant_rule == "Pro-rata by hostel days":
		return flt(rate * hostel_days / doc.calendar_days, 2)
	if doc.grant_rule == "Per day":
		return flt(rate * hostel_days, 2)
	return rate  # Full month per student


def fill_rows(doc):
	"""Replace rows with one per Enrolled student of the company and academic year."""
	if not (doc.company and doc.month and doc.year):
		frappe.throw(_("Set Company, Month and Year first"))
	set_period(doc)
	set_sanction(doc)
	days = working_days_by_school(doc)
	students = frappe.get_all(
		"Student Enrollment",
		filters={"unit": doc.company, "academic_year": doc.academic_year, "status": "Enrolled"},
		fields=STUDENT_FIELDS,
		order_by="register_sl_no asc",
	)
	students = [s for s in students if not s.enrollment_date or getdate(s.enrollment_date) <= doc.period_end]
	missing = sorted({s.school for s in students if s.school not in days})
	if missing:
		frappe.throw(_("Add working days for: {0}").format(", ".join(missing)))
	doc.rows = []
	for s in students:
		hostel_days = doc.calendar_days
		if s.enrollment_date and getdate(s.enrollment_date) > doc.period_start:
			hostel_days -= (getdate(s.enrollment_date) - doc.period_start).days
		doc.append(
			"rows",
			{
				"enrollment": s.name,
				"school_days_present": days[s.school],
				"hostel_days": hostel_days,
			},
		)
	validate_attendance(doc)


def validate_attendance(doc):
	set_period(doc)
	set_sanction(doc)
	assert_period_open(doc.company, doc.period_start, doc.doctype)
	assert_period_open(doc.company, doc.period_end, doc.doctype)
	days = working_days_by_school(doc)
	seen = set()
	for row in doc.rows:
		if row.enrollment in seen:
			frappe.throw(_("Row {0}: {1} appears twice").format(row.idx, row.enrollment))
		seen.add(row.enrollment)
		enr = frappe.db.get_value("Student Enrollment", row.enrollment, STUDENT_FIELDS + ["unit", "academic_year"], as_dict=True)
		if enr.unit != doc.company or enr.academic_year != doc.academic_year:
			frappe.throw(_("Row {0}: {1} does not belong to this unit and academic year").format(row.idx, row.enrollment))
		if enr.school not in days:
			frappe.throw(_("Row {0}: add working days for {1}").format(row.idx, enr.school))
		row.register_sl_no, row.student_name = enr.register_sl_no, enr.student_name
		row.trust_class, row.school = enr.trust_class, enr.school
		row.school_working_days = days[enr.school]
		if row.school_days_present is None:
			row.school_days_present = row.school_working_days
		if row.hostel_days is None:
			row.hostel_days = doc.calendar_days
		if not 0 <= cint(row.hostel_days) <= doc.calendar_days:
			frappe.throw(_("Row {0}: Hostel Days must be between 0 and {1}").format(row.idx, doc.calendar_days))
		if not 0 <= cint(row.school_days_present) <= row.school_working_days:
			frappe.throw(_("Row {0}: School Days Present must be between 0 and {1}").format(row.idx, row.school_working_days))
		row.grant_amount = grant_for(doc, cint(row.hostel_days))
	doc.students_on_roll = len(doc.rows)
	if doc.students_on_roll > cint(doc.sanctioned_strength):
		frappe.throw(_("{0} students exceed the sanctioned strength of {1}").format(doc.students_on_roll, doc.sanctioned_strength))
	doc.total_hostel_days = sum(cint(r.hostel_days) for r in doc.rows)
	doc.total_school_days_present = sum(cint(r.school_days_present) for r in doc.rows)
	doc.total_grant = sum(flt(r.grant_amount) for r in doc.rows)
