import frappe
from frappe import _
from frappe.model.document import Document

from zohra_trust.utils.consumption import cancel_stock_entry, make_stock_entry, validate_consumption


class MaterialConsumption(Document):
	def _validate_links(self):
		# The Amend button copies the cancelled document's stock entry; submit makes a new one. Link checks run before
		# before_insert, so the stale link has to go first.
		if self.amended_from and self.is_new():
			self.stock_entry = None
		super()._validate_links()

	def validate(self):
		validate_consumption(self)

	def on_submit(self):
		make_stock_entry(self)

	def before_cancel(self):
		self.ignore_linked_doctypes = ("Stock Entry",)

	def on_cancel(self):
		cancel_stock_entry(self)
