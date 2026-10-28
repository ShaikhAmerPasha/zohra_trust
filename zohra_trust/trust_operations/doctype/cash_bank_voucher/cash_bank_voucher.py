from frappe.model.document import Document

from zohra_trust.utils.voucher import cancel_journal_entry, make_journal_entry, validate_voucher


class CashBankVoucher(Document):
	def validate(self):
		validate_voucher(self)

	def on_submit(self):
		make_journal_entry(self)

	def before_cancel(self):
		self.ignore_linked_doctypes = ("Journal Entry",)

	def on_cancel(self):
		cancel_journal_entry(self)
