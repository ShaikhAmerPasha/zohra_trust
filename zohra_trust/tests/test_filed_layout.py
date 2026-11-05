"""The generated pages follow the filed pages: the decisions taken after comparing with the two filed reports."""

import re

import frappe
from frappe.tests.utils import FrappeTestCase

from zohra_trust.tests.pack_data import make_pack_data
from zohra_trust.utils.report_pages import RESULT_ROWS, chunks, build_pages

COMPANY, ABBR = "Test Hostel U", "THU"
START, END = "2026-04-01", "2026-09-30"


class TestFiledLayout(FrappeTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		make_pack_data(COMPANY, ABBR)
		cls.pages, _warnings = build_pages(COMPANY, START, END, "2026-10-05", "Kalaburagi")
		cls.by_key = {p["key"]: p for p in cls.pages}

	def test_register_lists_every_girl_once_with_no_school_name_and_signs_as_principal(self):
		html = self.by_key["register_2026_June"]["html"]
		for name in ("Girl U1", "Girl U2", "Girl U3"):  # girl 3 is in the other school: still on the same list
			self.assertEqual(html.count(name), 1, name)
		self.assertNotIn("Zohra English Medium", html)
		self.assertNotIn("Zohra Kannada Medium", html)
		self.assertIn("Principal", html)
		self.assertIn("June 2026", html)

	def test_paging_follows_the_filed_sheets(self):
		self.assertEqual([len(c) for c in chunks(range(45), 19, 22)], [19, 22, 4])  # register: heading takes room on page one
		self.assertEqual([len(c) for c in chunks(range(130), RESULT_ROWS, RESULT_ROWS)], [22] * 5 + [20])  # result sheet, 22 a page
		self.assertEqual(len(chunks([], 19, 22)), 1)  # an empty list still prints its heading page

	def test_abstract_leaves_school_attendance_and_total_blank(self):
		html = self.by_key["abstract"]["html"]
		self.assertIn("School attendance", html)
		self.assertRegex(html, r"<td>\s*90\s*</td><td></td><td></td><td></td>")  # June: hostel days 90, then three blank cells

	def test_result_sheet_has_no_signature_line(self):
		html = self.by_key["result_sheet"]["html"]
		self.assertNotIn("Secretary", html)
		self.assertNotIn("Principal", html)
		self.assertNotIn('class="sign"', html)

	def test_date_and_place_come_from_the_pack(self):
		self.assertIn("Date: 05-10-2026", self.by_key["letter"]["html"])
		self.assertIn("Date: 05-10-2026", self.by_key["receipts_payments"]["html"])
		appendix = self.by_key["appendix_h"]["html"]
		self.assertIn("Date: 05-10-2026", appendix)
		self.assertIn("Place: Kalaburagi", appendix)
		self.assertIn("Zohra Minority Girls Hostel", appendix)
		bare, _ = build_pages(COMPANY, START, END)
		self.assertNotIn("Date: ", {p["key"]: p for p in bare}["letter"]["html"])  # no date typed: none printed

	def test_officer_list_has_the_filed_columns_and_the_qualification_under_the_name(self):
		html = self.by_key["officer_bearers"]["html"]
		for label in ("SL.NO", "NAME", "DESIGNATION", "ADDRESS"):
			self.assertIn(f"<th>{label}</th>", html)
		self.assertRegex(html, r"Tasneem Fatima<br>B\.A")

	def test_letterhead_labels_trustees_above_the_name(self):
		settings = frappe.get_single("Trust Settings")
		before = [o.as_dict() for o in settings.officer_bearers]
		try:
			settings.officer_bearers = []
			settings.append("officer_bearers", {"member_name": "Dr Test Trustee", "designation": "Trustee", "qualification": "MBBS", "sort_order": 1, "is_active": 1})
			settings.append("officer_bearers", {"member_name": "Test President", "designation": "President", "sort_order": 2, "is_active": 1})
			settings.save()
			pages, _ = build_pages(COMPANY, START, END)
			html = {p["key"]: p for p in pages}["letter"]["html"]
			self.assertRegex(html, r"Trustee:</div>\s*<div class=\"name\">Dr Test Trustee")
			self.assertRegex(html, r"Test President</div>\s*<div>President</div>")  # others: the designation under the name
		finally:
			settings.officer_bearers = []
			for row in before:
				settings.append("officer_bearers", row)
			settings.save()
