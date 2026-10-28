frappe.ui.form.on("Cash Bank Voucher", {
	setup(frm) {
		frm.set_query("account_head", () => ({
			filters: { company: frm.doc.company, is_group: 0, account_type: ["not in", ["Cash", "Bank"]] },
		}));
		frm.set_query("bank_account", () => ({ filters: { company: frm.doc.company } }));
	},
});
