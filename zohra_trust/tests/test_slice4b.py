"""Slice 4, phase b: the Report Pack, its page list and the merged PDF."""

import io

import frappe
from frappe.tests.utils import FrappeTestCase
from PIL import Image
from pypdf import PdfReader

from zohra_trust.api.report_pack import pack_info, pack_pdf
from zohra_trust.tests.pack_data import make_pack_data
from zohra_trust.utils.report_pack import default_sections, info, pdf_bytes
from zohra_trust.utils.report_pages import build_pages, to_pdf

COMPANY, ABBR = "Test Hostel V", "THV"


def upload(name, content):
	return frappe.get_doc({"doctype": "File", "file_name": name, "content": content, "is_private": 1}).insert().file_url


def png_bytes(width, height):
	out = io.BytesIO()
	Image.new("RGB", (width, height), (200, 220, 240)).save(out, "PNG")
	return out.getvalue()


def pack(**kw):
	doc = frappe.get_doc({"doctype": "Report Pack", "company": COMPANY, "from_date": "2026-04-01", "to_date": "2026-09-30", **kw})
	return doc.insert()


def sizes(pdf):
	return [(round(float(p.mediabox.width)), round(float(p.mediabox.height))) for p in PdfReader(io.BytesIO(pdf)).pages]


class TestReportPack(FrappeTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		make_pack_data(COMPANY, ABBR)
		cls.generated, _w = build_pages(COMPANY, "2026-04-01", "2026-09-30")

	def test_new_pack_lists_the_standard_pages_in_filing_order(self):
		doc = pack()
		self.assertEqual([r.section for r in doc.pages], default_sections())
		self.assertTrue(all(r.include for r in doc.pages))
		self.assertTrue(doc.name.startswith("RPK-"))

	def test_refused_input(self):
		with self.assertRaises(frappe.ValidationError):
			pack(from_date="2026-09-30", to_date="2026-04-01")
		with self.assertRaises(frappe.ValidationError):  # a section twice
			pack(pages=[{"section": "Letter", "include": 1}, {"section": "Letter", "include": 1}])
		with self.assertRaises(frappe.ValidationError):  # uploaded page without a file
			pack(pages=[{"section": "Uploaded page", "title": "CA balance sheet", "include": 1}])
		with self.assertRaises(frappe.ValidationError):  # uploaded page without a title
			pack(pages=[{"section": "Uploaded page", "file": upload("a.pdf", to_pdf("<p>x</p>")), "include": 1}])
		with self.assertRaises(frappe.ValidationError):  # a file type that cannot be merged
			pack(pages=[{"section": "Uploaded page", "title": "Sheet", "file": upload("a.txt", b"hello"), "include": 1}])

	def test_info_names_every_page_with_its_month_and_the_warnings(self):
		listed = info(pack())
		titles = [p["title"] for p in listed["pages"]]
		self.assertEqual(len(titles), len(self.generated))
		self.assertIn("Food expenditure statement – June 2026", titles)
		self.assertTrue(any(t == "School: College attendance register – July 2026" for t in titles))
		self.assertTrue(any("August 2026" in w for w in listed["warnings"]))

	def test_merged_pdf_has_one_pdf_page_per_page_in_order_and_keeps_landscape(self):
		doc = pack()
		sized = sizes(pdf_bytes(doc))
		expected = []
		for page in self.generated:
			expected += [(842, 595) if page["orientation"] == "Landscape" else (595, 842)] * len(PdfReader(io.BytesIO(to_pdf(page["html"], page["orientation"]))).pages)
		self.assertEqual(sized, expected)
		self.assertIn((842, 595), sized)
		self.assertIn((595, 842), sized)

	def test_excluded_section_is_left_out(self):
		doc = pack()
		full = len(PdfReader(io.BytesIO(pdf_bytes(doc))).pages)
		for row in doc.pages:
			if row.section == "Food expenditure statements":
				row.include = 0
		doc.save()
		self.assertEqual(len(PdfReader(io.BytesIO(pdf_bytes(doc))).pages), full - 2)  # June and July statements
		self.assertNotIn("Food expenditure statement – June 2026", [p["title"] for p in info(doc)["pages"]])

	def test_uploaded_pdf_and_images_go_in_at_their_row(self):
		ca_pdf = to_pdf("<h1>CA balance sheet</h1>")
		ca_url = upload("ca.pdf", ca_pdf)
		plan_url = upload("plan.png", png_bytes(900, 500))  # wider than tall: lands on a landscape page
		sections = default_sections()
		pages = [{"section": s, "include": 1} for s in sections[:3]]
		pages.append({"section": "Uploaded page", "title": "CA balance sheet", "file": ca_url, "include": 1})
		pages += [{"section": s, "include": 1} for s in sections[3:]]
		pages.append({"section": "Uploaded page", "title": "Building plan", "file": plan_url, "include": 1})
		doc = pack(pages=pages)
		titles = [p["title"] for p in info(doc)["pages"]]
		self.assertEqual(titles[3], "CA balance sheet")  # right after letter, receipts and abstract
		self.assertEqual(titles[-1], "Building plan")
		merged = pdf_bytes(doc)
		self.assertEqual(len(PdfReader(io.BytesIO(merged)).pages), len(self.generated) + 2)
		self.assertEqual(sizes(merged)[-1], (842, 595))  # the plan
		text = " ".join(PdfReader(io.BytesIO(merged)).pages[3].extract_text().split())
		self.assertIn("CA balance sheet", text)

	def test_a_missing_uploaded_file_is_a_warning(self):
		url = upload("gone.pdf", to_pdf("<p>x</p>"))
		doc = pack(pages=[{"section": "Letter", "include": 1}, {"section": "Uploaded page", "title": "Signed scan", "file": url, "include": 1}])
		frappe.get_doc("File", {"file_url": url}).delete()
		self.assertTrue(any("Signed scan" in w for w in info(doc)["warnings"]))

	def test_section_with_no_data_is_reported(self):
		doc = pack(from_date="2026-08-01", to_date="2026-08-31")  # nothing was entered for August
		warnings = info(doc)["warnings"]
		self.assertTrue(any("Nothing to print for Food expenditure statements" in w for w in warnings))

	def test_merged_pdf_is_kept_so_download_after_preview_is_instant(self):
		from unittest import mock

		memory = {}  # stands in for Redis, which the test runner does not keep values in

		doc = pack(pages=[{"section": "Letter", "include": 1}, {"section": "Abstract statement of attendance", "include": 1}])
		with mock.patch("zohra_trust.utils.report_pack.kept", memory.get), mock.patch("zohra_trust.utils.report_pack.keep", memory.__setitem__), mock.patch("zohra_trust.utils.report_pack.to_pdf", wraps=to_pdf) as render:
			first = pdf_bytes(doc)
			rendered = render.call_count
			second = pdf_bytes(doc)
			self.assertEqual(render.call_count, rendered)  # the second call rendered nothing
			self.assertEqual(rendered, 2)
			self.assertEqual(first, second)
			doc.pages[1].include = 0  # a different pack is a different PDF, not the kept one
			self.assertEqual(len(PdfReader(io.BytesIO(pdf_bytes(doc))).pages), 1)
			self.assertEqual(len(PdfReader(io.BytesIO(first)).pages), 2)

	def test_endpoints_return_info_and_a_pdf(self):
		doc = pack()
		self.assertEqual(pack_info(doc.name)["pages"], info(doc)["pages"])
		pack_pdf(doc.name)
		self.assertEqual(frappe.local.response.type, "pdf")
		self.assertEqual(frappe.local.response.filename, f"{doc.name}.pdf")
		self.assertTrue(frappe.local.response.filecontent.startswith(b"%PDF"))
