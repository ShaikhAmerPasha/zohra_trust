import frappe
from frappe.tests.utils import FrappeTestCase

from zohra_trust.api.material_consumption import copy_yesterday
from zohra_trust.tests.helpers import bin_qty, consume, make_unit, pay_expense, purchase, seed_stock
from zohra_trust.utils.food_statement import calculate

# item: (old_qty, old_amount, purchased_qty, purchased_amount, consumed)
JUNE = {
	"Rice": (50, 2450, 1200, 58800, 1050), "Jawar": (35, 1050, 600, 18000, 450), "S. Oil": (3, 450, 30, 4500, 30),
	"Daal": (3, 240, 30, 2400, 30), "Sugar": (6, 330, 30, 1650, 32), "Tamarind": (0, 0, 30, 2250, 28),
	"Salt": (1, 20, 30, 600, 30), "G. Nut": (0, 0, 30, 3600, 30), "Chilli": (0, 0, 30, 4500, 30),
	"Condiments": (11, 2200, 20, 4000, 15), "Onion": (20, 400, 50, 1000, 60), "C. Oil": (2, 400, 40, 8000, 24),
	"T. Soap": (0, 0, 300, 4800, 300), "W. Soap": (0, 0, 300, 4200, 300),
}  # fmt: skip
# item: (expenditure, balance_qty, balance_amount)
JUNE_EXPECTED = {
	"Rice": (51450, 200, 9800), "Jawar": (13500, 185, 5550), "S. Oil": (4500, 3, 450), "Daal": (2400, 3, 240),
	"Sugar": (1760, 4, 220), "Tamarind": (2100, 2, 150), "Salt": (600, 1, 20), "G. Nut": (3600, 0, 0),
	"Chilli": (4500, 0, 0), "Condiments": (3000, 16, 3200), "Onion": (1200, 10, 200), "C. Oil": (4800, 18, 3600),
	"T. Soap": (4800, 0, 0), "W. Soap": (4200, 0, 0),
}  # fmt: skip
JUNE_HEADS = {"Vegetables": 15370, "Mutton": 22700, "Fuel": 11780, "Salaries": 11000}

# July: purchases and consumption only; old balances come from June
JULY = {  # item: (purchased_qty, purchased_amount, consumed)
	"Rice": (1000, 49000, 1175), "Jawar": (500, 15000, 631), "S. Oil": (20, 3000, 9), "Daal": (10, 800, 13),
	"Sugar": (20, 1100, 21), "Salt": (25, 500, 2), "Condiments": (0, 0, 2), "Onion": (50, 1000, 10),
	"C. Oil": (20, 4000, 24), "T. Soap": (200, 3200, 200), "W. Soap": (100, 1400, 100), "Tamarind": (0, 0, 1),
}  # fmt: skip
JULY_HEADS = {"Vegetables": 20000, "Mutton": 15000, "Fuel": 12700, "Salaries": 11000}

# September (August not entered): old balances typed on an opening statement
SEPT_OLD = {
	"Rice": (100, 4900), "Jawar": (100, 3000), "S. Oil": (5, 750), "Daal": (10, 800), "Sugar": (10, 550),
	"Tamarind": (2, 100), "Salt": (2, 40), "Condiments": (10, 2000), "Onion": (25, 500), "C. Oil": (50, 10000),
}  # fmt: skip
SEPT = {  # item: (purchased_qty, purchased_amount, consumed)
	"Rice": (400, 19600, 8), "Jawar": (1300, 39000, 42), "S. Oil": (20, 3000, 18), "Daal": (20, 1600, 30),
	"Sugar": (30, 1650, 35), "Tamarind": (30, 2250, 30), "Salt": (3, 61.5, 2), "G. Nut": (30, 3600, 30),
	"Chilli": (30, 4500, 30), "Condiments": (21, 4210.5, 9), "Onion": (50, 1000, 60), "C. Oil": (40, 8000, 30),
	"T. Soap": (300, 4800, 300), "W. Soap": (300, 4200, 300),
}  # fmt: skip
SEPT_HEADS = {"Vegetables": 40000, "Mutton": 30000, "Milk": 5000, "Fuel": 12000, "Salaries": 11000, "GESCOM": 28916}


def run_month(abbr, company, month_no, purchases, consumption, heads, split=True):
	"""Enter a month's purchase invoices, consumption (in two halves) and head payments."""
	purchase(abbr, company, f"2026-{month_no:02d}-02", {i: (q, a) for i, (q, a) in purchases.items() if q})
	food_only = {h: (1, a) for h, a in heads.items() if h in ("Vegetables", "Mutton", "Milk", "Fuel")}
	if food_only:
		purchase(abbr, company, f"2026-{month_no:02d}-03", {h: (1, a) for h, (_q, a) in food_only.items()}, stock=False)
	for head, amount in heads.items():
		if head not in food_only:
			pay_expense(abbr, company, f"2026-{month_no:02d}-04", head, amount)
	first = {i: c // 2 for i, c in consumption.items()}
	consume(company, f"2026-{month_no:02d}-15", first)
	consume(company, f"2026-{month_no:02d}-28", {i: c - first[i] for i, c in consumption.items()})


def statement(company, month, is_opening=0):
	doc = frappe.get_doc({"doctype": "Food Expenditure Statement", "company": company, "month": month, "year": 2026, "is_opening": is_opening})
	doc.fill()
	return doc


def by_item(doc):
	return {l.item_code or l.account.split(" - ")[0]: l for l in doc.lines}


def set_old(doc, olds):
	for line in doc.lines:
		if line.item_code in olds:
			line.old_qty, line.old_amount = olds[line.item_code]
	calculate(doc)


class TestFoodStatement(FrappeTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		cls.company, cls.abbr = "Test Hostel C", "THC"
		make_unit(cls.company, cls.abbr)

	def test_june_then_july(self):
		c, a = self.company, self.abbr
		seed_stock(a, c, "2026-05-31", {i: (v[0], v[1]) for i, v in JUNE.items()})
		run_month(a, c, 6, {i: (v[2], v[3]) for i, v in JUNE.items()}, {i: v[4] for i, v in JUNE.items()}, JUNE_HEADS)

		june = statement(c, "June", is_opening=1)
		set_old(june, {i: (v[0], v[1]) for i, v in JUNE.items()})
		june.fill()  # filling again keeps what was typed
		lines = by_item(june)
		for item, (exp, bq, ba) in JUNE_EXPECTED.items():
			line = lines[item]
			self.assertEqual((line.old_qty, line.old_amount), JUNE[item][:2], item)
			self.assertEqual((line.purchased_qty, line.purchased_amount), JUNE[item][2:4], item)
			self.assertEqual(line.consumed_qty, JUNE[item][4], item)
			self.assertEqual((line.expenditure_amount, line.balance_qty, line.balance_amount), (exp, bq, ba), item)
		for head, amount in JUNE_HEADS.items():
			self.assertEqual(lines[head].purchased_amount, amount, head)
			self.assertEqual(lines[head].expenditure_amount, amount, head)
		self.assertEqual(lines["Milk"].purchased_amount, 0)
		self.assertEqual(lines["GESCOM"].purchased_amount, 0)
		self.assertEqual(
			(june.total_opening, june.total_purchase, june.total_available, june.total_expenditure, june.total_closing),
			(7540, 179150, 186690, 163260, 23430),
		)
		june.insert()
		june.submit()
		self.assertEqual(june.name, "FES-THC-2026-06")

		run_month(a, c, 7, {i: (v[0], v[1]) for i, v in JULY.items()}, {i: v[2] for i, v in JULY.items()}, JULY_HEADS)
		july = statement(c, "July")
		self.assertEqual(july.previous_statement, june.name)
		self.assertEqual(
			(july.total_opening, july.total_purchase, july.total_available, july.total_expenditure, july.total_closing),
			(23430, 137700, 161130, 148865, 12265),
		)
		july.insert()
		july.submit()
		# July of a later month with no statement in between still chains to the last submitted one
		self.assertEqual(statement(c, "September").previous_statement, july.name)

	def test_submit_needs_previous_unless_opening(self):
		doc = statement(self.company, "May")  # nothing is submitted before May
		doc.insert()
		with self.assertRaises(frappe.ValidationError):
			doc.submit()


class TestSeptemberOpening(FrappeTestCase):
	def test_september_opening(self):
		c, a = "Test Hostel D", "THD"
		make_unit(c, a)
		seed_stock(a, c, "2026-08-31", SEPT_OLD)
		run_month(a, c, 9, {i: (v[0], v[1]) for i, v in SEPT.items()}, {i: v[2] for i, v in SEPT.items()}, SEPT_HEADS)
		doc = statement(c, "September", is_opening=1)
		set_old(doc, SEPT_OLD)
		self.assertEqual(doc.total_opening, 22640)
		self.assertEqual(doc.total_purchase, 224388)
		self.assertEqual(doc.total_available, 247028)
		self.assertEqual(doc.total_expenditure, 163988.50)
		# the filed closing is 83,040: the exact figure is 83,039.50 (see slice 2 report)
		self.assertAlmostEqual(doc.total_closing, 83040, delta=0.5)
		doc.insert()
		doc.submit()


class TestConsumption(FrappeTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		cls.company, cls.abbr = "Test Hostel E", "THE"
		make_unit(cls.company, cls.abbr)
		seed_stock(cls.abbr, cls.company, "2026-05-31", {"Rice": (100, 4900), "Sugar": (50, 2750)})

	def test_submit_lowers_bin_and_cancel_restores(self):
		before = bin_qty(self.abbr, "Rice")
		doc = consume(self.company, "2026-06-10", {"Rice": 10, "Sugar": 5})
		self.assertEqual(bin_qty(self.abbr, "Rice"), before - 10)
		entry = frappe.get_doc("Stock Entry", doc.stock_entry)
		self.assertEqual((entry.docstatus, entry.custom_material_consumption), (1, doc.name))
		self.assertEqual(frappe.db.count("GL Entry", {"voucher_no": entry.name}), 0)
		doc.cancel()
		self.assertEqual(bin_qty(self.abbr, "Rice"), before)
		self.assertEqual(frappe.db.get_value("Stock Entry", entry.name, "docstatus"), 2)

	def test_copy_yesterday_and_one_per_day(self):
		consume(self.company, "2026-06-20", {"Rice": 4, "Sugar": 2})
		rows = copy_yesterday(self.company, "2026-06-21")
		self.assertEqual({r.item_code: r.qty for r in rows}, {"Rice": 4, "Sugar": 2})
		self.assertEqual({r.item_code: (r.item_name, r.uom) for r in rows}, {"Rice": ("Rice", "Kg"), "Sugar": ("Sugar", "Kg")})
		self.assertEqual(copy_yesterday(self.company, "2026-06-20"), [])
		with self.assertRaises(frappe.DuplicateEntryError):
			consume(self.company, "2026-06-20", {"Rice": 1})

	def test_non_statement_item_refused(self):
		with self.assertRaises(frappe.ValidationError):
			consume(self.company, "2026-06-25", {"Vegetables": 1})

	def test_closed_period_refused(self):
		frappe.get_doc(
			{
				"doctype": "Accounting Period", "period_name": "THE closed Aug", "company": self.company,
				"start_date": "2026-08-01", "end_date": "2026-08-31",
				"closed_documents": [{"document_type": "Material Consumption", "closed": 1}],
			}
		).insert()
		with self.assertRaises(frappe.ValidationError):
			consume(self.company, "2026-08-05", {"Rice": 1})

	def test_data_entry_can_use_purchase_invoice_and_masters(self):
		user = "store.test@example.com"
		if not frappe.db.exists("User", user):
			frappe.get_doc({"doctype": "User", "email": user, "first_name": "St", "send_welcome_email": 0, "roles": [{"role": "Store"}]}).insert()
		frappe.set_user(user)
		try:
			own = frappe.new_doc("Purchase Invoice")
			own.owner = user
			self.assertTrue(frappe.has_permission("Purchase Invoice", "submit", doc=own))
			for dt, ptype in (("Purchase Invoice", "create"), ("Item", "read"), ("Material Consumption", "create")):
				self.assertTrue(frappe.has_permission(dt, ptype), f"{dt} {ptype}")
			self.assertFalse(frappe.has_permission("Item", "write"))
		finally:
			frappe.set_user("Administrator")
