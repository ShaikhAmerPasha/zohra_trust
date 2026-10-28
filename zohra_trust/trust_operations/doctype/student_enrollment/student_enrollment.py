import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import today

from zohra_trust.utils.sanction import get_unit_sanction

HOLDS_SEAT = ("Planned", "Enrolled")


class StudentEnrollment(Document):
	def autoname(self):
		if not (self.academic_year and self.student):
			frappe.throw(_("Student and Academic Year are required"))
		name = f"ENR-{self.academic_year}-{self.student}"
		if frappe.db.exists("Student Enrollment", name):
			frappe.throw(_("{0} is already enrolled for {1}").format(self.student, self.academic_year))
		self.name = name

	def validate(self):
		self.validate_register_no()
		if self.status in HOLDS_SEAT:
			self.validate_strength()

	def validate_register_no(self):
		clash = frappe.db.get_value(
			"Student Enrollment",
			{"unit": self.unit, "academic_year": self.academic_year, "register_sl_no": self.register_sl_no, "name": ["!=", self.name]},
			"name",
		)
		if clash:
			frappe.throw(_("Register Sl No {0} is already used by {1}").format(self.register_sl_no, clash))

	def validate_strength(self):
		sanction = get_unit_sanction(self.unit, self.enrollment_date or today())
		if not sanction:
			frappe.throw(_("No sanctioned strength is set for {0} on this date").format(self.unit))
		taken = frappe.db.count(
			"Student Enrollment",
			{"unit": self.unit, "academic_year": self.academic_year, "status": ["in", HOLDS_SEAT], "name": ["!=", self.name or ""]},
		)
		if taken + 1 > sanction.strength:
			frappe.throw(
				_("Sanctioned strength reached: {0} students are allowed for {1}").format(sanction.strength, self.unit)
			)
