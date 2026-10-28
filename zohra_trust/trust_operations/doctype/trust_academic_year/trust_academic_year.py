import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import getdate


class TrustAcademicYear(Document):
	def validate(self):
		if getdate(self.end_date) <= getdate(self.start_date):
			frappe.throw(_("End Date must be after Start Date"))
		clash = frappe.db.sql(
			"""select name from `tabTrust Academic Year`
			where name != %s and start_date <= %s and end_date >= %s limit 1""",
			(self.name or "", self.end_date, self.start_date),
		)
		if clash:
			frappe.throw(_("Academic Year overlaps with {0}").format(clash[0][0]))
