import frappe
from frappe.utils import getdate


def get_unit_sanction(company, date):
	"""Sanction in force for a unit on a date, or None.

	Latest effective_from wins among rows with effective_from <= date and
	effective_to empty or >= date. Returns strength, rate, rule.
	"""
	date = getdate(date)
	rows = frappe.get_all(
		"Unit Sanction",
		filters={"parent": company, "parenttype": "Trust Unit Profile", "effective_from": ["<=", date]},
		fields=["effective_from", "effective_to", "sanctioned_strength", "grant_rate", "grant_rule", "order_reference"],
		order_by="effective_from desc, idx desc",
		parent_doctype="Trust Unit Profile",
	)
	for row in rows:
		if not row.effective_to or getdate(row.effective_to) >= date:
			return frappe._dict(
				strength=row.sanctioned_strength,
				rate=row.grant_rate,
				rule=row.grant_rule or "Full month per student",
				effective_from=row.effective_from,
				order_reference=row.order_reference,
			)
	return None
