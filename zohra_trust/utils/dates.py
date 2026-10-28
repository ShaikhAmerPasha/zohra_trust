import calendar

import frappe
from frappe import _
from frappe.utils import getdate

MONTHS = [
	"January", "February", "March", "April", "May", "June",
	"July", "August", "September", "October", "November", "December",
]  # fmt: skip


def month_bounds(month, year):
	"""Return (period_start, period_end, calendar_days) for a month name and year."""
	number = MONTHS.index(month) + 1
	days = calendar.monthrange(int(year), number)[1]
	return getdate(f"{int(year)}-{number:02d}-01"), getdate(f"{int(year)}-{number:02d}-{days:02d}"), days


def month_number(month):
	return MONTHS.index(month) + 1


def get_academic_year(date, throw=True):
	"""Name of the Trust Academic Year that contains date."""
	date = getdate(date)
	name = frappe.db.get_value(
		"Trust Academic Year", {"start_date": ["<=", date], "end_date": [">=", date]}, "name"
	)
	if not name and throw:
		frappe.throw(_("No Academic Year found for {0}").format(frappe.format(date, "Date")))
	return name
