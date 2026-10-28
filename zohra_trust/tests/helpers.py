import frappe

from zohra_trust.setup.create_unit import create_unit

SCHOOLS = ("Zohra English Medium", "Zohra Kannada Medium")
CLASSES = ("Class 8", "Class 9", "Class 10")


MAX_MARKS = {"Class 8": 250, "Class 9": 480, "Class 10": 625}


def make_class(name, sequence, next_class, max_marks):
	if not frappe.db.exists("Trust Class", name):
		frappe.get_doc(
			{
				"doctype": "Trust Class", "class_name": name, "sequence": sequence, "next_class": next_class,
				"exam_marks": [{"exam": "Mid-term", "max_marks": max_marks}, {"exam": "Final", "max_marks": max_marks}],
			}
		).insert()


def make_masters():
	"""Academic year 2026-27, schools and classes. Safe to call twice."""
	if not frappe.db.exists("Trust Academic Year", "2026-27"):
		frappe.get_doc(
			{"doctype": "Trust Academic Year", "academic_year_name": "2026-27", "start_date": "2026-04-01", "end_date": "2027-03-31"}
		).insert()
	if not frappe.db.exists("Trust Academic Year", "2027-28"):
		frappe.get_doc(
			{"doctype": "Trust Academic Year", "academic_year_name": "2027-28", "start_date": "2027-04-01", "end_date": "2028-03-31"}
		).insert()
	for exam, seq, final in (("Mid-term", 1, 0), ("Final", 2, 1)):
		if not frappe.db.exists("Trust Exam", exam):
			frappe.get_doc({"doctype": "Trust Exam", "exam_name": exam, "sequence": seq, "is_final": final}).insert()
	for school, medium in zip(SCHOOLS, ("English", "Kannada")):
		if not frappe.db.exists("Trust School", school):
			frappe.get_doc({"doctype": "Trust School", "school_name": school, "medium": medium}).insert()
	nxt = None
	for i, cls in reversed(list(enumerate(CLASSES))):
		make_class(cls, i + 8, nxt, MAX_MARKS[cls])
		nxt = cls


def make_unit(company, abbr, strength=150, rate=850):
	make_masters()
	return create_unit(company, abbr, sanctioned_strength=strength, grant_rate=rate)


def make_student(company, n, status="Enrolled", enrollment_date="2026-04-01", academic_year="2026-27", register=None, trust_class=None, guardian=None):
	student = frappe.get_doc(
		{
			"doctype": "Trust Student", "student_name": f"Girl {company[-1]}{n}", "home_unit": company, "admission_date": "2026-04-01",
			"has_guardian": 1 if guardian else 0, "guardians": [{"guardian_name": guardian, "relation": "Father"}] if guardian else [],
		}
	).insert()
	return frappe.get_doc(
		{
			"doctype": "Student Enrollment",
			"student": student.name,
			"academic_year": academic_year,
			"unit": company,
			"school": SCHOOLS[0] if n <= 60 else SCHOOLS[1],
			"trust_class": trust_class or CLASSES[n % 3],
			"register_sl_no": register or n,
			"enrollment_date": enrollment_date,
			"status": status,
		}
	).insert()


def make_attendance(company, month, year=2026, working_days=(24, 22)):
	return frappe.get_doc(
		{
			"doctype": "Boarding Attendance",
			"company": company,
			"month": month,
			"year": year,
			"school_days": [
				{"school": SCHOOLS[0], "working_days": working_days[0]},
				{"school": SCHOOLS[1], "working_days": working_days[1]},
			],
		}
	)


def stock_wh(abbr):
	return f"Hostel Store - {abbr}"


def seed_stock(abbr, company, date, rows):
	"""Material Receipt of opening quantities. rows: {item: (qty, amount)}."""
	entry = frappe.get_doc(
		{
			"doctype": "Stock Entry",
			"stock_entry_type": "Material Receipt",
			"company": company,
			"posting_date": date,
			"set_posting_time": 1,
			"to_warehouse": stock_wh(abbr),
			"items": [
				{"item_code": i, "qty": q, "basic_rate": a / q, "t_warehouse": stock_wh(abbr)} for i, (q, a) in rows.items() if q
			],
		}
	)
	entry.insert()
	entry.submit()


def purchase(abbr, company, date, rows, stock=True):
	"""Cash Purchase Invoice. rows: {item: (qty, amount)}."""
	total = sum(a for _q, a in rows.values())
	doc = frappe.get_doc(
		{
			"doctype": "Purchase Invoice",
			"company": company,
			"supplier": "Cash purchase",
			"posting_date": date,
			"bill_date": date,
			"set_posting_time": 1,
			"update_stock": 1 if stock else 0,
			"set_warehouse": stock_wh(abbr) if stock else None,
			"is_paid": 1,
			"mode_of_payment": "Cash",
			"cash_bank_account": f"Cash - {abbr}",
			"paid_amount": total,
			"items": [{"item_code": i, "qty": q, "rate": a / q, "warehouse": stock_wh(abbr) if stock else None} for i, (q, a) in rows.items()],
		}
	)
	doc.insert()
	doc.submit()
	return doc


def pay_expense(abbr, company, date, account, amount):
	"""Journal Entry Dr expense account, Cr cash. Stands in for a Cash Bank Voucher."""
	cost_center = frappe.get_cached_value("Company", company, "cost_center")
	entry = frappe.get_doc(
		{
			"doctype": "Journal Entry",
			"company": company,
			"posting_date": date,
			"accounts": [
				{"account": f"{account} - {abbr}", "debit_in_account_currency": amount, "cost_center": cost_center},
				{"account": f"Cash - {abbr}", "credit_in_account_currency": amount, "cost_center": cost_center},
			],
		}
	)
	entry.insert()
	entry.submit()


def consume(company, date, quantities):
	doc = frappe.get_doc(
		{
			"doctype": "Material Consumption",
			"company": company,
			"posting_date": date,
			"items": [{"item_code": i, "qty": q} for i, q in quantities.items() if q],
		}
	)
	doc.insert()
	doc.submit()
	return doc


def bin_qty(abbr, item):
	return frappe.db.get_value("Bin", {"item_code": item, "warehouse": stock_wh(abbr)}, "actual_qty") or 0
