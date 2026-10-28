import frappe
from frappe.tests.utils import FrappeTestCase

from zohra_trust.setup.schema import add_missing_custom_field_columns, has_column


class TestSchemaRepair(FrappeTestCase):
	def test_missing_custom_field_column_is_added(self):
		field = "is_your_company_address"
		self.assertTrue(has_column("Address", field))
		frappe.db.sql_ddl(f"alter table `tabAddress` drop column `{field}`")
		frappe.db.commit()
		self.assertFalse(has_column("Address", field))
		add_missing_custom_field_columns()
		frappe.db.commit()
		self.assertTrue(has_column("Address", field))
		add_missing_custom_field_columns()  # nothing to repair: no error
