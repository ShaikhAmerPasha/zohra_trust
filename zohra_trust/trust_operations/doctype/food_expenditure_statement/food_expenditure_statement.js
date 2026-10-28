frappe.ui.form.on("Food Expenditure Statement", {
	refresh(frm) {
		if (frm.doc.docstatus === 0) {
			frm.add_custom_button(__("Fill"), () => {
				frm.call({ doc: frm.doc, method: "fill", freeze: true }).then(() => frm.dirty());
			});
		}
	},
	onload(frm) {
		if (frm.is_new() && !frm.doc.year) {
			frm.set_value("year", moment().year());
			frm.set_value("month", moment().format("MMMM"));
		}
	},
});
