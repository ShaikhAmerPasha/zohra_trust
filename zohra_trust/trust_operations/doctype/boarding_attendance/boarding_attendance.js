frappe.ui.form.on("Boarding Attendance", {
	refresh(frm) {
		if (frm.doc.docstatus === 0) {
			frm.add_custom_button(__("Fill Girls"), () => {
				frm.call({ doc: frm.doc, method: "fill_rows", freeze: true }).then(() => frm.dirty());
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
