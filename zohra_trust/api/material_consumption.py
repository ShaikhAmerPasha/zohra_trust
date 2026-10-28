import frappe


@frappe.whitelist()
def copy_yesterday(company, posting_date):
	"""Items and quantities of the latest Material Consumption before posting_date."""
	frappe.has_permission("Material Consumption", "read", throw=True)
	previous = frappe.db.get_value(
		"Material Consumption",
		{"company": company, "posting_date": ["<", posting_date], "docstatus": ["<", 2]},
		"name",
		order_by="posting_date desc, creation desc",
	)
	if not previous:
		return []
	return frappe.get_all(
		"Material Consumption Item",
		filters={"parent": previous, "parenttype": "Material Consumption"},
		fields=["item_code", "item_name", "uom", "qty"],
		order_by="idx asc",
	)
