"""One unit with two months of everything the half-yearly report prints. For the report page tests."""

import frappe

from zohra_trust.tests.helpers import consume, make_attendance, make_student, make_unit, pay_expense, purchase, seed_stock
from zohra_trust.tests.test_slice5 import mark, sheet


def make_pack_data(COMPANY, ABBR):
	"""June and July: attendance, purchases, consumption, salaries, food statements; a Final result sheet; letterhead data."""
	make_unit(COMPANY, ABBR)
	settings = frappe.get_doc("Trust Settings")
	settings.trust_name = "Zohra Women & Children Charitable & Welfare Trust"
	settings.registration_no = "16/79-80"
	settings.officer_bearers = []
	for order, (name, designation) in enumerate((("Tasneem Fatima", "President"), ("Md. Azam Ali", "Secretary")), 1):
		settings.append("officer_bearers", {"member_name": name, "designation": designation, "qualification": "B.A", "phone": "9742920793", "sort_order": order, "is_active": 1})
	settings.append("officer_bearers", {"member_name": "Retired Member", "designation": "Trustee", "sort_order": 3, "is_active": 0})
	settings.save()
	profile = frappe.get_doc("Trust Unit Profile", COMPANY)
	profile.address = "Old Jewargi Road, Kalaburagi"
	profile.letter_text = "<p>Sub: accounts for the period {{ from_date }} to {{ to_date }}</p>"
	profile.appendix_h_text = "<p>Name of Trust: Zohra Trust</p>"
	profile.save()
	for name, designation, qualification in (("Najmunnisa", "House Mother", "B.A"), ("Shakeela", "Cook", "10th")):
		frappe.get_doc(
			{
				"doctype": "Employee", "first_name": name, "gender": "Female", "date_of_birth": "1990-01-01", "date_of_joining": "2020-01-01",
				"company": COMPANY, "status": "Active", "designation": frappe.get_doc({"doctype": "Designation", "designation_name": designation}).insert(ignore_if_duplicate=True).name,
				"education": [{"qualification": qualification}],
			}
		).insert()
	girls = [make_student(COMPANY, n, trust_class="Class 8" if n < 3 else "Class 10", guardian="Father One" if n == 1 else None) for n in (1, 2, 3)]
	frappe.db.set_value("Student Enrollment", girls[2].name, "school", "Zohra Kannada Medium")  # girl 3 attends the other school
	seed_stock(ABBR, COMPANY, "2026-05-31", {"Rice": (50, 2450)})
	for month_no, month in ((6, "June"), (7, "July")):
		attendance = make_attendance(COMPANY, month)
		attendance.fill_rows()
		attendance.insert()
		attendance.submit()
		purchase(ABBR, COMPANY, f"2026-{month_no:02d}-05", {"Rice": (100, 4900)})
		consume(COMPANY, f"2026-{month_no:02d}-20", {"Rice": 60})
		pay_expense(ABBR, COMPANY, f"2026-{month_no:02d}-25", "Salaries", 11000)
		statement = frappe.get_doc({"doctype": "Food Expenditure Statement", "company": COMPANY, "month": month, "year": 2026, "is_opening": 1 if month == "June" else 0})
		statement.fill()
		statement.insert()
		statement.submit()
	final = sheet(COMPANY)
	mark(final, {r.student_name: (300, "Pass", None, "Other" if r.trust_class == "Class 10" else None) for r in final.rows})
	final.insert()
	final.submit()
	return girls
