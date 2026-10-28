import frappe
from frappe import _
from frappe.model.document import Document


class TrustClass(Document):
	def validate(self):
		if self.next_class and self.next_class == self.name:
			frappe.throw(_("Next Class cannot be the class itself"))
		exams = [row.exam for row in self.exam_marks]
		if len(exams) != len(set(exams)):
			frappe.throw(_("An exam appears twice in Exam Marks"))
