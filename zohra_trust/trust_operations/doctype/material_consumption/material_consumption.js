frappe.ui.form.on("Material Consumption", {
	setup(frm) {
		frm.set_query("item_code", "items", () => ({ filters: { custom_on_food_statement: 1, disabled: 0 } }));
	},
	refresh(frm) {
		if (frm.doc.docstatus === 0) {
			frm.add_custom_button(__("Copy Yesterday"), () => frm.trigger("copy_yesterday"));
		}
	},
	copy_yesterday(frm) {
		if (!frm.doc.company || !frm.doc.posting_date) {
			frappe.msgprint(__("Set Company and Date first"));
			return;
		}
		frappe
			.call({
				method: "zohra_trust.api.material_consumption.copy_yesterday",
				args: { company: frm.doc.company, posting_date: frm.doc.posting_date },
			})
			.then((r) => {
				frm.clear_table("items");
				(r.message || []).forEach((row) => frm.add_child("items", row));
				frm.refresh_field("items");
			});
	},
});
