import frappe


def has_column(doctype, fieldname):
	"""Read the live table, not Frappe's cached column list."""
	return bool(frappe.db.sql(f"show columns from `tab{doctype}` like %s", fieldname))

SKIP = ("Section Break", "Column Break", "Tab Break", "HTML", "Button", "Table", "Table MultiSelect", "Heading", "Fold", "Image")


def add_missing_custom_field_columns():
	"""after_migrate: reload any DocType whose Custom Field has no database column.

	An ERPNext patch can re-create Custom Fields (Address, Contact) without adding their
	columns on an older site, which breaks every form that reads them.
	"""
	missing = set()
	for cf in frappe.get_all("Custom Field", fields=["dt", "fieldname", "fieldtype"]):
		if cf.fieldtype in SKIP or not frappe.db.exists("DocType", cf.dt):
			continue
		if not frappe.get_meta(cf.dt).issingle and not has_column(cf.dt, cf.fieldname):
			missing.add(cf.dt)
	for doctype in sorted(missing):
		frappe.reload_doctype(doctype, force=True)
		print(f"zohra_trust: added missing custom field columns on {doctype}")
