frappe.ui.form.on("Cash Bank Voucher", {
	setup(frm) {
		// The Journal Entry is cancelled by this document's own on_cancel, so Cancel All must not list it
		frm.ignore_doctypes_on_cancel_all = ["Journal Entry"];
		frm.set_query("account_head", () => ({
			filters: { company: frm.doc.company, is_group: 0, account_type: ["not in", ["Cash", "Bank"]] },
		}));
		frm.set_query("bank_account", () => ({ filters: { company: frm.doc.company } }));
	},
});
