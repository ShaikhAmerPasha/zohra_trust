"""Pages of the half-yearly report, built from the records.

build_pages(company, from_date, to_date) returns (pages, warnings). A page is a dict with
key, title, orientation and html; warnings are things the office should fix before filing
(for example a month with no submitted statement). The Report Pack merges the pages into one PDF.
"""

import re

import frappe
from frappe import _
from frappe.utils import add_months, flt, formatdate, getdate
from frappe.utils.pdf import get_pdf

from zohra_trust.trust_operations.report.receipts_and_payments_account.receipts_and_payments_account import execute as receipts_payments
from zohra_trust.utils.dates import MONTHS, month_bounds
from zohra_trust.utils.sanction import get_unit_sanction

TEMPLATE_DIR = "zohra_trust/templates/report_pages"
PORTRAIT, LANDSCAPE = "Portrait", "Landscape"

# The enclosures as the letter lists them (spec 10.1).
ENCLOSURES = (
	"Appendix – H", "List of officer bearer", "Boarding attendance", "Food expenditure statement",
	"List of staff members", "Grant bill", "Abstract of boarding and attendance",
)  # fmt: skip

# Rows of the Receipts and Payments Account that always print, as the filed page has them (spec 10.2).
RECEIPT_ROWS = ("Loan from Zohra trust", "Bank interest", "Govt. grant received")
# No Food Expenditure Statement or Boarding Attendance is made for these months (spec section 7), so
# their absence is not a warning.
UNEXPECTED_MONTHS = ("April", "May")
FOOD_ROWS = 24  # the filed sheet is numbered to 24; unused rows print blank
PAYMENT_ROWS = ("Food", "Fuel", "Detergent", "Salaries", "Education", "Miscellaneous", "Transfer to Zohra trust")


def inr(value, always_decimals=False):
	"""Indian digit grouping (12,30,000). Paise only when there are any."""
	if value in (None, ""):
		return ""
	value = flt(value, 2)
	text = f"{abs(value):.2f}"
	whole, paise = text.split(".")
	if len(whole) > 3:
		head, tail = whole[:-3], whole[-3:]
		groups = []
		while len(head) > 2:
			groups.insert(0, head[-2:])
			head = head[:-2]
		if head:
			groups.insert(0, head)
		whole = ",".join(groups + [tail])
	out = whole if paise == "00" and not always_decimals else f"{whole}.{paise}"
	return f"-{out}" if value < 0 else out


def qty(value):
	value = flt(value, 3)
	return "" if value == 0 else f"{value:g}"


def months_between(from_date, to_date):
	"""[(month name, year)] from the month of from_date to the month of to_date."""
	cursor, last, out = getdate(from_date).replace(day=1), getdate(to_date), []
	while cursor <= last:
		out.append((MONTHS[cursor.month - 1], cursor.year))
		cursor = add_months(cursor, 1)
	return out


def warn_missing(warnings, message, month, year):
	if month not in UNEXPECTED_MONTHS:
		warnings.append(_(message).format(month, year))


def unit_context(company, from_date, to_date):
	profile = frappe.db.get_value(
		"Trust Unit Profile", company, ["address", "letter_text", "appendix_h_text"], as_dict=True
	) or frappe._dict()
	settings = frappe.get_single("Trust Settings")
	officers = sorted((o for o in settings.officer_bearers if o.is_active), key=lambda o: (o.sort_order or 0, o.idx))
	return frappe._dict(
		company=company,
		unit_name="ZOHRA MINORITY GIRLS HOSTEL",
		address=profile.get("address") or "",
		letter_text=profile.get("letter_text") or "",
		appendix_h_text=profile.get("appendix_h_text") or "",
		trust_name=settings.trust_name or "",
		registration_no=settings.registration_no or "",
		officers=officers,
		from_date=formatdate(from_date, "dd-mm-yyyy"),
		to_date=formatdate(to_date, "dd-mm-yyyy"),
		period=f"{formatdate(from_date, 'dd-mm-yyyy')} to {formatdate(to_date, 'dd-mm-yyyy')}",
	)


KANNADA_RUN = re.compile(r"[\u0C80-\u0CFF]+(?:[ \t.,:;/()–-]*[\u0C80-\u0CFF]+)*")
TEXT_BETWEEN_TAGS = re.compile(r">([^<>]+)<")
NOT_VISIBLE = re.compile(r"(<(?:style|script|title)\b.*?</(?:style|script|title)>)", re.S | re.I)


def wrap_kannada(html):
	"""Put every run of Kannada text in its own span (class kn).

	wkhtmltopdf 0.12.6 (unpatched Qt) crashes with a segmentation fault when a single text run mixes
	Latin and Kannada glyphs. Runs in separate spans, each with its own font, render correctly. Only
	text between tags is touched, never attributes, CSS, scripts or the title.
	"""

	def wrap(text):
		return TEXT_BETWEEN_TAGS.sub(lambda m: ">" + KANNADA_RUN.sub(lambda k: f'<span class="kn">{k.group(0)}</span>', m.group(1)) + "<", text)

	parts = NOT_VISIBLE.split(html)  # odd items are the blocks to leave alone
	return "".join(part if n % 2 else wrap(part) for n, part in enumerate(parts))


def render(template, **context):
	html = frappe.render_template(
		f"{TEMPLATE_DIR}/{template}.html", {"inr": inr, "qty": qty, "enclosures": ENCLOSURES, **context}
	)
	return wrap_kannada(html)


def page(key, title, template, orientation=PORTRAIT, **context):
	return {"key": key, "title": title, "orientation": orientation, "html": render(template, title=title, **context)}


def letter_page(ctx):
	text = frappe.render_template(ctx.letter_text, {"unit": ctx, "from_date": ctx.from_date, "to_date": ctx.to_date, "period": ctx.period})
	return [page("letter", _("Letter"), "letter", ctx=ctx, body=text)]


def officer_page(ctx):
	return [page("officer_bearers", _("List of officer bearer"), "officer_bearers", ctx=ctx)]


def appendix_page(ctx):
	return [page("appendix_h", _("Appendix – H"), "appendix_h", ctx=ctx)]


def receipts_payments_page(ctx, from_date, to_date):
	_columns, rows = receipts_payments({"company": ctx.company, "from_date": from_date, "to_date": to_date})
	by_label = {r["particulars"]: r for r in rows}
	known = {"Opening balance (Cash)", "Opening balance (Bank)", "Closing balance (Cash)", "Closing balance (Bank)", "Total", *RECEIPT_ROWS, *PAYMENT_ROWS}
	extra_receipts = [r["particulars"] for r in rows if r["particulars"] not in known and r.get("receipts")]
	extra_payments = [r["particulars"] for r in rows if r["particulars"] not in known and r.get("payments")]

	def value(label, column):
		return (by_label.get(label) or {}).get(column)

	receipts = [(label, value(label, "receipts")) for label in (*RECEIPT_ROWS, *extra_receipts)]
	payments = [(label, value(label, "payments")) for label in (*PAYMENT_ROWS, *extra_payments)]
	totals = by_label.get("Total") or {}
	return [
		page(
			"receipts_payments", _("Receipts and payments account for the period"), "receipts_payments", ctx=ctx,
			opening_cash=value("Opening balance (Cash)", "receipts"), opening_bank=value("Opening balance (Bank)", "receipts"),
			closing_cash=value("Closing balance (Cash)", "payments"), closing_bank=value("Closing balance (Bank)", "payments"),
			receipts=receipts, payments=payments, total_receipts=totals.get("receipts"), total_payments=totals.get("payments"),
		)
	]


def submitted(doctype, filters, fields=None, order_by="creation asc"):
	return frappe.get_all(doctype, filters={**filters, "docstatus": 1}, fields=fields or ["name"], order_by=order_by)


def abstract_page(ctx, from_date, to_date, warnings):
	rows = []
	for month, year in months_between(from_date, to_date):
		sheet = submitted(
			"Boarding Attendance", {"company": ctx.company, "month": month, "year": year},
			["name", "sanctioned_strength", "total_hostel_days", "total_school_days_present"],
		)
		if not sheet:
			warn_missing(warnings, "No submitted Boarding Attendance for {0} {1}", month, year)
			continue
		rows.append(frappe._dict(month=f"{month} {year}", **sheet[0]))
	if not rows:
		return []
	strength = rows[0].sanctioned_strength
	return [page("abstract", _("Abstract statement of attendance"), "abstract", ctx=ctx, rows=rows, strength=strength)]


def food_statement_pages(ctx, from_date, to_date, warnings):
	pages = []
	for month, year in months_between(from_date, to_date):
		found = submitted("Food Expenditure Statement", {"company": ctx.company, "month": month, "year": year})
		if not found:
			warn_missing(warnings, "No submitted Food Expenditure Statement for {0} {1}", month, year)
			continue
		doc = frappe.get_doc("Food Expenditure Statement", found[0].name)
		sanction = get_unit_sanction(ctx.company, doc.period_end)
		items = [l for l in doc.lines if l.line_type == "Item"]
		heads = [l for l in doc.lines if l.line_type != "Item"]  # all amount-only rows print, empty or not, as on the filed sheet
		pages.append(
			page(
				f"food_{year}_{month}", _("Food expenditure statement"), "food_statement", LANDSCAPE, ctx=ctx, doc=doc,
				strength=sanction.strength if sanction else "", month=month, year=year, items=items,
				heads=heads, blanks=max(0, FOOD_ROWS - len(items) - len(heads)),
			)
		)
	return pages


def attendance_register_pages(ctx, from_date, to_date, warnings):
	"""One register per school and month: the days each girl's school ran and she attended."""
	pages = []
	for month, year in months_between(from_date, to_date):
		sheet = submitted("Boarding Attendance", {"company": ctx.company, "month": month, "year": year})
		if not sheet:
			continue  # the abstract already warned
		doc = frappe.get_doc("Boarding Attendance", sheet[0].name)
		for school in sorted({r.school for r in doc.rows if r.school}):
			rows = [r for r in doc.rows if r.school == school]
			pages.append(
				page(
					f"register_{year}_{month}_{school}", _("School: College attendance register"), "attendance_register", ctx=ctx,
					school=school, month=month, year=year, rows=rows,
				)
			)
	return pages


def staff_page(ctx, warnings):
	staff = frappe.get_all(
		"Employee", filters={"company": ctx.company, "status": "Active"}, fields=["name", "employee_name", "designation"], order_by="creation asc"
	)
	if not staff:
		warnings.append(_("No active Employee records for {0}").format(ctx.company))
		return []
	for member in staff:
		member.qualification = frappe.db.get_value(
			"Employee Education", {"parent": member.name, "parenttype": "Employee"}, "qualification", order_by="idx asc"
		) or ""
	return [page("staff_list", _("List of staff"), "staff_list", ctx=ctx, staff=staff)]


def result_sheet_page(ctx, to_date, warnings):
	sheets = submitted(
		"Result Sheet of Inmates", {"company": ctx.company}, ["name", "academic_year", "exam_date", "exam"], order_by="exam_date desc, creation desc"
	)
	year = frappe.db.get_value("Trust Academic Year", {"start_date": ["<=", to_date], "end_date": [">=", to_date]}, "name")
	sheets = [s for s in sheets if s.academic_year == year] if year else sheets
	if not sheets:
		warnings.append(_("No submitted Result Sheet of Inmates"))
		return []
	doc = frappe.get_doc("Result Sheet of Inmates", sheets[0].name)
	return [page("result_sheet", _("Result sheet of inmates"), "result_sheet", ctx=ctx, doc=doc)]


def build_pages(company, from_date, to_date):
	"""All generated pages in filing order, and the warnings."""
	warnings = []
	ctx = unit_context(company, from_date, to_date)
	pages = [
		*letter_page(ctx),
		*receipts_payments_page(ctx, from_date, to_date),
		*abstract_page(ctx, from_date, to_date, warnings),
		*food_statement_pages(ctx, from_date, to_date, warnings),
		*appendix_page(ctx),
		*officer_page(ctx),
		*staff_page(ctx, warnings),
		*result_sheet_page(ctx, to_date, warnings),
		*attendance_register_pages(ctx, from_date, to_date, warnings),
	]
	return pages, warnings


def to_pdf(html, orientation=PORTRAIT):
	return get_pdf(html, {"page-size": "A4", "orientation": orientation, "margin-top": "12mm", "margin-bottom": "12mm", "margin-left": "10mm", "margin-right": "10mm"})
