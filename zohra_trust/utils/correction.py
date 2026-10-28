import frappe
from frappe import _
from frappe.utils import cint, date_diff, getdate, today

# Derived documents follow the document that made them, which was already checked.
DERIVED_LINKS = ("custom_material_consumption", "custom_cash_bank_voucher")


def check_correction_window(doc, method=None):
	"""before_cancel hook: a user may cancel or amend only their own entry, inside the window."""
	user = frappe.session.user
	if user == "Administrator" or "Principal" in frappe.get_roles(user):
		return
	if any(doc.get(f) for f in DERIVED_LINKS):
		return
	if doc.owner != user:
		frappe.throw(_("Only {0} or a Principal can cancel or amend this entry").format(doc.owner), frappe.PermissionError)
	window = frappe.db.get_single_value("Trust Settings", "correction_window_days")
	window = 1 if window in (None, "") else cint(window)
	if date_diff(today(), getdate(doc.creation)) > window:
		frappe.throw(
			_("The correction window of {0} day(s) has passed. Ask a Principal to cancel or amend it").format(window),
			frappe.PermissionError,
		)
