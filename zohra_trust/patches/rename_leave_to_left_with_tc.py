import frappe


def execute():
	"""Promotion Action `Leave` became `Left with T.C.`. Convert the rows already entered."""
	frappe.db.sql("UPDATE `tabResult Row` SET promotion_action = 'Left with T.C.' WHERE promotion_action = 'Leave'")
