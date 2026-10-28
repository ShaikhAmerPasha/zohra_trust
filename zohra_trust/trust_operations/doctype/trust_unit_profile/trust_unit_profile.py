import frappe
from frappe import _
from frappe.model.document import Document


class TrustUnitProfile(Document):
	def validate(self):
		for row in self.sanctions:
			if row.effective_to and row.effective_to < row.effective_from:
				frappe.throw(_("Row {0}: Effective To is before Effective From").format(row.idx))
			if (row.sanctioned_strength or 0) <= 0:
				frappe.throw(_("Row {0}: Sanctioned Strength must be above zero").format(row.idx))
