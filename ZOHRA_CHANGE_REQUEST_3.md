# Zohra Trust: change request 3 (Report Pack)

For Claude Code. Apply after change requests 1 and 2 are committed. Work through the items in order, and after each one run its tests. Do not start the live preview (item 7) until items 1 to 6 pass. When done, show the changed files, the full test output and the git log, then stop and wait for my review.

The Report Pack as built is accepted: a child table of pages, Jinja templates, wkhtmltopdf, pypdf merge. Keep that design. These changes fix what the review found.

## 1. Abstract columns

School attendance is printed, from `total_school_days_present`. Total is blank by default, as in both filed reports. Add two switches on the Report Pack:
- `show_school_attendance` (Check, default 1).
- `show_abstract_total` (Check, default 0). When on, Total is hostel attendance plus school attendance; it is never just a copy of hostel attendance.

## 2. Letter and Appendix – H: date, place, paragraphs

1. Add `letter_date` (Date, default today) and `place` (Data, default "Kalaburagi") to the Report Pack. Print the letter date top right on the letter. Print "Date" and "Place" on Appendix – H from the same two fields.
2. Keep paragraph breaks. Render the typed texts as HTML, and add `white-space: pre-line` to the letter body so a plain string also keeps its line breaks. The letter should read as separate lines: To, the officer, Sub, Dear Sir, the body, Thanking you we remain, Yours faithfully.
3. Seed the Appendix – H text of the Minority Girls Hostel with the filed wording in the appendix at the end of this file.

## 3. Typed texts belong to the pack

1. Add `letter_text` and `appendix_h_text` (Text Editor) to the Report Pack. When a pack is created, copy them from the Trust Unit Profile. The pack prints its own copy.
2. Add a button "Save as standing text" (Principal only) that copies the pack's texts back to the Trust Unit Profile. Without it, an edit changes this pack only.

## 4. Freeze: Report Pack becomes submittable

1. Make the Report Pack submittable. On submit: generate the merged PDF, attach it as `final_pdf` (read-only), set `finalized_by` and `finalized_on`, and save a snapshot in `snapshot` (JSON, read-only): the letter and Appendix – H texts used, the page list, the sheet chosen, and the name and modified time of every source document used.
2. After submit the pack is read-only, and the PDF never changes. Cancelling and amending makes a new version; the old PDF stays attached to the cancelled one.
3. Draft packs may still use the 10-minute cache. A submitted pack never regenerates from live records.
4. Roles: Principal and System Manager can submit and cancel. Data Entry and Store still have no access.

## 5. Checks before submit

Keep the warnings in the preview. On submit, refuse (with a reason the Principal can override by ticking `ignore_warnings` and typing `override_reason`):
- a month in the range with no submitted Boarding Attendance, except the months in UNEXPECTED_MONTHS;
- a month in the range with no submitted Food Expenditure Statement, except those months;
- an empty letter text or Appendix – H text;
- no active officer bearer, or no active Employee;
- no sanction in force for the period.

Store the override reason in the snapshot.

## 6. Result sheet and signatures

1. Add an optional `result_sheet` link (Result Sheet of Inmates) on the Report Pack. If blank, use the existing rule (newest submitted sheet whose academic year contains `to_date`, else the newest). The preview must say which sheet was chosen and its exam and year. Keep the `include` tick on the page row; the second filed report has no result sheet.
2. Add `result_sheet_signatory` (Data, label "Result sheet signed by") on the Trust Unit Profile, default "Principal, Zohra English Medium School", and print it on the result sheet in place of the fixed "Secretary".
3. Officer list: print the Address column (change request 2). The letterhead lists every active officer bearer.

## 7. Live preview (after items 1 to 6 pass)

Build a split screen on the Report Pack form. On the left are the editable texts (letter, Appendix – H) and the page list. On the right is the preview of the selected page, redrawn about 0.4 seconds after typing stops. Add a whitelisted method `preview_page(pack, page_key, overrides)` that fills the same Jinja template with the typed, unsaved text and returns HTML. Show it as an A4 sheet. Add a "Check as PDF" button that uses the existing PDF route. Edits are saved only when the user saves the form. Add tests for the method.

## 8. Real-data PDF

Yes, run the filed June to September 2026 load. Create a separate Company named "Filed Half Year Hostel", load the data through the same methods, and keep it (do not roll it back). Generate a pack for 01-04-2026 to 30-09-2026 and give me the PDF. List every page or figure that does not match the filed report, with the filed value and the system value.

## 9. Leave as it is

- The ₹15,773 difference between the filed receipts page and the filed food statements. It is for Zohra to explain. Do not adjust any figure to hide it.
- The Grant Bill page and the diet scale: pending.
- The master data: the phone number of Md. Azam Ali is 9448041586 in the filed reports, and the officer addresses must be entered from the filed LIST OF MEMBERS and checked by Zohra. These are data fixes, not code.

## Appendix: filed Appendix – H wording (seed text)

APPENDIX – H. RULES 12 FORM OF APPLICATION FOR GRANT IN AID TO BE SUBMITTED TO THE CHIEF SECRETARY ZILLAH PANCHAYAT, GULBARGA

1. Name and Address of Institute/Hostel: ZOHRA MINORITY GIRLS HOSTEL, Old Jewargi Road, Opp. PWD Qrt., Gulbarga – 585 102.
2. Name of Trust: Zohra Women & Children Charitable Welfare Trust.
3. Name and Address of the Secretary: Mrs. Basheerunnissa Begum (Retd. Lecturer), Mahetab Ali Compound, Aiwan-e-Shahi Colony, Gulbarga – 585 102. (Flag: the letterhead lists Md. Azam Ali as Secretary; Zohra to confirm which belongs here.)
4. a) No. and date of the order recognition by the backward classes Dept.: Not Applicable.
   b) Period of which the recognition: 18/06/1997-98/12/04/99, 01/01/05 (56, 56-81, 81-150).
5. a) Sanctioned strength at the time of recognition.
   b) Strength and attendance as on 31st March: 150 Inmates.
6. Approved expenditure for the Hostel and amount actually spent as per audit statement of A/c: Enclosed.
7. Amount of grant sanctioned during the previous year and during the year budget estimate for the current year should be enclosed: Enclosed.

Note: This application for grant should be accompanied by the audit statement of account and all other relevant documents as the facilities the sanction of grant by the competent authority.

DECLARATION: On behalf of the management the institution I/we hereby declare that the condition of the recognition and grant in prepared to submit all the account of the hostel. In inspection and to furnish the returns as may be required by the Dept. no money will be collected from the boarders of the Hostel towards their boarding & lodging.

Date: Place: Zohra Minority Girls Hostel. Secretary.