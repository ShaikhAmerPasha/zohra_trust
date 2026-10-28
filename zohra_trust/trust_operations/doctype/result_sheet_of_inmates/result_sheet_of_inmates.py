import frappe
from frappe import _
from frappe.model.document import Document

from zohra_trust.utils.results import before_submit, fill_rows, promote, validate_results


class ResultSheetofInmates(Document):
	def autoname(self):
		if not (self.company and self.academic_year and self.exam):
			frappe.throw(_("Company, Academic Year and Exam are required"))
		abbr = frappe.get_cached_value("Company", self.company, "abbr")
		name = f"RSI-{abbr}-{self.academic_year}-{self.exam}"
		if frappe.db.exists("Result Sheet of Inmates", name):
			frappe.throw(_("Result Sheet {0} already exists").format(name), frappe.DuplicateEntryError)
		self.name = name

	def validate(self):
		validate_results(self)

	def before_submit(self):
		before_submit(self)

	def before_cancel(self):
		if self.promotion_done:
			frappe.throw(_("Promotion is already done for this sheet. It cannot be cancelled"))

	@frappe.whitelist()
	def fill_rows(self):
		fill_rows(self)

	@frappe.whitelist()
	def promote(self):
		promote(self)
