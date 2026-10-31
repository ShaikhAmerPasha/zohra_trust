import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import getdate

from zohra_trust.utils.report_pack import default_sections, validate_pages


class ReportPack(Document):
	def validate(self):
		if getdate(self.to_date) < getdate(self.from_date):
			frappe.throw(_("To Date cannot be before From Date"))
		if not self.pages:
			self.fill_sections()
		validate_pages(self)

	@frappe.whitelist()
	def fill_sections(self):
		"""Replace the page list with the standard pages in filing order."""
		self.pages = []
		for section in default_sections():
			self.append("pages", {"section": section, "include": 1})
