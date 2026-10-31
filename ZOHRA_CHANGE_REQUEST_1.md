# Zohra Trust: change request 1

For Claude Code. These changes come from Zohra's answers. Apply them to the repo's `ZOHRA_BUILD_SPEC.md`, the code and the tests, in that order. Do not start slice 4 or 6. When you finish, show the changed files, the full test output and the git log, then stop and wait for my review.

## 1. Remove NIOS

Embassy NIOS is a separate entity and is not part of this app. Delete every record, option, field, fixture, test and sentence that treats NIOS or Embassy as students, classes, schools or marks. Trust School lists only Zohra English Medium and Zohra Kannada Medium. Search the whole repo for `NIOS` and `Embassy`, and tell me what you removed and anything you left and why.

## 2. Promotion: "Left with T.C."

A girl who fails, in any class including class 10, may either repeat or leave with a Transfer Certificate. Nothing goes to NIOS.

1. In Result Row.promotion_action, rename the option `Leave` to `Left with T.C.`. The options are now: Promote, Repeat, Complete, Left with T.C.
2. Add a data patch that changes existing `Leave` values to `Left with T.C.`.
3. Add two fields to Trust Student: `tc_number` (Data, label "T.C. number") and `tc_date` (Date, label "T.C. date"). Both are optional, because the certificate may be issued after the result is entered. Show them only when status is Left.
4. In `promote()`, the action `Left with T.C.` sets the Trust Student status to Left, `leaving_date` to the end date of the academic year, and `leaving_reason` to "Left with T.C."; the old enrollment status becomes Left; no enrollment is made for next year.
5. Defaults do not change. Fail defaults to Repeat in every class. Pass in a class with a next class defaults to Promote. Pass in the last class defaults to Complete, which still requires a `leaving_destination`.
6. Update the promotion diagram in section 3.3 and the logic text in section 6 of the spec, and the Select options table.
7. Add tests: Fail with Left with T.C. closes the record and makes no next-year enrollment; Fail with Repeat makes the same-class enrollment with `is_repeating`; class 10 Fail allows both; the patch converts old `Leave` rows.

## 3. April and May

No Food Expenditure Statement is made for April and May. April's purchases are bought in March and entered as ordinary Purchase Invoices dated in March, so they are inside March's statement. The kitchen's daily Material Consumption continues all year, and the old balance of the next statement is always the real stock at the start of its period (this is already built).

No code change. Add to section 7 of the spec: "No statement is made for April and May." Add a test that a statement for March followed by one for June, with consumption entered in April and May, gives June an old balance equal to the real stock.

## 4. The grant

The department pays the grant once every six months, as one receipt. It is ₹850 per student per month, paid in full and not pro-rated, whatever the days stayed. The built behaviour already does this: `grant_amount` per row is the full rate. Record it in the spec: the half-yearly receipt is entered with a Cash Bank Voucher on the account "Govt. grant received", and the Grant Bill (later) sums the six months of Boarding Attendance. The grant bill format is still to come from Zohra.

## 5. Marks and diet scale

1. **Maximum marks (apply).** Zohra says the Education Department's 40 (classes 1 to 5), 60 (classes 6 and 7) and 80 (classes 8, 9 and 10) are marks per subject. The result sheet prints totals, so keep `max_marks` as the total per class and exam: 250 for classes 1 to 5, 480 for classes 6 to 9 and 625 for class 10, as on the filed sheet. Add a reference field `max_marks_per_subject` (Int, label "Maximum marks per subject") to Class Exam Marks and seed it 40, 60 and 80 by class band. The sheet and the checks must not use it, and the total must never be computed from it (for example 6 subjects at 80 gives 480 for classes 8 and 9, but the other totals do not follow from it). Zohra has not said what the Mid-term totals are, so seed the Mid-term rows with the same totals as the Final and mark that as an assumption in section 7 of the spec.
2. **Diet scale (pending, do not build).** Zohra has said both that no diet scale is prescribed and that one exists from a nutrition board, and is now not sure of the table. When a table arrives, the plan is a Diet Scale DocType with a child table of items and quantity per student per day, and a "Fill from diet scale" button on Material Consumption next to Copy yesterday. Add it to section 9 of the spec as pending.

## 6. Open questions to list in section 9

- The Mid-term totals per class.
- The diet scale table, and whether it differs by age or class.
- The grant bill sample.
- Whether the report filed last March has Food Expenditure Statements for March and April. The October report has statements for June to September only, so it cannot answer this.