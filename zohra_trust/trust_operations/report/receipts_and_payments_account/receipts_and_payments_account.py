import frappe
from frappe import _
from frappe.utils import flt, getdate

# An empty cell is None: Frappe prints a missing key as 0.00 but null as blank.
# Rows of the filed report come first, in its order; any other head follows alphabetically.
RECEIPT_ORDER = ["Loan from Zohra trust", "Bank interest", "Govt. grant received"]
PAYMENT_ORDER = ["Food", "Fuel", "Detergent", "Salaries", "Education", "Miscellaneous", "Transfer to Zohra trust"]


def execute(filters=None):
	filters = frappe._dict(filters or {})
	if not (filters.company and filters.from_date and filters.to_date):
		frappe.throw(_("Company, From Date and To Date are required"))
	if getdate(filters.from_date) > getdate(filters.to_date):
		frappe.throw(_("From Date cannot be after To Date"))
	return get_columns(), get_data(filters)


def get_columns():
	return [
		{"fieldname": "particulars", "label": _("Particulars"), "fieldtype": "Data", "width": 280},
		{"fieldname": "receipts", "label": _("Receipts"), "fieldtype": "Currency", "width": 150},
		{"fieldname": "payments", "label": _("Payments"), "fieldtype": "Currency", "width": 150},
	]


def money_accounts(company):
	rows = frappe.get_all(
		"Account", filters={"company": company, "account_type": ["in", ["Cash", "Bank"]], "is_group": 0}, fields=["name", "account_type"]
	)
	return {r.name: r.account_type for r in rows}


def balance(company, accounts, before=None, upto=None):
	"""Net debit of the accounts before a date, or up to and including a date."""
	if not accounts:
		return 0
	condition, value = ("posting_date < %s", before) if before else ("posting_date <= %s", upto)
	return flt(
		frappe.db.sql(
			f"""select coalesce(sum(debit - credit), 0) from `tabGL Entry`
			where company = %s and is_cancelled = 0 and account in %s and {condition}""",
			(company, tuple(accounts), value),
		)[0][0],
		2,
	)


def movements(company, accounts, from_date, to_date):
	"""Net money in (+) or out (-) of each counter-account, per voucher, as (account, amount)."""
	entries = frappe.db.sql(
		"""select voucher_type, voucher_no, account, debit, credit from `tabGL Entry`
		where company = %s and is_cancelled = 0 and posting_date between %s and %s
		and voucher_no in (select distinct voucher_no from `tabGL Entry`
			where company = %s and is_cancelled = 0 and posting_date between %s and %s and account in %s)""",
		(company, from_date, to_date, company, from_date, to_date, tuple(accounts) or ("",)),
		as_dict=True,
	)
	per_voucher = {}
	for e in entries:
		if e.account in accounts:
			continue
		key = (e.voucher_type, e.voucher_no, e.account)
		per_voucher[key] = per_voucher.get(key, 0) + flt(e.credit) - flt(e.debit)
	return [(key[2], amount) for key, amount in per_voucher.items() if flt(amount, 2)]


def head_for(account, money_in, cache):
	if account not in cache:
		cache[account] = frappe.db.get_value("Account", account, ["account_name", "custom_rp_head_in", "custom_rp_head_out"], as_dict=True)
	row = cache[account]
	return (row.custom_rp_head_in if money_in else row.custom_rp_head_out) or row.account_name


def ordered(totals, order):
	known = [h for h in order if h in totals]
	return known + sorted(h for h in totals if h not in order)


def get_data(filters):
	company, from_date, to_date = filters.company, getdate(filters.from_date), getdate(filters.to_date)
	accounts = money_accounts(company)
	cash = [a for a, t in accounts.items() if t == "Cash"]
	bank = [a for a, t in accounts.items() if t == "Bank"]
	receipts, payments, cache = {}, {}, {}
	for account, amount in movements(company, accounts, from_date, to_date):
		if amount > 0:
			head = head_for(account, True, cache)
			receipts[head] = receipts.get(head, 0) + amount
		else:
			head = head_for(account, False, cache)
			payments[head] = payments.get(head, 0) - amount

	opening = {"Cash": balance(company, cash, before=from_date), "Bank": balance(company, bank, before=from_date)}
	closing = {"Cash": balance(company, cash, upto=to_date), "Bank": balance(company, bank, upto=to_date)}
	data = [{"particulars": _("Opening balance ({0})").format(_(k)), "receipts": opening[k], "payments": None} for k in ("Cash", "Bank")]
	data += [{"particulars": _(h), "receipts": flt(receipts[h], 2), "payments": None} for h in ordered(receipts, RECEIPT_ORDER)]
	data += [{"particulars": _(h), "receipts": None, "payments": flt(payments[h], 2)} for h in ordered(payments, PAYMENT_ORDER)]
	data += [{"particulars": _("Closing balance ({0})").format(_(k)), "receipts": None, "payments": closing[k]} for k in ("Cash", "Bank")]
	data.append(
		{
			"particulars": _("Total"),
			"receipts": flt(sum(opening.values()) + sum(receipts.values()), 2),
			"payments": flt(sum(payments.values()) + sum(closing.values()), 2),
			"bold": 1,
		}
	)
	return data
