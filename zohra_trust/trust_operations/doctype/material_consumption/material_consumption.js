frappe.ui.form.on("Material Consumption", {
	setup(frm) {
		// The Stock Entry is cancelled by this document's own on_cancel, so Cancel All must not list it
		frm.ignore_doctypes_on_cancel_all = ["Stock Entry"];
		frm.set_query("item_code", "items", () => ({ filters: { custom_on_food_statement: 1, disabled: 0 } }));
	},
	company(frm) {
		frm.trigger("open_existing_for_day");
	},
	posting_date(frm) {
		frm.trigger("open_existing_for_day");
	},
	// One document per company and day: open the draft if there is one, else point to the submitted one
	open_existing_for_day(frm) {
		if (!frm.is_new() || !frm.doc.company || !frm.doc.posting_date) return;
		frappe
			.call({
				method: "zohra_trust.api.material_consumption.existing_for_day",
				args: { company: frm.doc.company, posting_date: frm.doc.posting_date },
			})
			.then((r) => {
				const found = r.message;
				if (!found) return;
				if (found.docstatus === 0) {
					frappe.show_alert({ message: __("{0} is already started for this day. Opening it.", [found.name]), indicator: "blue" });
					frappe.set_route("Form", "Material Consumption", found.name);
				} else {
					const link = `<a href="/app/material-consumption/${encodeURIComponent(found.name)}">${frappe.utils.escape_html(found.name)}</a>`;
					frappe.msgprint({
						title: __("Already made for this day"),
						message: __("Material Consumption {0} is already submitted for this day. Open it to see it, or cancel it to enter again.", [link]),
						indicator: "orange",
					});
					frm.set_value("posting_date", "");
				}
			});
	},
	refresh(frm) {
		if (frm.is_new() && frm.doc.amended_from && frm.doc.stock_entry) frm.set_value("stock_entry", "");
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
