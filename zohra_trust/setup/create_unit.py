import frappe
from frappe.utils import getdate


def create_unit(
	company,
	abbr,
	unit_type="Hostel",
	sanctioned_strength=150,
	grant_rate=850,
	effective_from="2026-04-01",
	order_reference=None,
	bank_name="Hostel Bank",
):
	"""One-call site setup for a unit. Safe to run again: existing records are kept."""
	create_company(company, abbr)
	warehouse = create_warehouse("Hostel Store", company, abbr)
	create_supplier("Cash purchase")
	create_accounts(company, abbr)
	create_cash_mode(company, abbr)
	create_bank(company, abbr, bank_name)
	create_items(company, abbr, warehouse)
	return create_profile(company, unit_type, warehouse, sanctioned_strength, grant_rate, effective_from, order_reference)


def create_company(company, abbr):
	if frappe.db.exists("Company", company):
		return
	frappe.get_doc(
		{
			"doctype": "Company",
			"company_name": company,
			"abbr": abbr,
			"default_currency": "INR",
			"country": "India",
			"enable_perpetual_inventory": 0,
		}
	).insert()


def create_warehouse(name, company, abbr):
	full_name = f"{name} - {abbr}"
	if not frappe.db.exists("Warehouse", full_name):
		frappe.get_doc(
			{
				"doctype": "Warehouse",
				"warehouse_name": name,
				"company": company,
				"parent_warehouse": frappe.db.get_value("Warehouse", {"company": company, "is_group": 1, "parent_warehouse": ["is", "not set"]}),
			}
		).insert()
	return full_name


def create_supplier(name):
	if not frappe.db.exists("Supplier", name):
		group = frappe.db.get_value("Supplier Group", {"is_group": 0}) or "All Supplier Groups"
		frappe.get_doc({"doctype": "Supplier", "supplier_name": name, "supplier_group": group}).insert()


def create_profile(company, unit_type, warehouse, strength, rate, effective_from, order_reference):
	if frappe.db.exists("Trust Unit Profile", company):
		return frappe.get_doc("Trust Unit Profile", company)
	hostel = unit_type == "Hostel"
	return frappe.get_doc(
		{
			"doctype": "Trust Unit Profile",
			"company": company,
			"unit_type": unit_type,
			"tracks_residents": hostel,
			"tracks_food_statement": hostel,
			"tracks_results": hostel,
			"ration_warehouse": warehouse,
			"sanctions": [
				{
					"effective_from": getdate(effective_from),
					"sanctioned_strength": strength,
					"grant_rate": rate,
					"order_reference": order_reference,
				}
			],
		}
	).insert()


# name, parent, root_type, order on the food statement, rp head in, rp head out
ACCOUNTS = [
	("Food", "Indirect Expenses", "Expense", None, None, "Food"),
	("Vegetables", "Indirect Expenses", "Expense", 1, None, "Food"),
	("Mutton", "Indirect Expenses", "Expense", 2, None, "Food"),
	("Milk", "Indirect Expenses", "Expense", 3, None, "Food"),
	("Fuel", "Indirect Expenses", "Expense", 4, None, "Fuel"),
	("Detergent", "Indirect Expenses", "Expense", None, None, "Detergent"),
	("Salaries", "Indirect Expenses", "Expense", 5, None, "Salaries"),
	("GESCOM", "Indirect Expenses", "Expense", 6, None, "GESCOM"),
	("Education", "Indirect Expenses", "Expense", None, None, "Education"),
	("Miscellaneous", "Indirect Expenses", "Expense", None, None, "Miscellaneous"),
	("Govt. grant received", "Indirect Income", "Income", None, "Govt. grant received", None),
	("Bank interest", "Indirect Income", "Income", None, "Bank interest", None),
	("Zohra trust", "Current Liabilities", "Liability", None, "Loan from Zohra trust", "Transfer to Zohra trust"),
]

# item, uom, expense account
STOCK_ITEMS = [
	("Rice", "Kg", "Food"), ("Jawar", "Kg", "Food"), ("S. Oil", "Kg", "Food"), ("Daal", "Kg", "Food"),
	("Sugar", "Kg", "Food"), ("Tamarind", "Kg", "Food"), ("Salt", "Kg", "Food"), ("G. Nut", "Kg", "Food"),
	("Chilli", "Kg", "Food"), ("Condiments", "Kg", "Food"), ("Onion", "Kg", "Food"), ("C. Oil", "Kg", "Food"),
	("T. Soap", "Nos", "Detergent"), ("W. Soap", "Nos", "Detergent"),
]  # fmt: skip
NON_STOCK_ITEMS = ["Vegetables", "Mutton", "Milk", "Fuel"]


def create_accounts(company, abbr):
	for name, parent, root_type, order, rp_in, rp_out in ACCOUNTS:
		if frappe.db.exists("Account", f"{name} - {abbr}"):
			continue
		frappe.get_doc(
			{
				"doctype": "Account",
				"account_name": name,
				"company": company,
				"parent_account": f"{parent} - {abbr}",
				"root_type": root_type,
				"account_type": "Expense Account" if root_type == "Expense" else "",
				"custom_on_food_statement": 1 if order else 0,
				"custom_statement_order": order,
				"custom_rp_head_in": rp_in,
				"custom_rp_head_out": rp_out,
			}
		).insert()


def create_cash_mode(company, abbr):
	"""Cash mode of payment pointing at the unit's cash account, so cash purchase invoices post."""
	mode = frappe.get_doc("Mode of Payment", "Cash") if frappe.db.exists("Mode of Payment", "Cash") else None
	if not mode:
		mode = frappe.get_doc({"doctype": "Mode of Payment", "mode_of_payment": "Cash", "type": "Cash"}).insert()
	if not any(row.company == company for row in mode.accounts):
		mode.append("accounts", {"company": company, "default_account": f"Cash - {abbr}"})
		mode.save()


def create_items(company, abbr, warehouse):
	group = "Hostel Ration"
	if not frappe.db.exists("Item Group", group):
		frappe.get_doc({"doctype": "Item Group", "item_group_name": group, "parent_item_group": "All Item Groups"}).insert()
	rows = [(n, u, a, 1, i + 1) for i, (n, u, a) in enumerate(STOCK_ITEMS)]
	rows += [(n, "Nos", n, 0, None) for n in NON_STOCK_ITEMS]
	for code, uom, account, is_stock, order in rows:
		# a warehouse is set on every row, else Frappe fills the site's default one from another company
		defaults = {"company": company, "expense_account": f"{account} - {abbr}", "default_warehouse": warehouse}
		if frappe.db.exists("Item", code):
			item = frappe.get_doc("Item", code)
			if not any(row.company == company for row in item.item_defaults):
				item.append("item_defaults", defaults)
				item.save()
			continue
		frappe.get_doc(
			{
				"doctype": "Item",
				"item_code": code,
				"item_name": code,
				"item_group": group,
				"stock_uom": uom,
				"is_stock_item": is_stock,
				"custom_on_food_statement": 1 if is_stock else 0,
				"custom_statement_order": order,
				"item_defaults": [defaults],
			}
		).insert()


def create_bank(company, abbr, bank_name):
	"""A bank GL account and the Bank Account that points at it, for Cash Bank Vouchers in Bank mode."""
	account = f"Bank - {abbr}"
	if not frappe.db.exists("Account", account):
		frappe.get_doc(
			{
				"doctype": "Account",
				"account_name": "Bank",
				"company": company,
				"parent_account": f"Bank Accounts - {abbr}",
				"account_type": "Bank",
				"root_type": "Asset",
			}
		).insert()
	if not frappe.db.exists("Bank", bank_name):
		frappe.get_doc({"doctype": "Bank", "bank_name": bank_name}).insert()
	name = f"{company} - {bank_name}"
	if not frappe.db.exists("Bank Account", name):
		frappe.get_doc(
			{
				"doctype": "Bank Account",
				"account_name": company,
				"bank": bank_name,
				"account": account,
				"company": company,
				"is_company_account": 1,
			}
		).insert()
