"""The Report Pack: generated pages and uploaded pages merged into one PDF, in the order the pack lists."""

import base64
import hashlib
import io
import os
from concurrent.futures import ThreadPoolExecutor

import frappe
from frappe import _
from pypdf import PdfReader, PdfWriter

from zohra_trust.utils.report_pages import LANDSCAPE, PORTRAIT, build_pages, to_pdf

UPLOADED = "Uploaded page"
ALLOWED_UPLOADS = (".pdf", ".png", ".jpg", ".jpeg")

# Pack section, in filing order, and which generated pages belong to it.
SECTIONS = {
	"Letter": lambda key: key == "letter",
	"Receipts and payments account": lambda key: key == "receipts_payments",
	"Abstract statement of attendance": lambda key: key == "abstract",
	"Food expenditure statements": lambda key: key.startswith("food_"),
	"Appendix – H": lambda key: key == "appendix_h",
	"List of officer bearer": lambda key: key == "officer_bearers",
	"List of staff": lambda key: key == "staff_list",
	"Result sheet of inmates": lambda key: key == "result_sheet",
	"School: College attendance registers": lambda key: key.startswith("register_"),
}


def default_sections():
	return list(SECTIONS)


def label(page):
	"""A page's title with its month (and school) where it has one."""
	parts = page["key"].split("_", 3)
	if page["key"].startswith("food_"):
		return f"{page['title']} – {parts[2]} {parts[1]}"
	if page["key"].startswith("register_"):
		return f"{page['title']} – {parts[2]} {parts[1]}"
	return page["title"]


def validate_pages(doc):
	seen = set()
	for row in doc.pages:
		if row.section == UPLOADED:
			if not row.file:
				frappe.throw(_("Row {0}: attach the file for the uploaded page").format(row.idx))
			if not row.title:
				frappe.throw(_("Row {0}: give the uploaded page a title").format(row.idx))
			if os.path.splitext(row.file)[1].lower() not in ALLOWED_UPLOADS:
				frappe.throw(_("Row {0}: only PDF, PNG and JPG files can go into the pack").format(row.idx))
		elif row.section in seen:
			frappe.throw(_("Row {0}: {1} is listed twice").format(row.idx, _(row.section)))
		seen.add(row.section)


def file_content(file_url):
	return frappe.get_doc("File", {"file_url": file_url}).get_content()


def image_html(content, extension):
	from PIL import Image

	width, height = Image.open(io.BytesIO(content)).size
	mime = "image/png" if extension == ".png" else "image/jpeg"
	data = base64.b64encode(content).decode()
	html = (
		'<html><head><meta charset="utf-8"></head><body style="margin:0;text-align:center">'
		f'<img style="max-width:100%;max-height:270mm" src="data:{mime};base64,{data}"></body></html>'
	)
	return html, LANDSCAPE if width > height else PORTRAIT


def items(doc):
	"""The pack as an ordered list of items (generated or uploaded), and the warnings."""
	pages, warnings = build_pages(doc.company, doc.from_date, doc.to_date, doc.get("letter_date"), doc.get("place"))
	out = []
	for row in doc.pages:
		if not row.include:
			continue
		if row.section == UPLOADED:
			out.append({"title": row.title, "kind": "uploaded", "file": row.file})
			continue
		matcher = SECTIONS.get(row.section)
		found = [p for p in pages if matcher and matcher(p["key"])]
		if not found:
			warnings.append(_("Nothing to print for {0}").format(_(row.section)))
		out += [{"title": label(p), "kind": "generated", "page": p} for p in found]
	return out, warnings


def info(doc):
	listed, warnings = items(doc)
	for item in listed:
		if item["kind"] == "uploaded" and not frappe.db.exists("File", {"file_url": item["file"]}):
			warnings.append(_("The file for {0} is missing").format(item["title"]))
	return {"pages": [{"title": i["title"], "kind": i["kind"]} for i in listed], "warnings": warnings}


RENDER_WORKERS = 4
CACHE_SECONDS = 600


def source_of(item):
	"""What one item prints: (kind, html, orientation) for a generated page, or the uploaded file's bytes."""
	if item["kind"] == "generated":
		return ("html", item["page"]["html"], item["page"]["orientation"])
	extension = os.path.splitext(item["file"])[1].lower()
	content = file_content(item["file"])
	if extension == ".pdf":
		return ("pdf", content, None)
	html, orientation = image_html(content, extension)
	return ("html", html, orientation)


def render_source(source):
	kind, data, orientation = source
	return data if kind == "pdf" else to_pdf(data, orientation)


def kept(key):
	return frappe.cache.get_value(key)


def keep(key, value):
	frappe.cache.set_value(key, value, expires_in_sec=CACHE_SECONDS)


def pdf_bytes(doc):
	"""One PDF with every included page. Portrait and landscape pages keep their own size.

	Pages are rendered in parallel. The merged PDF is kept for ten minutes under a hash of everything it
	prints, so Download right after Preview is instant and an edit to any record or file makes a new one.
	"""
	listed, _warnings = items(doc)
	sources = [source_of(item) for item in listed]
	digest = hashlib.sha1()
	for kind, data, orientation in sources:
		digest.update(f"{kind}|{orientation}|".encode())
		digest.update(data if isinstance(data, bytes) else data.encode())
	key = f"zohra_trust_pack_pdf:{digest.hexdigest()}"
	cached = kept(key)
	if cached:
		return cached
	with ThreadPoolExecutor(max_workers=RENDER_WORKERS) as pool:
		parts = list(pool.map(render_source, sources))  # in order
	writer = PdfWriter()
	for pdf in parts:
		for pdf_page in PdfReader(io.BytesIO(pdf)).pages:
			writer.add_page(pdf_page)
	out = io.BytesIO()
	writer.write(out)
	keep(key, out.getvalue())
	return out.getvalue()
