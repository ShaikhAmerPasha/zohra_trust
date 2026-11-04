"""Roles: the Principal cancels and amends through the screen path; Store runs a cycle; a User Permission limits a user to one Company."""

import frappe
from frappe.desk.form.linked_with import get_submitted_linked_docs
from frappe.desk.form.save import cancel
from frappe.tests.utils import FrappeTestCase

from zohra_trust.tests.helpers import bin_qty, consume, make_attendance, make_student, make_unit, purchase, seed_stock
from zohra_trust.tests.test_cancel_screen import declared_ignore_list

COMPANY, ABBR = "Test Hostel P", "THP"
OTHER, OTHER_ABBR = "Test Hostel Q", "THQ"
PRINCIPAL, ENTRY, STORE, LIMITED = (f"role.{n}@example.com" for n in ("principal", "entry", "store", "limited"))


def make_user(email, role):
	if not frappe.db.exists("User", email):
		frappe.get_doc({"doctype": "User", "email": email, "first_name": role, "send_welcome_email": 0, "roles": [{"role": role}]}).insert()


def as_user(user, fn):
	frappe.set_user(user)
	try:
		return fn()
	finally:
		frappe.set_user("Administrator")


def voucher(head, amount, date="2026-06-10"):
	doc = frappe.get_doc(
		{"doctype": "Cash Bank Voucher", "company": COMPANY, "voucher_type": "Payment", "posting_date": date, "mode": "Cash", "account_head": f"{head} - {ABBR}", "amount": amount}
	)
	doc.insert()
	doc.submit()
	return doc


def screen_cancel(doctype, name):
	"""What the form does: ask for linked documents (skipping the declared ones), then cancel."""
	folder = doctype.lower().replace(" ", "_")
	try:
		ignore = declared_ignore_list(folder)
	except FileNotFoundError:
		ignore = []
	linked = get_submitted_linked_docs(doctype, name, ignore)
	assert linked["count"] == 0, f"the screen would stop on a linked-documents dialog: {linked['docs']}"
	cancel(doctype, name)


def amend(doc):
	"""What the Amend button does: a draft copy that points back at the cancelled document, then Submit."""
	new = frappe.copy_doc(doc, ignore_no_copy=False)  # honours no_copy, as the Amend button does
	new.amended_from = doc.name
	new.docstatus = 0
	new.insert()
	new.submit()
	return new


class TestPrincipalCancelsAndAmends(FrappeTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		make_unit(COMPANY, ABBR)
		seed_stock(ABBR, COMPANY, "2026-05-31", {"Rice": (100, 4900)})
		make_user(PRINCIPAL, "Principal")
		make_user(ENTRY, "Data Entry")

	def old(self, doctype, name, days=10):
		"""Make a document older than the correction window, as it would be by the time the Principal acts."""
		frappe.db.set_value(doctype, name, "creation", frappe.utils.add_days(frappe.utils.now_datetime(), -days), update_modified=False)

	def test_principal_cancels_and_amends_a_material_consumption(self):
		before = bin_qty(ABBR, "Rice")
		doc = as_user(ENTRY, lambda: consume(COMPANY, "2026-06-11", {"Rice": 10}))
		self.old("Material Consumption", doc.name)
		self.assertEqual(bin_qty(ABBR, "Rice"), before - 10)

		def act():
			screen_cancel("Material Consumption", doc.name)
			return amend(frappe.get_doc("Material Consumption", doc.name))

		new = as_user(PRINCIPAL, act)
		self.assertEqual(frappe.db.get_value("Material Consumption", doc.name, "docstatus"), 2)
		self.assertEqual(frappe.db.get_value("Stock Entry", doc.stock_entry, "docstatus"), 2)
		self.assertEqual(new.amended_from, doc.name)
		self.assertEqual(new.docstatus, 1)
		self.assertEqual(bin_qty(ABBR, "Rice"), before - 10)  # the amended one issues again

	def test_principal_cancels_and_amends_a_cash_bank_voucher(self):
		doc = as_user(ENTRY, lambda: voucher("Salaries", 900))
		self.old("Cash Bank Voucher", doc.name)

		def act():
			screen_cancel("Cash Bank Voucher", doc.name)
			return amend(frappe.get_doc("Cash Bank Voucher", doc.name))

		new = as_user(PRINCIPAL, act)
		self.assertEqual(frappe.db.get_value("Cash Bank Voucher", doc.name, "docstatus"), 2)
		self.assertEqual(frappe.db.get_value("Journal Entry", doc.journal_entry, "docstatus"), 2)
		self.assertEqual(frappe.db.get_value("Journal Entry", new.journal_entry, "docstatus"), 1)
		self.assertEqual(new.amended_from, doc.name)

	def test_principal_cancels_a_purchase_invoice_and_the_stock_goes_back(self):
		before = bin_qty(ABBR, "Rice")
		doc = as_user(ENTRY, lambda: purchase(ABBR, COMPANY, "2026-06-12", {"Rice": (20, 1000)}))
		self.old("Purchase Invoice", doc.name)
		self.assertEqual(bin_qty(ABBR, "Rice"), before + 20)
		as_user(PRINCIPAL, lambda: screen_cancel("Purchase Invoice", doc.name))
		self.assertEqual(frappe.db.get_value("Purchase Invoice", doc.name, "docstatus"), 2)
		self.assertEqual(bin_qty(ABBR, "Rice"), before)

	def test_principal_cancels_attendance_and_a_statement(self):
		make_student(COMPANY, 1)
		att = make_attendance(COMPANY, "June")
		att.fill_rows()
		att.insert()
		att.submit()
		stmt = frappe.get_doc({"doctype": "Food Expenditure Statement", "company": COMPANY, "month": "June", "year": 2026, "is_opening": 1})
		stmt.fill()
		stmt.insert()
		stmt.submit()
		for d in (att, stmt):
			self.old(d.doctype, d.name)
			as_user(PRINCIPAL, lambda d=d: screen_cancel(d.doctype, d.name))
			self.assertEqual(frappe.db.get_value(d.doctype, d.name, "docstatus"), 2, d.doctype)

	def test_principal_can_open_the_receipts_report(self):
		from zohra_trust.trust_operations.report.receipts_and_payments_account.receipts_and_payments_account import execute

		voucher("Salaries", 100, "2026-06-20")

		def run():
			self.assertTrue(frappe.has_permission("GL Entry", "read"))
			return execute({"company": COMPANY, "from_date": "2026-04-01", "to_date": "2026-09-30"})

		_columns, rows = as_user(PRINCIPAL, run)
		self.assertTrue(any(r["particulars"] == "Salaries" for r in rows))


class TestStoreCycle(FrappeTestCase):
	"""Store buys, records what the kitchen used and makes the monthly statement: spec section 6, Roles."""

	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		cls.company, cls.abbr = "Test Hostel T", "THT"
		make_unit(cls.company, cls.abbr)
		seed_stock(cls.abbr, cls.company, "2026-05-31", {"Rice": (50, 2500)})
		make_user(STORE, "Store")

	def test_store_runs_a_whole_month(self):
		def cycle():
			bought = purchase(self.abbr, self.company, "2026-06-10", {"Rice": (100, 5000)})
			used = consume(self.company, "2026-06-15", {"Rice": 40})
			statement = frappe.get_doc({"doctype": "Food Expenditure Statement", "company": self.company, "month": "June", "year": 2026, "is_opening": 1})
			statement.fill()
			statement.insert()
			statement.submit()
			return bought, used, statement

		bought, used, statement = as_user(STORE, cycle)
		self.assertEqual((bought.docstatus, used.docstatus, statement.docstatus), (1, 1, 1))
		rice = next(l for l in statement.lines if l.item_code == "Rice")
		self.assertEqual((rice.old_qty, rice.purchased_qty, rice.consumed_qty, rice.balance_qty), (50, 100, 40, 110))
		self.assertEqual(statement.owner, STORE)
		self.assertEqual(bin_qty(self.abbr, "Rice"), 110)

	def test_store_cannot_do_what_the_spec_does_not_give_it(self):
		def check():
			for doctype in ("Cash Bank Voucher", "Boarding Attendance", "Result Sheet of Inmates", "Student Enrollment"):
				self.assertFalse(frappe.has_permission(doctype, "create"), doctype)

		as_user(STORE, check)


class TestUserPermissionOnCompany(FrappeTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		make_unit(COMPANY, ABBR)
		make_unit(OTHER, OTHER_ABBR)
		make_user(LIMITED, "Data Entry")
		if not frappe.db.exists("User Permission", {"user": LIMITED, "allow": "Company", "for_value": COMPANY}):
			frappe.get_doc({"doctype": "User Permission", "user": LIMITED, "allow": "Company", "for_value": COMPANY}).insert()
		frappe.clear_cache(user=LIMITED)

	def test_a_user_limited_to_one_company_cannot_see_the_other(self):
		own = voucher("Salaries", 10, "2026-07-01")
		frappe.get_doc({"doctype": "Cash Bank Voucher", "company": OTHER, "voucher_type": "Payment", "posting_date": "2026-07-01", "mode": "Cash", "account_head": f"Salaries - {OTHER_ABBR}", "amount": 20}).insert()
		other = frappe.get_all("Cash Bank Voucher", {"company": OTHER}, pluck="name")[0]
		student = make_student(OTHER, 1)

		def look():
			seen = frappe.get_list("Cash Bank Voucher", fields=["name", "company"], limit=500)
			self.assertTrue(seen)
			self.assertEqual({r.company for r in seen}, {COMPANY})
			self.assertIn(own.name, [r.name for r in seen])
			self.assertNotIn(other, [r.name for r in seen])
			self.assertFalse(frappe.has_permission("Cash Bank Voucher", "read", doc=other))
			with self.assertRaises(frappe.PermissionError):
				frappe.get_doc("Cash Bank Voucher", other).check_permission("read")
			self.assertFalse(frappe.has_permission("Student Enrollment", "read", doc=student.name))
			self.assertNotIn(student.name, [r.name for r in frappe.get_list("Student Enrollment", limit=500)])
			self.assertTrue(frappe.has_permission("Cash Bank Voucher", "read", doc=own.name))

		as_user(LIMITED, look)
