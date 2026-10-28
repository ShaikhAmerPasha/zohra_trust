# Zohra Trust: test guide

Three kinds of check, all run on `zohra_erp`. Unit tests roll back their data at the end of each class; the flow check rolls back everything. Nothing stays in the database.

```
bench --site zohra_erp run-tests --app zohra_trust                     # all unit tests
bench --site zohra_erp run-tests --module zohra_trust.tests.test_slice1  # one slice
bench --site zohra_erp execute zohra_trust.tests.flow.run               # end-to-end flow as real roles
```

Run after each slice: the new slice's tests, then the whole suite, so earlier slices are checked for breakage, then the flow check.

## Results

| Slice | Tests | Passed | Flow checks passed |
|---|---|---|---|
| 1: masters, students, Boarding Attendance | 14 | 14 | 4/4 (flow phase 1) |
| 2: purchases, consumption, Food Expenditure Statement | 8 | 8 | 7/7 (flow phase 2) |
| 3: Cash Bank Voucher, Receipts and Payments | 9 | 9 | 5/5 (flow phase 3) |
| 5: Result Sheet, promotion | 8 | 8 | 5/5 (flow phase 5) |
| Schema repair after migrate | 1 | 1 | n/a |
| Whole suite now | 40 | 40 | 21/21 including cleanup |

## Slice 1 tests (`tests/test_slice1.py`)

- Academic years that overlap are refused.
- Leaving date is required unless the student is Active.
- Sanction lookup: latest effective date wins; before the first row returns nothing.
- Hostel days with 100 enrolled: June 3,000, July 3,100, August 3,100, September 3,000; roll 100; grant 100 x 850.
- Grant follows the rate in force (900 from 1 November).
- A strength drop (90 from 1 December) refuses December's sheet.
- A second sheet for the same month is refused.
- Days above calendar days or working days are refused.
- A school with no working days row stops the fill.
- A girl enrolled on 11 June counts 20 hostel days in June.
- A closed Accounting Period refuses the sheet.
- Correction window: a Data Entry owner is blocked after 3 days; Administrator is not.
- 151st enrollment refused; after a 160 row from 1 October, an enrollment dated 5 October is accepted and one dated 15 September is refused.
- Duplicate enrollment for the same year and duplicate register number are refused.

## Slice 2 tests (`tests/test_slice2.py`)

- June opening statement: every item line of the filed table (old, purchased, consumed, expenditure, balance), amount-only rows (Vegetables 15,370; Mutton 22,700; Fuel 11,780; Salaries 11,000; Milk and GESCOM nil), totals 7,540 / 1,79,150 / 1,86,690 / 1,63,260 / 23,430. Filling twice keeps the typed old balances.
- July chains to June: totals 23,430 / 1,37,700 / 1,61,130 / 1,48,865 / 12,265. A later month with no statement in between still chains to the last submitted one. (Per-item July data is made up to reach the filed totals.)
- September opening: old 22,640, purchase 2,24,388, available 2,47,028, expenditure 1,63,988.50, closing 83,040 within 0.50. (Per-item data made up.)
- A non-opening statement with no earlier submitted one cannot be submitted.
- Material Consumption lowers the Bin and posts no GL; cancelling restores the Bin and cancels the Stock Entry.
- `copy_yesterday` returns the earlier day's lines; a second consumption on one day is refused.
- A non-statement item is refused; a closed period refuses a consumption.
- Store role: can create and submit its own Purchase Invoice, read Items, create Material Consumption, cannot write Items.

## Slice 3 tests (`tests/test_slice3.py`)

- Receipt makes a Journal Entry: Dr cash, Cr head, with the voucher linked both ways. Payment from the bank is the reverse.
- Cancelling the voucher cancels the entry and removes its GL entries.
- Cancelling the Journal Entry directly is refused and the entry stays submitted.
- Refused: amount 0, Bank mode without a bank account, a payable head without a party, a cash account as head, a closed period.
- Roles: Data Entry enters and submits a voucher; Store cannot create one.
- Filed half year (1 April to 30 September 2026): opening cash 682 and bank 6,34,446.84; loan 12,30,000; bank interest 4,779; Food 5,63,825, Fuel 37,780, Detergent 47,400, Salaries 48,000, Transfer to Zohra trust 7,00,000. Closing cash 33,677, closing bank 4,39,225.84 (the filed 4,39,225 plus the 84 paise), receipts equal payments at 18,69,907.84. The loan is split cash 7,30,000 and bank 5,00,000 so the filed cash and bank closings both hold.
- A cash purchase invoice (stock item and non-stock item) shows as one Food row, no payable row, receipts equal payments.

## Slice 5 tests (`tests/test_slice5.py`)

- Fill Students: 13 girls in register order, maximum marks by class (250, 480, 625), guardian name only where there is one.
- Marks above the maximum are refused; totals appeared, passed, failed; a missing result stops submit; sheet name `RSI-THJ-2026-27-Mid-term`.
- Default actions: Pass in classes 1 to 9 Promote, Pass in class 10 Complete, Fail Repeat (also in class 10), Absent blank.
- Final submit is refused while an action or leaving destination is missing.
- Promotion: classes 1 to 9 move up to the next class as Planned with `previous_enrollment`; a failed girl repeats with `is_repeating`; a class 10 pass is Passed Out with date 31 March 2027, destination and Completed enrollment; Leave closes the student; register numbers 1 to 11 are sequential; last year's enrollments are unchanged; promoting twice and cancelling after promotion are refused.
- A Mid-term sheet and an unsubmitted sheet cannot promote.
- Data Entry can enter and submit a sheet.
- Strength: with strength 3 and a fourth seat already held next year, promotion is refused with "Sanctioned strength reached" and nothing is saved; after the seat is freed it succeeds.

## Defect fixes (browser run)

- `tests/test_schema.py`: drops `Address.is_your_company_address`, runs the repair, expects the column back.
- `test_slice2`: Copy Yesterday also returns item name and unit.
- `test_slice3`: every Receipts and Payments row has null (not missing) in the empty cell.

## Flow check (`tests/flow.py`)

Runs the real working day as Principal, Data Entry and Store users and ends with a rollback and a check that no data is left. Phase 1: students, June Boarding Attendance, cancel inside the window. Phase 2: purchases, consumption, statement, cancel. Phase 3: vouchers, direct Journal Entry cancel refused, report, voucher cancel. Phase 5: Final result sheet, promote, student status changes, Principal confirms a Planned enrollment. Slice 4 has no phase. Each new slice adds a `phase_N` function and appends it to `PHASES`.

## Test data notes

Tests use fake units (Test Hostel A to E, Flow Hostel) and fake students. Items, the Cash mode of payment and the Hostel Ration item group are created by `create_unit` and removed by the rollback.
