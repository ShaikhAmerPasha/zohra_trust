"""Slice 4, phase a: the generated pages of the half-yearly report."""

import io

import frappe
from frappe.tests.utils import FrappeTestCase
from pypdf import PdfReader

from zohra_trust.tests.pack_data import make_pack_data
from zohra_trust.utils.report_pages import build_pages, inr, qty, to_pdf, wrap_kannada

COMPANY, ABBR = "Test Hostel U", "THU"
START, END = "2026-04-01", "2026-09-30"


class TestFormatting(FrappeTestCase):
	def test_indian_grouping(self):
		self.assertEqual(inr(1230000), "12,30,000")
		self.assertEqual(inr(634446.84), "6,34,446.84")
		self.assertEqual(inr(18699.07), "18,699.07")
		self.assertEqual(inr(999), "999")
		self.assertEqual(inr(0), "0")
		self.assertEqual(inr(None), "")
		self.assertEqual(inr(-1500), "-1,500")
		self.assertEqual(inr(4439225.84), "44,39,225.84")

	def test_quantity_has_no_trailing_zeros(self):
		self.assertEqual((qty(1050.0), qty(2.5), qty(0)), ("1050", "2.5", ""))

	def test_kannada_runs_get_their_own_span(self):
		html = '<p title="ತರಗತಿ">ತರಗತಿ Class ಹೆಸರು</p><style>.x{content:"ಕ"}</style>'
		out = wrap_kannada(html)
		self.assertIn('<span class="kn">ತರಗತಿ</span> Class <span class="kn">ಹೆಸರು</span>', out)
		self.assertIn('title="ತರಗತಿ"', out)  # attributes are left alone
		self.assertIn('content:"ಕ"', out)  # so is CSS
		self.assertEqual(wrap_kannada("<title>ತರಗತಿ Class</title>"), "<title>ತರಗತಿ Class</title>")


class TestReportPages(FrappeTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		cls.girls = make_pack_data(COMPANY, ABBR)
		cls.pages, cls.warnings = build_pages(COMPANY, START, END)
		cls.by_key = {p["key"]: p for p in cls.pages}

	def test_pages_come_in_filing_order(self):
		keys = [p["key"] for p in self.pages]
		wanted = ["letter", "receipts_payments", "abstract", "food_2026_June", "food_2026_July", "appendix_h", "officer_bearers", "staff_list", "result_sheet"]
		self.assertEqual([k for k in keys if not k.startswith("register_")], wanted)
		self.assertTrue(all(k.startswith("register_") for k in keys[len(wanted):]))

	def test_warnings_skip_april_and_may_and_name_the_real_gaps(self):
		text = " ".join(self.warnings)
		self.assertNotIn("April", text)
		self.assertNotIn("May", text)
		self.assertIn("No submitted Food Expenditure Statement for August 2026", text)
		self.assertIn("No submitted Boarding Attendance for September 2026", text)
		self.assertNotIn("for July", text)

	def test_letter_uses_the_typed_text_and_lists_the_enclosures(self):
		html = self.by_key["letter"]["html"]
		self.assertIn("accounts for the period 01-04-2026 to 30-09-2026", html)
		for enclosure in ("Appendix – H", "List of officer bearer", "Boarding attendance", "Food expenditure statement", "List of staff members", "Grant bill", "Abstract of boarding and attendance"):
			self.assertIn(enclosure, html)
		self.assertIn("Tasneem Fatima", html)
		self.assertIn("Md. Azam Ali", html)
		self.assertNotIn("Retired Member", html)  # inactive bearers are not printed
		self.assertIn("Registration No. 16/79-80", html)

	def test_receipts_and_payments_uses_the_corrected_spelling_and_the_report_figures(self):
		html = self.by_key["receipts_payments"]["html"]
		self.assertIn("RECEIPTS", html)
		self.assertNotIn("RECIEPTS", html)
		for label in ("Loan from Zohra trust", "Bank interest", "Govt. grant received", "Food", "Fuel", "Detergent", "Salaries", "Education", "Miscellaneous", "Transfer to Zohra trust"):
			self.assertIn(label, html)
		self.assertIn("01-04-2026 to 30-09-2026", html)
		self.assertIn("ZOHRA MINORITY GIRLS HOSTEL", html)

	def test_abstract_sums_the_months(self):
		html = self.by_key["abstract"]["html"]
		self.assertIn("June 2026", html)
		self.assertIn("July 2026", html)
		self.assertIn("90", html)  # 3 girls x 30 days in June
		self.assertIn("93", html)  # 3 girls x 31 days in July
		self.assertIn("Sanction strength", html)

	def test_food_statement_header_and_landscape(self):
		page = self.by_key["food_2026_June"]
		self.assertEqual(page["orientation"], "Landscape")
		self.assertIn("Sanctioned Strength-150 Month-June Year-2026", page["html"])
		self.assertIn("Salaries", page["html"])
		for label in ("Opening balance", "Monthly purchase", "Monthly expenditure", "remaining balance"):
			self.assertIn(label, page["html"])

	def test_result_sheet_has_the_filed_columns_and_the_guardian(self):
		html = self.by_key["result_sheet"]["html"]
		for label in ("SL. NO", "NAME &amp; FATHER NAME", "CLASS", "TOTAL MARKS", "MARKS OBTAINED", "RESULT"):
			self.assertIn(label, html)
		self.assertIn("Girl U1 Father One", html)
		self.assertIn("PASS", html)

	def test_staff_list_comes_from_employees_with_qualification(self):
		html = self.by_key["staff_list"]["html"]
		self.assertIn("NAJMUNNISA", html)
		self.assertIn("HOUSE MOTHER", html)
		self.assertIn("10th", html)

	def test_register_is_one_page_per_school_and_month_with_kannada_heading(self):
		registers = [p for p in self.pages if p["key"].startswith("register_")]
		self.assertEqual(len(registers), 4)  # two months x two schools
		html = registers[0]["html"]
		self.assertIn('<span class="kn">ಶಾಲೆ: ಕಾಲೇಜು ಹಾಜರಾತಿ ನೊಂದಣಿ</span>', html)
		self.assertIn("School: College attendance register", html)
		self.assertIn("Days school ran", html)
		self.assertIn("Reasons for absence", html)

	def test_every_page_renders_to_pdf_and_orientation_is_kept(self):
		"""Regression: wkhtmltopdf crashed (exit -11) on a text run mixing Kannada and Latin."""
		for page in self.pages:
			pdf = to_pdf(page["html"], page["orientation"])
			self.assertTrue(pdf.startswith(b"%PDF"), page["key"])
			box = PdfReader(io.BytesIO(pdf)).pages[0].mediabox
			landscape = float(box.width) > float(box.height)
			self.assertEqual(landscape, page["orientation"] == "Landscape", page["key"])

	def test_mixed_kannada_and_latin_in_typed_text_does_not_crash(self):
		profile = frappe.get_doc("Trust Unit Profile", COMPANY)
		profile.letter_text = "<p>ಮಾನ್ಯರೇ, Sub: accounts ತಿಂಗಳು {{ period }}</p>"
		profile.save()
		pages, _warnings = build_pages(COMPANY, START, END)
		self.assertTrue(to_pdf(pages[0]["html"]).startswith(b"%PDF"))
