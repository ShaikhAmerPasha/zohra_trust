import frappe
from frappe import _
from frappe.utils import flt

from zohra_trust.utils.dates import month_bounds
from zohra_trust.utils.period import assert_period_open

ITEM, HEAD = "Item", "Expense Head"


def set_period(doc):
	doc.period_start, doc.period_end, _days = month_bounds(doc.month, doc.year)
	doc.warehouse = frappe.db.get_value("Trust Unit Profile", doc.company, "ration_warehouse")
	if not doc.warehouse:
		frappe.throw(_("Set the Ration Warehouse in the Trust Unit Profile of {0}").format(doc.company))


def find_previous(doc):
	"""Latest submitted statement of the company ending before this one starts, whatever the month."""
	return frappe.db.get_value(
		"Food Expenditure Statement",
		{"company": doc.company, "docstatus": 1, "period_end": ["<", doc.period_start], "name": ["!=", doc.name or ""]},
		"name",
		order_by="period_end desc",
	)


def fill(doc):
	set_period(doc)
	doc.previous_statement = None if doc.is_opening else find_previous(doc)
	old = previous_balances(doc.previous_statement) if doc.previous_statement else {}
	typed = {(l.line_type, l.item_code or l.account): l for l in doc.lines} if doc.is_opening else {}
	purchased, consumed, debits = month_purchases(doc), month_consumption(doc), month_debits(doc)

	doc.lines = []
	items = frappe.get_all(
		"Item", filters={"custom_on_food_statement": 1, "disabled": 0}, fields=["name", "stock_uom"],
		order_by="custom_statement_order asc, name asc",
	)
	for item in items:
		line = {"line_type": ITEM, "item_code": item.name, "uom": item.stock_uom}
		if doc.is_opening:
			prev = typed.get((ITEM, item.name))
			line.update(old_qty=prev.old_qty if prev else 0, old_amount=prev.old_amount if prev else 0)
		else:
			line.update(zip(("old_qty", "old_amount"), old.get(item.name, (0, 0))))
		qty, amount = purchased.get(item.name, (0, 0))
		line.update(purchased_qty=qty, purchased_amount=amount, consumed_qty=consumed.get(item.name, 0))
		doc.append("lines", line)
	accounts = frappe.get_all(
		"Account", filters={"company": doc.company, "custom_on_food_statement": 1, "is_group": 0, "disabled": 0},
		fields=["name"], order_by="custom_statement_order asc, name asc",
	)
	for account in accounts:
		doc.append("lines", {"line_type": HEAD, "account": account.name, "purchased_amount": debits.get(account.name, 0)})
	calculate(doc)


def previous_balances(previous):
	rows = frappe.get_all(
		"Food Expenditure Statement Line", filters={"parent": previous, "line_type": ITEM},
		fields=["item_code", "balance_qty", "balance_amount"],
	)
	return {r.item_code: (r.balance_qty, r.balance_amount) for r in rows}


def month_purchases(doc):
	rows = frappe.db.sql(
		"""select pii.item_code, sum(pii.stock_qty), sum(pii.base_net_amount)
		from `tabPurchase Invoice Item` pii join `tabPurchase Invoice` pi on pi.name = pii.parent
		where pi.docstatus = 1 and pi.company = %s and pi.posting_date between %s and %s
		group by pii.item_code""",
		(doc.company, doc.period_start, doc.period_end),
	)
	return {code: (flt(qty), flt(amount)) for code, qty, amount in rows}


def month_consumption(doc):
	rows = frappe.db.sql(
		"""select mci.item_code, sum(mci.qty)
		from `tabMaterial Consumption Item` mci join `tabMaterial Consumption` mc on mc.name = mci.parent
		where mc.docstatus = 1 and mc.company = %s and mc.posting_date between %s and %s
		group by mci.item_code""",
		(doc.company, doc.period_start, doc.period_end),
	)
	return {code: flt(qty) for code, qty in rows}


def month_debits(doc):
	rows = frappe.db.sql(
		"""select account, sum(debit - credit) from `tabGL Entry`
		where company = %s and is_cancelled = 0 and posting_date between %s and %s group by account""",
		(doc.company, doc.period_start, doc.period_end),
	)
	return {account: flt(amount, 2) for account, amount in rows}


def calculate(doc):
	"""Derive columns 4 and 7 to 14 of every line, then the totals."""
	for line in doc.lines:
		if line.line_type == HEAD:
			amount = flt(line.purchased_amount, 2)
			line.total_amount = line.expenditure_amount = amount
			line.balance_amount = 0
			continue
		if doc.is_opening and not flt(line.old_amount) and flt(line.old_rate):
			line.old_amount = flt(flt(line.old_qty) * flt(line.old_rate), 2)
		line.old_rate = flt(line.old_amount / line.old_qty, 2) if flt(line.old_qty) else 0
		line.purchased_rate = flt(line.purchased_amount / line.purchased_qty, 2) if flt(line.purchased_qty) else 0
		line.total_qty = flt(line.old_qty) + flt(line.purchased_qty)
		line.total_amount = flt(line.old_amount) + flt(line.purchased_amount)
		consumed = flt(line.consumed_qty)
		if consumed == flt(line.total_qty):
			expenditure = line.total_amount
		elif flt(line.purchased_qty) > 0:
			expenditure = consumed * flt(line.purchased_amount) / flt(line.purchased_qty)
		else:
			expenditure = consumed * (flt(line.old_amount) / flt(line.old_qty) if flt(line.old_qty) else 0)
		line.expenditure_amount = flt(expenditure, 2)
		line.balance_qty = flt(line.total_qty) - consumed
		line.balance_amount = flt(line.total_amount - line.expenditure_amount, 2)
	doc.total_opening = sum(flt(l.old_amount) for l in doc.lines)
	doc.total_purchase = sum(flt(l.purchased_amount) for l in doc.lines)
	doc.total_available = doc.total_opening + doc.total_purchase
	doc.total_expenditure = sum(flt(l.expenditure_amount) for l in doc.lines)
	doc.total_closing = sum(flt(l.balance_amount) for l in doc.lines)


def validate_statement(doc):
	set_period(doc)
	assert_period_open(doc.company, doc.period_start, doc.doctype)
	assert_period_open(doc.company, doc.period_end, doc.doctype)
	doc.previous_statement = None if doc.is_opening else find_previous(doc)
	calculate(doc)


def before_submit(doc):
	if not doc.is_opening and not doc.previous_statement:
		frappe.throw(_("No earlier submitted statement found. Tick Is Opening if this is the first statement"))
	from erpnext.stock.utils import get_stock_balance

	for line in doc.lines:
		if line.line_type != ITEM:
			continue
		stock = flt(get_stock_balance(line.item_code, doc.warehouse, doc.period_end))
		if flt(line.balance_qty) != stock:
			frappe.msgprint(
				_("{0}: statement balance {1} differs from stock {2} at period end").format(line.item_code, line.balance_qty, stock),
				indicator="orange", alert=True,
			)
