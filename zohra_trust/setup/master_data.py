"""The masters of the Zohra Minority Girls Hostel, so a new site can be tested straight away.

    bench --site <site> execute zohra_trust.setup.master_data.load
    bench --site <site> execute zohra_trust.setup.master_data.load_students --kwargs "{'csv_path': '/path/girls.csv'}"
    bench --site <site> execute zohra_trust.setup.master_data.load_opening_balances --kwargs "{'cash': 682, 'bank': 634446.84}"

`load` is safe to run again: whatever already exists is left as the user set it, except the officer bearers
and the typed texts, which are set to the values below only when they are still empty.
No student is in this file: the girls are children, so their names come from a file that is not in Git.
"""

import csv

import frappe

from zohra_trust.setup.create_unit import create_unit
from zohra_trust.setup.seed_classes import seed_classes

COMPANY, ABBR = "Zohra Minority Girls Hostel", "ZMH"
SCHOOLS = (("Zohra English Medium", "English"), ("Zohra Kannada Medium", "Kannada"))
ACADEMIC_YEARS = (("2026-27", "2026-04-01", "2027-03-31"), ("2027-28", "2027-04-01", "2028-03-31"))
TRUST_NAME, REGISTRATION_NO = "ZOHRA WOMEN & CHILDREN CHARITABLE & WELFARE TRUST", "16/79-80"
ADDRESS = "Near Masjid-e-Umar Old Jewargi Road, Kalaburagi-585102"

# (name, designation, qualification, phone, address) in the order of the filed letterhead
OFFICERS = (
	("Tasneem Fatima", "President", "B.A", "9742920793", "Kalaburagi"),
	("Md. Azam Ali", "Secretary", "B.Com", "9448041586", "Kalaburagi"),
	("Md. Iqbal Ali", "Joint Secretary", "B.Com", "9845203533", "Kalaburagi"),
	("Dr. Md. Ateeq Ur Rahman", "Trustee", "B.E, M.Tech, Ph D, MISTE, MIE, PRINCIPAL, Shadan College of Engg & Technology, Hyderabad", "8143339722", "Hyderabad"),
	("Md. Abubaker", "Trustee", "D.Arch", "7019977008", "Kalaburagi"),
	("Dr. Omer Mauzam Ali", "Trustee", "MBBS, DIP in emergency Medicine", "", "Kalaburagi"),
	("Sabiha Kauser", "Trustee", "Social worker", "8296202820", "Kalaburagi"),
)  # fmt: skip
STAFF = (("Najmunnisa", "House Mother", "B.A"), ("Shabnam", "House Mother", "PUC"), ("Shakeela", "Cook", "10th"), ("Asma", "Asst Cook", "PUC"))

LETTER = """<p>To,<br><b>The District Minority officer,<br>Kalaburagi</b></p>
<p style="margin-left:40px"><b>Sub:</b> Submission of accounts and necessary paper for the period {{ from_date }} to {{ to_date }} towards maintenance grant of Zohra minority girls' hostel.</p>
<p>Dear Sir,</p>
<p>With reference to the above we are here with submitting all the required papers for the release of grant towards maintenance of the Hostel.</p>
<p style="text-align:center"><b>Thanking you we remain</b></p>
<p style="text-align:right"><b>Yours faithfully</b></p>"""
APPENDIX_H = """<h2 style="text-align:center;text-decoration:underline">APPENDIX- H</h2>
<h3 style="text-align:center;text-decoration:underline">RULES 12 FORM OF APPLICATION FOR GRANT IN AID TO BE SUBMITTED TO THE CHIEF SECRETARY ZILLAH PANCHAYAT, GULBARGA</h3>
<table style="width:100%;border-collapse:collapse;font-size:16px" cellpadding="6">
<tr><td>1.</td><td>Name and Address of Institute/Hostel</td><td>:</td><td>ZOHRA MINORITY GIRLS HOSTEL<br>Old Jewargi Road, Opp. PWD Qrt. Gulbarga - 585 102.</td></tr>
<tr><td>2.</td><td>Name of Trust</td><td>:</td><td>Zohra Women &amp; Children Charitable Welfare Trust</td></tr>
<tr><td>3.</td><td>Name and Address of the Secretary</td><td>:</td><td>Mrs. Basheerunnissa Begum<br>Mahetab Ali Compound, Aiwan-e-Shahi Colony, Gulbarga - 585 102.</td></tr>
<tr><td>4.</td><td>a) No. and date of the order recognition by the backward classes Dept.</td><td>:</td><td>Not Applicable</td></tr>
<tr><td></td><td>b) Period of which the recognition</td><td>:</td><td>18/08/1997-98/12/04/99, 01/01/05</td></tr>
<tr><td>5.</td><td>a) Sanctioned strength at the time of recognition<br>b) Strength and attendance as on 31st March</td><td>:</td><td>150 inmates</td></tr>
<tr><td>6.</td><td>Approved expenditure for the Hostel and amount actually spent as per audit statement of A/c</td><td>:</td><td>Enclosed</td></tr>
<tr><td>7.</td><td>Amount of grant sanctioned during the previous year and during the year budget estimate for the current year should be enclosed</td><td>:</td><td>Enclosed</td></tr></table>
<p><b>Note:</b> This application for grant should be accompanied by the audit statement of account and all other relevant documents as the facilities the sanction of grant by the competent authority.</p>
<h3 style="text-align:center;text-decoration:underline">DECLARATION</h3>
<p>On behalf of the management the institution I/we hereby declare that the condition of the recognition and grant in prepared to submit all the account of the hostel. In inspection and to furnish the returns as may be required by the Dept. no money will be collected from the boarders of the Hostel towards their boarding &amp; lodging.</p>"""


def make_masters():
	"""Academic years, schools and the classes with their exams. Safe to run twice."""
	for name, start, end in ACADEMIC_YEARS:
		if not frappe.db.exists("Trust Academic Year", name):
			frappe.get_doc({"doctype": "Trust Academic Year", "academic_year_name": name, "start_date": start, "end_date": end}).insert()
	for school, medium in SCHOOLS:
		if not frappe.db.exists("Trust School", school):
			frappe.get_doc({"doctype": "Trust School", "school_name": school, "medium": medium}).insert()
	seed_classes()


def load(company=COMPANY, abbr=ABBR):
	"""Everything except the girls and the opening balances."""
	if not frappe.db.exists("Fiscal Year", "2025-2026"):
		frappe.get_doc({"doctype": "Fiscal Year", "year": "2025-2026", "year_start_date": "2025-04-01", "year_end_date": "2026-03-31"}).insert()
	make_masters()
	set_trust(TRUST_NAME, REGISTRATION_NO, OFFICERS)
	create_unit(company, abbr, sanctioned_strength=150, grant_rate=850, effective_from="2026-04-01")
	profile = frappe.get_doc("Trust Unit Profile", company)
	for field, value in (("address", ADDRESS), ("letter_text", LETTER), ("appendix_h_text", APPENDIX_H)):
		if not profile.get(field):
			profile.set(field, value)
	profile.save()
	for name, designation, qualification in STAFF:
		add_staff(company, name, designation, qualification)
	print(f"Masters of {company} are ready.")


def set_trust(trust_name, registration_no, officers):
	settings = frappe.get_single("Trust Settings")
	if not settings.trust_name:
		settings.trust_name = trust_name
	if not settings.registration_no:
		settings.registration_no = registration_no
	if not settings.officer_bearers:
		for order, (name, designation, qualification, phone, address) in enumerate(officers, 1):
			settings.append(
				"officer_bearers",
				{"member_name": name, "designation": designation, "qualification": qualification, "phone": phone, "address": address, "sort_order": order, "is_active": 1},
			)
	if not settings.current_academic_year:
		settings.current_academic_year = ACADEMIC_YEARS[0][0]
	settings.save()


def add_staff(company, name, designation, qualification):
	if frappe.db.exists("Employee", {"company": company, "first_name": name}):
		return
	frappe.get_doc(
		{
			"doctype": "Employee", "first_name": name, "gender": "Female", "date_of_birth": "1985-01-01", "date_of_joining": "2020-01-01", "company": company,
			"status": "Active", "designation": frappe.get_doc({"doctype": "Designation", "designation_name": designation}).insert(ignore_if_duplicate=True).name,
			"education": [{"qualification": qualification}],
		}
	).insert()


def load_students(csv_path, company=COMPANY, academic_year="2026-27", enrollment_date="2026-04-01"):
	"""Girls from a CSV with the columns name, class, school. Register numbers follow the file order; a girl already in the hostel is skipped."""
	with open(csv_path, newline="", encoding="utf-8") as handle:
		rows = [(r["name"], int(r["class"]), r["school"]) for r in csv.DictReader(handle)]
	return add_students(rows, company, academic_year, enrollment_date)


def add_students(rows, company=COMPANY, academic_year="2026-27", enrollment_date="2026-04-01"):
	"""rows: (name, class number, school). Returns how many were added."""
	added = 0
	existing = frappe.db.count("Student Enrollment", {"unit": company, "academic_year": academic_year})
	for n, (name, klass, school) in enumerate(rows, existing + 1):
		name = name.strip()
		if frappe.db.exists("Trust Student", {"student_name": name, "home_unit": company}):
			continue
		student = frappe.get_doc({"doctype": "Trust Student", "student_name": name, "home_unit": company, "admission_date": enrollment_date}).insert()
		frappe.get_doc(
			{
				"doctype": "Student Enrollment", "student": student.name, "academic_year": academic_year, "unit": company, "school": school.strip(),
				"trust_class": f"Class {int(klass)}", "register_sl_no": n, "enrollment_date": enrollment_date, "status": "Enrolled",
			}
		).insert()
		added += 1
	print(f"{added} girls added to {company}.")
	return added


def load_opening_balances(cash, bank, company=COMPANY, abbr=ABBR, as_on="2026-03-31"):
	"""Cash and bank on the day before the first month, from the paper books (Temporary Opening is the other side)."""
	remark = f"Opening balances of {as_on}"
	if frappe.db.exists("Journal Entry", {"company": company, "user_remark": remark, "docstatus": 1}):
		return
	entry = frappe.get_doc(
		{
			"doctype": "Journal Entry", "company": company, "posting_date": as_on, "user_remark": remark,
			"accounts": [
				{"account": f"Cash - {abbr}", "debit_in_account_currency": cash},
				{"account": f"Bank - {abbr}", "debit_in_account_currency": bank},
				{"account": f"Temporary Opening - {abbr}", "credit_in_account_currency": cash + bank},
			],
		}
	)
	entry.insert()
	entry.submit()
	print("Opening balances entered.")
