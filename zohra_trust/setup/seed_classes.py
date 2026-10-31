"""Trust Classes 1 to 10 with their promotion chain and the maximum marks of each exam.

bench --site <site> execute zohra_trust.setup.seed_classes.seed_classes

Safe to run again: a class or an exam row that already exists is left as the user set it.
The marks live in the Class Exam Marks table of each Trust Class; no other code reads
this module, so the totals can be changed on the Trust Class form at any time.
"""

import frappe

EXAMS = (("Mid-term", 1, 0), ("Final", 2, 1))

# (first class, last class, total marks per exam, marks per subject). Totals are as on the filed result sheet.
# The Mid-term totals are assumed equal to the Final totals until Zohra says otherwise.
BANDS = (
	(1, 5, 250, 40),
	(6, 7, 480, 60),
	(8, 9, 480, 80),
	(10, 10, 625, 80),
)


def seed_classes():
	for name, sequence, is_final in EXAMS:
		if not frappe.db.exists("Trust Exam", name):
			frappe.get_doc({"doctype": "Trust Exam", "exam_name": name, "sequence": sequence, "is_final": is_final}).insert()
	bands = {n: (total, subject) for first, last, total, subject in BANDS for n in range(first, last + 1)}
	last_class = max(bands)
	for n in range(last_class, 0, -1):  # from the top, so that next_class exists when it is linked
		name = f"Class {n}"
		if frappe.db.exists("Trust Class", name):
			continue
		total, subject = bands[n]
		frappe.get_doc(
			{
				"doctype": "Trust Class",
				"class_name": name,
				"sequence": n,
				"next_class": f"Class {n + 1}" if n < last_class else None,
				"exam_marks": [{"exam": exam, "max_marks": total, "max_marks_per_subject": subject} for exam, _seq, _final in EXAMS],
			}
		).insert()
