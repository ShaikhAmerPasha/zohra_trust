import frappe
from frappe import _
from frappe.model.document import Document

from zohra_trust.utils.attendance import fill_rows, validate_attendance
from zohra_trust.utils.dates import month_number


class BoardingAttendance(Document):
	def autoname(self):
		if not (self.company and self.month and self.year):
			frappe.throw(_("Company, Month and Year are required"))
		abbr = frappe.get_cached_value("Company", self.company, "abbr")
		name = f"BAT-{abbr}-{int(self.year)}-{month_number(self.month):02d}"
		if frappe.db.exists("Boarding Attendance", name):
			frappe.throw(_("Boarding Attendance {0} already exists").format(name), frappe.DuplicateEntryError)
		self.name = name

	def validate(self):
		validate_attendance(self)

	@frappe.whitelist()
	def fill_rows(self):
		fill_rows(self)
