import frappe
from frappe import _
from frappe.utils import formatdate, getdate


def assert_period_open(company, date, doctype=None):
	"""Raise if an Accounting Period of the company has closed this date.

	With doctype, only a period that closes that DocType counts.
	"""
	date = getdate(date)
	conditions = "ap.company = %(company)s AND cd.closed = 1 AND %(date)s BETWEEN ap.start_date AND ap.end_date"
	if doctype:
		conditions += " AND cd.document_type = %(doctype)s"
	periods = frappe.db.sql(
		f"""SELECT DISTINCT ap.name
		FROM `tabAccounting Period` ap, `tabClosed Document` cd
		WHERE ap.name = cd.parent AND {conditions}""",
		{"company": company, "date": date, "doctype": doctype},
		as_dict=True,
	)
	for period in periods:
		frappe.throw(
			_("{0} is closed: Accounting Period {1} covers {2}").format(
				_(doctype) if doctype else _("Posting"), period.name, formatdate(date)
			),
			title=_("Period Closed"),
		)
