# Zohra Trust: change request 2

For Claude Code. A second filed report (October 2024 to March 2025, filed 28 February 2025) was reviewed. Apply these small changes after change request 1 is committed. Do not start slice 4 or 6. When done, show the changed files, the full test output and the git log, then stop and wait for my review.

## 1. Officer Bearer: address and "Member"

The filed report has a page called LIST OF MEMBERS with the columns SL.NO, NAME, DESIGNATION and ADDRESS. The name carries the qualification on a second line (for example "B.E, M.TECH, Ph.D"). Designations used are President, Secretary, Joint Secretary and Member.

1. Add `address` (Small Text, label "Address") to the Officer Bearer child table.
2. Change the designation options to: President, Secretary, Joint Secretary, Member, Trustee.
3. Update section 5 and section 10 of the spec to match. Add the page columns SL.NO, NAME, DESIGNATION, ADDRESS to section 10.1.
4. Add a patch only if existing rows need it (existing rows keep their designation).

## 2. More golden test data (second filing)

Add tests from this filing. In October 2024 to March 2025 the hostel had 132 enrolled students and a sanctioned strength of 150. The filed abstract is exactly 132 times the number of days:

| Month | Hostel attendance (132 × calendar days) | School days | School attendance (132 × school days) |
|---|---|---|---|
| October 2024 | 4,092 | 22 | 2,904 |
| November 2024 | 3,960 | 24 | 3,168 |
| December 2024 | 4,092 | 22 | 2,904 |
| January 2025 | 4,092 | 26 | 3,432 |
| February 2025 | 3,696 | 23 | 3,036 |
| March 2025 | 4,092 | 24 | 3,168 |

Test that with 132 Enrolled students and every girl present, Boarding Attendance gives these hostel totals and school attendance totals.

Reference only (do not build item-level fixtures from the handwriting): the filed food statement totals, opening / purchased / total / expenditure / closing, were Oct 24,455 / 1,10,047 / 1,34,502 / 1,18,757 / 15,745; Nov 15,745 / 1,68,110 / 1,83,855 / 1,52,082 / 31,773; Dec 31,773 / 1,49,800 / 1,81,574 / 1,53,585 / 27,988; Jan 27,988 / 1,50,320 / 1,78,308 / 1,53,787 / 24,521; Feb 24,521 / 2,11,430 / 2,35,951 / 1,44,798 / 91,153; Mar 91,153 / 70,605 / 1,61,758 / 1,53,547 / 8,206. Each month's closing is the next month's opening. The paper has two slips: the December total should be 1,81,573, and March's closing should be 8,211. Do not use the written figures as strict expectations.

## 3. Check only, do not change

This report was filed on 28 February 2025, yet it contains the March 2025 food statement and the March attendance. Check whether any code or validation blocks submitting a Boarding Attendance or a Food Expenditure Statement before the end of its month. Report what you find. Make no change until I decide.

## 4. Open questions to list in section 9 of the spec

- Filing calendar: this report was filed 28 February for a period ending 31 March, so the last month appears to be prepared in advance.
- Whether the March report carries a Result Sheet of Inmates. This filing has none.
- Whether the "School attendance" and "Total" columns of the abstract are filled or left blank. This filing fills School attendance; the October 2026 filing left it blank.
- The receipts and payments page of this filing is headed "Zohra Destitute Home for Girls, for one cottage", but its figures match the hostel's statements.
- The grant received in this filing, 4,61,745, is about 69 percent of 132 × 6 × ₹850 (6,73,200).