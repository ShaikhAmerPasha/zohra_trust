import frappe
from frappe import _
from frappe.model.document import Document

from zohra_trust.utils.consumption import cancel_stock_entry, make_stock_entry, validate_consumption


class MaterialConsumption(Document):
	def validate(self):
		validate_consumption(self)

	def on_submit(self):
		make_stock_entry(self)

	def before_cancel(self):
		self.ignore_linked_doctypes = ("Stock Entry",)

	def on_cancel(self):
		cancel_stock_entry(self)
