frappe.ui.form.on("Report Pack", {
	refresh(frm) {
		if (frm.is_new()) return;
		frm.add_custom_button(__("Preview"), () => frm.trigger("preview"));
		frm.add_custom_button(__("Download PDF"), () => frm.trigger("download_pdf"));
		frm.add_custom_button(__("Standard Pages"), () => {
			frappe.confirm(__("Replace the page list with the standard pages?"), () => {
				frm.call({ doc: frm.doc, method: "fill_sections", freeze: true }).then(() => frm.dirty());
			});
		});
	},
	pdf_url(frm) {
		return `/api/method/zohra_trust.api.report_pack.pack_pdf?name=${encodeURIComponent(frm.doc.name)}`;
	},
	download_pdf(frm) {
		window.open(frm.events.pdf_url(frm), "_blank");
	},
	preview(frm) {
		if (frm.is_dirty()) {
			frappe.msgprint(__("Save the Report Pack first"));
			return;
		}
		frappe
			.call({ method: "zohra_trust.api.report_pack.pack_info", args: { name: frm.doc.name }, freeze: true })
			.then((r) => {
				const info = r.message;
				const warnings = info.warnings.length
					? `<div class="alert alert-warning"><b>${__("To fix before filing")}</b><ul>${info.warnings.map((w) => `<li>${frappe.utils.escape_html(w)}</li>`).join("")}</ul></div>`
					: "";
				const pages = info.pages.map((p) => `<li>${frappe.utils.escape_html(p.title)}</li>`).join("");
				const dialog = new frappe.ui.Dialog({
					title: __("Preview: {0} pages", [info.pages.length]),
					size: "extra-large",
					fields: [{ fieldtype: "HTML", fieldname: "body" }],
				});
				dialog.fields_dict.body.$wrapper.html(
					`${warnings}<div class="row"><div class="col-sm-3"><ol class="small">${pages}</ol></div>` +
						`<div class="col-sm-9" style="position:relative">` +
						`<div class="pdf-wait text-muted" style="position:absolute;top:0;left:15px;right:15px;height:70vh;display:flex;align-items:center;justify-content:center;text-align:center;border:1px solid #ccc">` +
						`${__("Building the PDF. This can take up to 20 seconds. Please wait.")}</div>` +
						`<iframe style="width:100%;height:70vh;border:1px solid #ccc" src="${frm.events.pdf_url(frm)}"></iframe></div></div>`
				);
				dialog.show();
				// the message stays until the browser has the PDF
				dialog.$wrapper.find("iframe").on("load", () => dialog.$wrapper.find(".pdf-wait").hide());
			});
	},
});
