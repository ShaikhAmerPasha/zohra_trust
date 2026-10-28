# Zohra Trust: maintainer guide

What each part of the app does and how it is built. `ZOHRA_BUILD_SPEC.md` is the source of truth; this file records what is implemented. Updated after every slice.

## Layout

```
zohra_trust/
  hooks.py                        fixtures, doc_events (correction window)
  trust_operations/doctype/       custom DocTypes: JSON + controller (+ .js for buttons)
  utils/                          shared logic (sanction, period, dates, correction, attendance,
                                  consumption, food_statement)
  api/                            whitelisted methods called from the browser
  setup/create_unit.py            one-call unit setup
  fixtures/                       role, custom_field, custom_docperm
  tests/                          unit tests, helpers, flow.py (end-to-end flow check)
docs/                             this guide, TEST_GUIDE.md, FLOW.md
```

Controllers stay small. Logic lives in `utils/`; the controller calls it.

## Slice 1: masters, students, Boarding Attendance

| Part | How it works |
|---|---|
| Masters | Trust School, Trust Exam, Trust Class (+ Class Exam Marks), Trust Academic Year, Trust Settings (+ Officer Bearer), Trust Unit Profile (+ Unit Sanction). Named by their key field. Academic years may not overlap; a class cannot be its own next class. |
| `get_unit_sanction(company, date)` | `utils/sanction.py`. Reads the profile's sanction rows: `effective_from <= date` and (`effective_to` empty or `>= date`), latest `effective_from` wins. Returns `strength`, `rate`, `rule`, or `None`. The strength is never hard-coded. |
| `assert_period_open(company, date, doctype)` | `utils/period.py`. Raises if an Accounting Period of the company covers the date and lists that DocType as closed. Needed because ERPNext only checks the period when GL entries post, so stock-only documents are not blocked. To close a month for a custom DocType, the Principal adds an Accounting Period and lists the DocType under closed documents. |
| Correction window | `utils/correction.py`, hooked to `before_cancel` of every custom transaction plus Purchase Invoice, Stock Entry and Journal Entry (`hooks.py`). Principal and Administrator always pass. Others may cancel only their own entry within `Trust Settings.correction_window_days` (default 1). Stock Entries and Journal Entries made by our documents are skipped; the parent was already checked. |
| Trust Student | `leaving_date` required unless status is Active. |
| Student Enrollment | Name `ENR-{academic year}-{student}`, so one per student per year. `register_sl_no` unique within unit and year. Planned and Enrolled enrollments for the unit and year, including this one, may not exceed the strength in force on `enrollment_date` (or today): "Sanctioned strength reached". Status defaults to Enrolled. |
| Boarding Attendance | Name `BAT-{abbr}-{YYYY}-{MM}`, one per unit and month. **Fill Girls** (`fill_rows`) loads every Enrolled student of the unit and academic year in register order. Hostel days = calendar days, or counted from the enrollment date if she joined during the month. School days present default to her school's working days from the `school_days` table (a missing school stops the fill). Sanction fields are copied from `get_unit_sanction(company, period_end)`. Grant per row: full monthly rate (rule Full month per student); pro-rata and per-day rules are also coded. `validate` checks roll vs strength, day limits, closed period, and sets totals. |

## Slice 2: purchases, consumption, Food Expenditure Statement

| Part | How it works |
|---|---|
| Custom fields | Item and Account: `custom_on_food_statement`, `custom_statement_order`. Account: `custom_rp_head_in/out` (used in slice 3). Stock Entry: `custom_material_consumption`. Shipped in `fixtures/custom_field.json`. |
| Permissions on standard DocTypes | `fixtures/custom_docperm.json`: Data Entry and Store can read/create/write/submit/cancel their own Purchase Invoice, and read the masters a Purchase Invoice needs. |
| Purchases | Standard Purchase Invoice, paid in cash, Update Stock on. Dr expense, Cr cash; quantity goes to the Bin. Perpetual Inventory is off. |
| Material Consumption | `utils/consumption.py`. One per unit per day (docstatus below 2). Items must be flagged for the statement. On submit it makes a Material Issue Stock Entry from the unit's ration warehouse (no GL entries) and stores it in `stock_entry`; on cancel it cancels that entry. `api/material_consumption.copy_yesterday` returns the latest earlier day's items; the **Copy Yesterday** button calls it. |
| Food Expenditure Statement | `utils/food_statement.py`. Name `FES-{abbr}-{YYYY}-{MM}`. **Fill** builds one line per flagged Item (old balance from the last submitted statement, month purchases from Purchase Invoices, month consumption from Material Consumption) and one line per flagged Account (net GL debit of the month). `calculate()` derives rates, totals, expenditure and balances. Expenditure: consumed = total quantity → total amount; else purchased quantity > 0 → consumed × purchased rate; else consumed × old rate. In an opening statement old quantity and amount are typed and survive re-filling. Submit needs a previous submitted statement unless `is_opening`; a stock-vs-statement difference is only a warning. |
| `create_unit` | Creates Company (Perpetual Inventory off), Hostel Store warehouse, supplier "Cash purchase", accounts named as the filed report (Food, Vegetables, Mutton, Milk, Fuel, Detergent, Salaries, GESCOM, Education, Miscellaneous, Govt. grant received, Bank interest, Zohra trust; with statement order and Receipts and Payments heads), a Bank GL account and a Bank Account (`bank_name`, default "Hostel Bank"), Cash mode of payment, items (14 stock items in statement order plus Vegetables, Mutton, Milk, Fuel) and the Trust Unit Profile. Safe to run again; adds the Item Default for a second unit. |

## Slice 3: receipts and payments

| Part | How it works |
|---|---|
| Cash Bank Voucher | `utils/voucher.py`. Name `CBV-.YYYY.-.#####`. Receipt or Payment, Cash or Bank, against an account head (income, expense or trust account; not a group, not cash or bank). Validates amount above zero, head and bank account belong to the company, closed period, and party for payable or receivable heads. Roles: Data Entry (and Principal). |
| Journal Entry made on submit | Receipt: Dr cash (company default cash account) or the Bank Account's GL account, Cr head. Payment: reverse. Cash mode uses voucher type Cash Entry, Bank mode Journal Entry (a Bank Entry would force a reference date). `custom_cash_bank_voucher` on the entry and `journal_entry` on the voucher link them. Created with permissions ignored, so Data Entry needs no Journal Entry rights beyond read. |
| Cancel | Cancelling the voucher cancels the entry (`frappe.flags.cancelling_cash_bank_voucher` lets that through). `block_direct_journal_cancel` (doc_events on Journal Entry) refuses cancelling such an entry by itself. |
| Receipts and Payments Account | Script report in `trust_operations/report/receipts_and_payments_account/`. Opening and closing cash and bank from GL entries of Cash and Bank type accounts. For every voucher touching those accounts, non-cash/bank lines are netted per voucher and account; net credit is a receipt under `custom_rp_head_in`, net debit a payment under `custom_rp_head_out` (account name if the head is blank). So a cash purchase invoice shows under Food, and its payable lines net to nothing. Rows in the filed order, then others alphabetically; Opening balance and Closing balance for Cash and Bank; Total row where receipts equal payments. |

## Slice 5: Result Sheet of Inmates and promotion

| Part | How it works |
|---|---|
| Result Sheet of Inmates | `utils/results.py`. Name `RSI-{abbr}-{academic year}-{exam}`, one per unit, year and exam. **Fill Students** (`fill_rows`) loads Enrolled students in register order with maximum marks from the student's Trust Class (Class Exam Marks row for the exam; a missing row stops the fill) and the first guardian's name when the girl has a guardian. `validate`: marks between 0 and maximum, closed period, totals `appeared` (Pass or Fail), `passed`, `failed`. On a Final exam a blank `promotion_action` takes the default once a result is set: Pass with a next class Promote, Pass in the last class Complete, Fail Repeat in every class, Absent stays blank. Submit needs a result on every row; on a Final also an action, a leaving destination for Complete, and a next class for Promote. |
| `promote()` | Button **Promote** on a submitted Final sheet with `promotion_done` off. Next year is the Trust Academic Year with the earliest start after this year's end. Promote and Repeat make a Planned Student Enrollment (enrollment date = next year's start, next free register number, `previous_enrollment` set, `is_repeating` for Repeat). Complete makes the Trust Student Passed Out and the enrollment Completed; Leave makes both Left; the leaving date is the year's end date. Enrollments are made through the normal Student Enrollment validation, so a promotion above the sanctioned strength is refused. It runs inside a savepoint: one refusal undoes the whole promotion. Last year's enrollment is changed only for Complete or Leave (status). Once done, the sheet cannot be cancelled or promoted again. |
| Confirming | Planned becomes Enrolled by editing the enrollment status (Principal). |

## Spec changes applied (second version of the spec)

Section 10 labels applied to the DocTypes (`gen` labels such as Sanction strength, Hostel attendance, Name of food grains). Office Bearer became Officer Bearer (patch `rename_officer_bearer`). Account names follow section 4 (Detergent, Salaries, GESCOM, Govt. grant received, Bank interest, Zohra trust). GESCOM's Receipts and Payments head out is "GESCOM". Result Row labels (SL. NO, NAME & FATHER NAME, CLASS, TOTAL MARKS, MARKS OBTAINED, RESULT) are applied.

## Schema repair after migrate

`setup/schema.py` runs on `after_migrate`. An ERPNext patch (`v16_0.migrate_address_contact_custom_fields`) re-creates Custom Fields on Address and Contact; on this older site the columns were not added, so forms that read them failed with "Unknown column". The hook reloads any DocType whose Custom Field has no column (it reads the live table, not Frappe's cached column list). It does nothing when all is well.

## Known gaps and assumptions

Slice 5 assumptions: Data Entry (not Store) enters and submits result sheets and may press Promote; guardian name is shown in its own column next to the name; Planned enrollments are dated the first day of next year.

See the "assumptions" lists in each slice report. Open items: the filed September closing 83,040 differs by 0.50 from the exact figure 83,039.50. Opening balances dated before 1 April 2026 need Fiscal Year 2025-2026 on the site. The default bank name "Hostel Bank" is a placeholder.

## Commands

```
bench --site zohra_erp migrate
bench --site zohra_erp run-tests --app zohra_trust
bench --site zohra_erp execute zohra_trust.tests.flow.run
```
