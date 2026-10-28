import frappe
from frappe import _
from frappe.utils import cint, flt

from zohra_trust.utils.period import assert_period_open

PARTY_ACCOUNT_TYPES = ("Payable", "Receivable")


def money_account(doc):
	"""GL account the money moves through: the company's cash account, or the Bank Account's."""
	if doc.mode == "Bank":
		if not doc.bank_account:
			frappe.throw(_("Bank Account is required when the mode is Bank"))
		account, company = frappe.db.get_value("Bank Account", doc.bank_account, ["account", "company"])
		if company != doc.company:
			frappe.throw(_("Bank Account {0} belongs to {1}").format(doc.bank_account, company))
		if not account:
			frappe.throw(_("Bank Account {0} has no GL account").format(doc.bank_account))
		return account
	account = frappe.get_cached_value("Company", doc.company, "default_cash_account")
	if not account:
		frappe.throw(_("Set the Default Cash Account on Company {0}").format(doc.company))
	return account


def validate_voucher(doc):
	if flt(doc.amount) <= 0:
		frappe.throw(_("Amount must be above zero"))
	assert_period_open(doc.company, doc.posting_date, doc.doctype)
	head = frappe.db.get_value("Account", doc.account_head, ["company", "is_group", "account_type"], as_dict=True)
	if head.company != doc.company:
		frappe.throw(_("Account Head {0} belongs to {1}").format(doc.account_head, head.company))
	if cint(head.is_group) or head.account_type in ("Cash", "Bank"):
		frappe.throw(_("Choose an income, expense or trust account as the Account Head"))
	if head.account_type in PARTY_ACCOUNT_TYPES and not (doc.party_type and doc.party):
		frappe.throw(_("Party Type and Party are required for {0}").format(doc.account_head))
	if doc.mode == "Cash":
		doc.bank_account = None
	money_account(doc)


def make_journal_entry(doc):
	money = money_account(doc)
	cost_center = frappe.get_cached_value("Company", doc.company, "cost_center")
	receipt = doc.voucher_type == "Receipt"
	money_row = {"account": money, "cost_center": cost_center}
	head_row = {"account": doc.account_head, "cost_center": cost_center}
	if doc.party_type and doc.party:
		head_row.update(party_type=doc.party_type, party=doc.party)
	money_row["debit_in_account_currency" if receipt else "credit_in_account_currency"] = doc.amount
	head_row["credit_in_account_currency" if receipt else "debit_in_account_currency"] = doc.amount
	entry = frappe.get_doc(
		{
			"doctype": "Journal Entry",
			"voucher_type": "Cash Entry" if doc.mode == "Cash" else "Journal Entry",
			"company": doc.company,
			"posting_date": doc.posting_date,
			"user_remark": doc.narration,
			"cheque_no": doc.reference_no,
			"cheque_date": doc.posting_date if doc.reference_no else None,
			"custom_cash_bank_voucher": doc.name,
			"accounts": [money_row, head_row],
		}
	)
	entry.flags.ignore_permissions = True
	entry.insert()
	entry.submit()
	doc.db_set("journal_entry", entry.name)


def cancel_journal_entry(doc):
	if not doc.journal_entry:
		return
	entry = frappe.get_doc("Journal Entry", doc.journal_entry)
	if entry.docstatus != 1:
		return
	entry.flags.ignore_permissions = True
	entry.ignore_linked_doctypes = ("Cash Bank Voucher",)
	frappe.flags.cancelling_cash_bank_voucher = True
	try:
		entry.cancel()
	finally:
		frappe.flags.cancelling_cash_bank_voucher = False


def block_direct_journal_cancel(doc, method=None):
	"""A Journal Entry made by a voucher is cancelled only through that voucher."""
	if doc.get("custom_cash_bank_voucher") and not frappe.flags.cancelling_cash_bank_voucher:
		frappe.throw(
			_("This Journal Entry was made by Cash Bank Voucher {0}. Cancel the voucher instead").format(doc.custom_cash_bank_voucher),
			title=_("Cannot Cancel"),
		)
