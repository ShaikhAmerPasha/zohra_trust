import frappe
from frappe.tests.utils import FrappeTestCase

from zohra_trust.tests.helpers import make_unit, purchase
from zohra_trust.trust_operations.report.receipts_and_payments_account.receipts_and_payments_account import execute

COMPANY, ABBR = "Test Hostel F", "THF"


def voucher(voucher_type, head, amount, date="2026-06-10", mode="Cash", **kw):
	doc = frappe.get_doc(
		{
			"doctype": "Cash Bank Voucher",
			"company": COMPANY,
			"voucher_type": voucher_type,
			"posting_date": date,
			"mode": mode,
			"bank_account": f"{COMPANY} - Hostel Bank" if mode == "Bank" else None,
			"account_head": f"{head} - {ABBR}",
			"amount": amount,
			**kw,
		}
	)
	doc.insert()
	doc.submit()
	return doc


def gl(voucher_no):
	return {(e.account, round(e.debit), round(e.credit)) for e in frappe.get_all("GL Entry", {"voucher_no": voucher_no, "is_cancelled": 0}, ["account", "debit", "credit"])}


class TestCashBankVoucher(FrappeTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		make_unit(COMPANY, ABBR)

	def test_receipt_makes_journal_entry_with_right_sides(self):
		doc = voucher("Receipt", "Govt. grant received", 85000, narration="June grant")
		self.assertTrue(doc.name.startswith("CBV-"))
		entry = frappe.get_doc("Journal Entry", doc.journal_entry)
		self.assertEqual((entry.docstatus, entry.custom_cash_bank_voucher), (1, doc.name))
		self.assertEqual(gl(entry.name), {(f"Cash - {ABBR}", 85000, 0), (f"Govt. grant received - {ABBR}", 0, 85000)})

	def test_payment_from_bank_is_the_reverse(self):
		doc = voucher("Payment", "Fuel", 1200, mode="Bank", reference_no="CHQ123")
		self.assertEqual(gl(doc.journal_entry), {(f"Fuel - {ABBR}", 1200, 0), (f"Bank - {ABBR}", 0, 1200)})

	def test_cancel_voucher_cancels_entry(self):
		doc = voucher("Payment", "Education", 500)
		doc.cancel()
		self.assertEqual(frappe.db.get_value("Journal Entry", doc.journal_entry, "docstatus"), 2)
		self.assertEqual(gl(doc.journal_entry), set())

	def test_cancelling_the_journal_entry_directly_is_refused(self):
		doc = voucher("Payment", "Miscellaneous", 300)
		with self.assertRaises(frappe.ValidationError):
			frappe.get_doc("Journal Entry", doc.journal_entry).cancel()
		self.assertEqual(frappe.db.get_value("Journal Entry", doc.journal_entry, "docstatus"), 1)

	def test_checks(self):
		with self.assertRaises(frappe.ValidationError):
			voucher("Receipt", "Bank interest", 0)
		with self.assertRaises(frappe.ValidationError):  # Bank mode without a bank account
			voucher("Receipt", "Bank interest", 10, mode="Bank", bank_account=None)
		with self.assertRaises(frappe.ValidationError):  # payable account needs a party
			frappe.get_doc(
				{"doctype": "Cash Bank Voucher", "company": COMPANY, "voucher_type": "Payment", "posting_date": "2026-06-10", "mode": "Cash",
				 "account_head": f"Creditors - {ABBR}", "amount": 10}
			).insert()
		with self.assertRaises(frappe.ValidationError):  # cash account is not a head
			frappe.get_doc(
				{"doctype": "Cash Bank Voucher", "company": COMPANY, "voucher_type": "Payment", "posting_date": "2026-06-10", "mode": "Cash",
				 "account_head": f"Cash - {ABBR}", "amount": 10}
			).insert()

	def test_closed_period_refused(self):
		frappe.get_doc(
			{
				"doctype": "Accounting Period", "period_name": "THF closed May", "company": COMPANY,
				"start_date": "2026-05-01", "end_date": "2026-05-31",
				"closed_documents": [{"document_type": "Cash Bank Voucher", "closed": 1}],
			}
		).insert()
		with self.assertRaises(frappe.ValidationError):
			voucher("Payment", "Food", 10, date="2026-05-05")

	def test_roles(self):
		entry_user, store_user = "cbv.entry@example.com", "cbv.store@example.com"
		for email, role in ((entry_user, "Data Entry"), (store_user, "Store")):
			if not frappe.db.exists("User", email):
				frappe.get_doc({"doctype": "User", "email": email, "first_name": role, "send_welcome_email": 0, "roles": [{"role": role}]}).insert()
		frappe.set_user(entry_user)
		try:
			doc = voucher("Payment", "Salaries", 700)  # Data Entry enters and submits; the entry is made for them
			self.assertEqual(frappe.db.get_value("Journal Entry", doc.journal_entry, "docstatus"), 1)
		finally:
			frappe.set_user("Administrator")
		frappe.set_user(store_user)
		try:
			self.assertFalse(frappe.has_permission("Cash Bank Voucher", "create"))
		finally:
			frappe.set_user("Administrator")


def amounts(rows):
	return {r["particulars"]: (r.get("receipts"), r.get("payments")) for r in rows}


class TestReceiptsAndPayments(FrappeTestCase):
	def test_filed_half_year(self):
		company, abbr = "Test Hostel G", "THG"
		make_unit(company, abbr)
		if not frappe.db.exists("Fiscal Year", "2025-2026"):  # the opening balances are dated 31 March
			frappe.get_doc({"doctype": "Fiscal Year", "year": "2025-2026", "year_start_date": "2025-04-01", "year_end_date": "2026-03-31"}).insert()
		opening = frappe.get_doc(
			{
				"doctype": "Journal Entry", "company": company, "posting_date": "2026-03-31",
				"accounts": [
					{"account": f"Cash - {abbr}", "debit_in_account_currency": 682},
					{"account": f"Bank - {abbr}", "debit_in_account_currency": 634446.84},
					{"account": f"Temporary Opening - {abbr}", "credit_in_account_currency": 635128.84},
				],
			}
		)
		opening.insert()
		opening.submit()

		def v(voucher_type, head, amount, date, mode="Cash"):
			doc = frappe.get_doc(
				{
					"doctype": "Cash Bank Voucher", "company": company, "voucher_type": voucher_type, "posting_date": date, "mode": mode,
					"bank_account": f"{company} - Hostel Bank" if mode == "Bank" else None,
					"account_head": f"{head} - {abbr}", "amount": amount,
				}
			)
			doc.insert()
			doc.submit()

		v("Receipt", "Zohra trust", 730000, "2026-04-05")  # loan, part in cash
		v("Receipt", "Zohra trust", 500000, "2026-04-06", mode="Bank")  # loan, part in the bank
		v("Receipt", "Bank interest", 4779, "2026-09-30", mode="Bank")
		for head, amount in (("Food", 563825), ("Fuel", 37780), ("Detergent", 47400), ("Salaries", 48000)):
			v("Payment", head, amount, "2026-07-15")
		v("Payment", "Zohra trust", 700000, "2026-08-20", mode="Bank")

		_columns, rows = execute({"company": company, "from_date": "2026-04-01", "to_date": "2026-09-30"})
		got = amounts(rows)
		self.assertEqual(got["Opening balance (Cash)"], (682, None))
		self.assertEqual(got["Opening balance (Bank)"], (634446.84, None))
		self.assertEqual(got["Loan from Zohra trust"], (1230000, None))
		self.assertEqual(got["Bank interest"], (4779, None))
		for head, amount in (("Food", 563825), ("Fuel", 37780), ("Detergent", 47400), ("Salaries", 48000), ("Transfer to Zohra trust", 700000)):
			self.assertEqual(got[head], (None, amount), head)
		self.assertEqual(got["Closing balance (Cash)"], (None, 33677))
		self.assertEqual(got["Closing balance (Bank)"][1], 439225.84)  # the filed 4,39,225 plus the 84 paise
		total = got["Total"]
		self.assertEqual(total[0], total[1])  # receipts equal payments
		self.assertEqual(int(total[0]), 1869907)
		for r in rows[:-1]:  # an empty cell is null, which the screen prints blank (a missing key prints 0.00)
			self.assertTrue("receipts" in r and "payments" in r)
			self.assertTrue(r["receipts"] is None or r["payments"] is None, r["particulars"])
		self.assertEqual([r["particulars"] for r in rows][-3:], ["Closing balance (Cash)", "Closing balance (Bank)", "Total"])

	def test_cash_purchase_appears_under_its_expense_head(self):
		company, abbr = "Test Hostel H", "THH"
		make_unit(company, abbr)
		purchase(abbr, company, "2026-06-03", {"Rice": (10, 500)})
		purchase(abbr, company, "2026-06-04", {"Vegetables": (1, 300)}, stock=False)
		_c, rows = execute({"company": company, "from_date": "2026-06-01", "to_date": "2026-06-30"})
		got = amounts(rows)
		self.assertEqual(got["Food"], (None, 800))  # Rice and Vegetables both go to the Food row
		self.assertNotIn("Creditors", got)
		self.assertEqual(got["Closing balance (Cash)"], (None, -800))
		self.assertEqual(got["Total"][0], got["Total"][1])
