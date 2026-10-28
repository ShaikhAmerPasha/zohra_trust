import frappe
from frappe import _
from frappe.model.document import Document


class TrustStudent(Document):
	def validate(self):
		if self.status != "Active" and not self.leaving_date:
			frappe.throw(_("Leaving Date is required when the student is {0}").format(_(self.status)))
		if self.leaving_date and self.admission_date and self.leaving_date < self.admission_date:
			frappe.throw(_("Leaving Date cannot be before Admission Date"))
