import frappe

from zohra_trust.utils.report_pack import info, pdf_bytes


def _pack(name):
	doc = frappe.get_doc("Report Pack", name)
	doc.check_permission("read")
	return doc


@frappe.whitelist()
def pack_info(name):
	"""Page list and warnings for the Preview dialog."""
	return info(_pack(name))


@frappe.whitelist()
def pack_pdf(name):
	"""The merged PDF, built from the records at this moment."""
	doc = _pack(name)
	frappe.local.response.filename = f"{doc.name}.pdf"
	frappe.local.response.filecontent = pdf_bytes(doc)
	frappe.local.response.type = "pdf"
