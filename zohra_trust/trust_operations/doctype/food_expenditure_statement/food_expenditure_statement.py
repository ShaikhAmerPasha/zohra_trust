import frappe
from frappe import _
from frappe.model.document import Document

from zohra_trust.utils.food_statement import before_submit, fill, validate_statement
from zohra_trust.utils.dates import month_number


class FoodExpenditureStatement(Document):
	def autoname(self):
		if not (self.company and self.month and self.year):
			frappe.throw(_("Company, Month and Year are required"))
		abbr = frappe.get_cached_value("Company", self.company, "abbr")
		name = f"FES-{abbr}-{int(self.year)}-{month_number(self.month):02d}"
		if frappe.db.exists("Food Expenditure Statement", name):
			frappe.throw(_("Food Expenditure Statement {0} already exists").format(name), frappe.DuplicateEntryError)
		self.name = name

	def validate(self):
		validate_statement(self)

	def before_submit(self):
		before_submit(self)

	@frappe.whitelist()
	def fill(self):
		fill(self)
