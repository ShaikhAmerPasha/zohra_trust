from frappe.model.document import Document

from zohra_trust.utils.voucher import cancel_journal_entry, make_journal_entry, validate_voucher


class CashBankVoucher(Document):
	def _validate_links(self):
		# The Amend button copies the cancelled document's journal entry; submit makes a new one. Link checks run before
		# before_insert, so the stale link has to go first.
		if self.amended_from and self.is_new():
			self.journal_entry = None
		super()._validate_links()

	def validate(self):
		validate_voucher(self)

	def on_submit(self):
		make_journal_entry(self)

	def before_cancel(self):
		self.ignore_linked_doctypes = ("Journal Entry",)

	def on_cancel(self):
		cancel_journal_entry(self)
