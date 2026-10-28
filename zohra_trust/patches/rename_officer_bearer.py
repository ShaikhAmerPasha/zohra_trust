import frappe


def execute():
	"""Office Bearer was renamed Officer Bearer (the report's wording). Nothing was entered yet, so the old DocType is dropped."""
	if frappe.db.exists("DocType", "Office Bearer"):
		frappe.delete_doc("DocType", "Office Bearer", force=True, ignore_missing=True)
