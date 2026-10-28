import frappe
from frappe import _

from zohra_trust.utils.period import assert_period_open


def validate_consumption(doc):
	warehouse = frappe.db.get_value("Trust Unit Profile", doc.company, "ration_warehouse")
	if not warehouse:
		frappe.throw(_("Set the Ration Warehouse in the Trust Unit Profile of {0}").format(doc.company))
	doc.warehouse = warehouse
	clash = frappe.db.get_value(
		"Material Consumption",
		{"company": doc.company, "posting_date": doc.posting_date, "docstatus": ["<", 2], "name": ["!=", doc.name or ""]},
		"name",
	)
	if clash:
		frappe.throw(_("Material Consumption {0} already exists for this day").format(clash), frappe.DuplicateEntryError)
	assert_period_open(doc.company, doc.posting_date, doc.doctype)
	if not doc.items:
		frappe.throw(_("Add at least one item"))
	seen = set()
	for row in doc.items:
		item = frappe.db.get_value("Item", row.item_code, ["item_name", "stock_uom", "custom_on_food_statement"], as_dict=True)
		if not item.custom_on_food_statement:
			frappe.throw(_("Row {0}: {1} is not on the Food Expenditure Statement").format(row.idx, row.item_code))
		if row.item_code in seen:
			frappe.throw(_("Row {0}: {1} appears twice").format(row.idx, row.item_code))
		seen.add(row.item_code)
		if (row.qty or 0) <= 0:
			frappe.throw(_("Row {0}: Qty must be above zero").format(row.idx))
		row.item_name, row.uom = item.item_name, item.stock_uom


def make_stock_entry(doc):
	entry = frappe.new_doc("Stock Entry")
	entry.update(
		{
			"stock_entry_type": "Material Issue",
			"purpose": "Material Issue",
			"company": doc.company,
			"posting_date": doc.posting_date,
			"set_posting_time": 1,
			"from_warehouse": doc.warehouse,
			"custom_material_consumption": doc.name,
			"remarks": _("Material Consumption {0}").format(doc.name),
		}
	)
	for row in doc.items:
		entry.append("items", {"item_code": row.item_code, "qty": row.qty, "s_warehouse": doc.warehouse})
	entry.flags.ignore_permissions = True
	entry.insert()
	entry.submit()
	doc.db_set("stock_entry", entry.name)


def cancel_stock_entry(doc):
	if not doc.stock_entry:
		return
	entry = frappe.get_doc("Stock Entry", doc.stock_entry)
	if entry.docstatus == 1:
		entry.flags.ignore_permissions = True
		entry.flags.ignore_linked_doctypes = ("Material Consumption",)
		entry.ignore_linked_doctypes = ("Material Consumption",)
		entry.cancel()
