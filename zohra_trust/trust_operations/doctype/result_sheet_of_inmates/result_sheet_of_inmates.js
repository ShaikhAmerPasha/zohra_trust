frappe.ui.form.on("Result Sheet of Inmates", {
	refresh(frm) {
		if (frm.doc.docstatus === 0) {
			frm.add_custom_button(__("Fill Students"), () => {
				frm.call({ doc: frm.doc, method: "fill_rows", freeze: true }).then(() => frm.dirty());
			});
		}
		if (frm.doc.docstatus === 1 && !frm.doc.promotion_done) {
			frm.add_custom_button(__("Promote"), () => {
				frappe.confirm(__("Make next year's enrollments from this Final result sheet?"), () => {
					frm.call({ doc: frm.doc, method: "promote", freeze: true }).then(() => frm.reload_doc());
				});
			}).addClass("btn-primary");
		}
	},
});
