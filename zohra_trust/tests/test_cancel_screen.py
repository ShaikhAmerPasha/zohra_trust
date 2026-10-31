"""Cancelling from the form, as the screen does it.

The Cancel button first asks get_submitted_linked_docs for the linked submitted documents and, if there are
any, offers Cancel All, which cancels them first. A Material Consumption and its Stock Entry (a Cash Bank
Voucher and its Journal Entry) link to each other, so Cancel All is refused. Each form therefore declares
frm.ignore_doctypes_on_cancel_all; the list is read from the form's JS file so that dropping it fails here.
"""

import json
import re
from pathlib import Path

import frappe
from frappe.desk.form.linked_with import cancel_all_linked_docs, get_submitted_linked_docs
from frappe.desk.form.save import cancel
from frappe.tests.utils import FrappeTestCase

from zohra_trust.tests.helpers import bin_qty, consume, make_unit, seed_stock

DOCTYPE_DIR = Path(frappe.get_app_path("zohra_trust", "trust_operations", "doctype"))


def declared_ignore_list(folder):
	"""The doctypes a form's JS file lists in frm.ignore_doctypes_on_cancel_all."""
	script = (DOCTYPE_DIR / folder / f"{folder}.js").read_text()
	match = re.search(r"frm\.ignore_doctypes_on_cancel_all\s*=\s*(\[[^\]]*\])", script)
	return json.loads(match.group(1)) if match else []


class TestCancelFromScreen(FrappeTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		cls.company, cls.abbr = "Test Hostel S", "THS"
		make_unit(cls.company, cls.abbr)
		seed_stock(cls.abbr, cls.company, "2026-05-31", {"Rice": (100, 4900)})

	def test_forms_declare_what_cancel_all_must_skip(self):
		self.assertEqual(declared_ignore_list("material_consumption"), ["Stock Entry"])
		self.assertEqual(declared_ignore_list("cash_bank_voucher"), ["Journal Entry"])

	def test_consumption_cancel_all_alone_is_refused_and_the_declared_list_avoids_it(self):
		doc = consume(self.company, "2026-06-11", {"Rice": 10})
		listed = get_submitted_linked_docs(doc.doctype, doc.name)
		self.assertEqual([d["doctype"] for d in listed["docs"]], ["Stock Entry"])  # the screen would offer Cancel All
		with self.assertRaises(frappe.ValidationError):  # and Cancel All is refused: the cause of the defect
			cancel_all_linked_docs(json.dumps(listed["docs"]))
		self.assertEqual(frappe.db.get_value("Material Consumption", doc.name, "docstatus"), 1)
		ignore = declared_ignore_list("material_consumption")
		self.assertEqual(get_submitted_linked_docs(doc.doctype, doc.name, ignore)["count"], 0)  # no dialog now

	def test_consumption_cancel_through_the_screen_endpoint(self):
		before = bin_qty(self.abbr, "Rice")
		doc = consume(self.company, "2026-06-12", {"Rice": 10})
		self.assertEqual(bin_qty(self.abbr, "Rice"), before - 10)
		cancel(doc.doctype, doc.name)  # what the form calls after the dialog step is skipped
		self.assertEqual(frappe.db.get_value("Material Consumption", doc.name, "docstatus"), 2)
		self.assertEqual(frappe.db.get_value("Stock Entry", doc.stock_entry, "docstatus"), 2)
		self.assertEqual(bin_qty(self.abbr, "Rice"), before)

	def test_voucher_cancel_through_the_screen(self):
		from zohra_trust.tests.test_slice3 import ABBR, COMPANY, voucher

		make_unit(COMPANY, ABBR)
		doc = voucher("Payment", "Salaries", 500)
		listed = get_submitted_linked_docs(doc.doctype, doc.name)
		self.assertEqual([d["doctype"] for d in listed["docs"]], ["Journal Entry"])
		with self.assertRaises(frappe.ValidationError):
			cancel_all_linked_docs(json.dumps(listed["docs"]))
		self.assertEqual(frappe.db.get_value("Journal Entry", doc.journal_entry, "docstatus"), 1)
		ignore = declared_ignore_list("cash_bank_voucher")
		self.assertEqual(get_submitted_linked_docs(doc.doctype, doc.name, ignore)["count"], 0)
		cancel(doc.doctype, doc.name)
		self.assertEqual(frappe.db.get_value("Cash Bank Voucher", doc.name, "docstatus"), 2)
		self.assertEqual(frappe.db.get_value("Journal Entry", doc.journal_entry, "docstatus"), 2)
		self.assertEqual(frappe.db.count("GL Entry", {"voucher_no": doc.journal_entry, "is_cancelled": 0}), 0)

	def test_journal_entry_still_cannot_be_cancelled_directly(self):
		from zohra_trust.tests.test_slice3 import ABBR, COMPANY, voucher

		make_unit(COMPANY, ABBR)
		doc = voucher("Payment", "Salaries", 300)
		with self.assertRaises(frappe.ValidationError):
			cancel("Journal Entry", doc.journal_entry)
		self.assertEqual(frappe.db.get_value("Journal Entry", doc.journal_entry, "docstatus"), 1)
