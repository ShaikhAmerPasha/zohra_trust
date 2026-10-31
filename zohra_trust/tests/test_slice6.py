"""Slice 6: the whole filed June to September 2026 half year, through the desk's entry points, against the filed pages.

Runs tests/e2e_filed_half_year.py (attendance, purchases, consumption, food statements, vouchers, the Receipts
and Payments Account, then the Report Pack pages) and compares every figure with the filed report. Exactly one
difference is allowed: the filed Receipts and Payments page prints Food 5,63,825, but the filed food statements
add up to 5,79,598 of food purchases (a gap of 15,773 that also moves closing cash from 17,904 to the filed
33,677). It is the same in the Receipts report and on the pack page. Anything else that differs fails.
"""

from frappe.tests.utils import FrappeTestCase

from zohra_trust.tests import e2e_filed_half_year as e2e

KNOWN_GAP = {
	"R&P Food",
	"R&P Closing balance (Cash)",
	"pack R&P page prints Food",
	"pack R&P page prints Cash (closing)",
}


class TestFiledHalfYear(FrappeTestCase):
	def test_every_filed_figure_matches_except_the_known_gap(self):
		e2e.run()
		differing = {label for ok, label, _detail in e2e.LINES if not ok}
		self.assertEqual(differing, KNOWN_GAP)
		self.assertGreaterEqual(len(e2e.LINES), 200)  # the run really compared the whole half year
		# the pack pages were checked too, not only the records
		self.assertTrue(any(label.startswith("pack September food page") for _ok, label, _d in e2e.LINES))
		self.assertTrue(any(label.startswith("pack abstract page") for _ok, label, _d in e2e.LINES))
