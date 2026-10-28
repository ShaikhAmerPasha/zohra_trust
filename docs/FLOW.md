# Zohra Trust: working flow

The order in which staff use the system. Roles in brackets. Updated after every slice. The same sequence is exercised by `zohra_trust.tests.flow.run`.

## Once, at set-up (Principal / system admin)

1. Run `create_unit` for the hostel (company, abbreviation, sanctioned strength, grant rate, date of the order). This makes the company, store, accounts, items and the unit profile.
2. Make sure the Fiscal Years exist for every year that has opening balances (Fiscal Year 2025-2026 for the 1 April 2026 opening). Create the Trust Academic Year (for example 2026-27, 1 April to 31 March), the Trust Schools (English and Kannada medium) and the Trust Classes with their next class.
3. Fill Trust Settings: trust name, current academic year, correction window.
4. Create users, give each a role (Data Entry, Store or Principal) and a User Permission on the Company.
5. When the sanctioned strength or grant rate changes, add a row to Sanctions in the Trust Unit Profile with the date it starts. Do not edit the old row.

## When a girl is admitted (Principal)

1. Create the Trust Student (home unit, admission date).
2. Create her Student Enrollment (academic year, school, class, register number). The system refuses it if the sanctioned strength is reached.

## Every day

**Purchases (Store or Data Entry).** Enter a Purchase Invoice for each cash purchase: supplier "Cash purchase", tick Update Stock and Paid, mode Cash, choose items and quantities. Vegetables, Mutton, Milk and Fuel are entered as non-stock items.

**Kitchen use (Store).** Open Material Consumption. Click Copy Yesterday if today is similar, correct the quantities, save and submit. Only one per day. If a mistake is found, cancel it the same day (or next day) and enter it again; after the correction window only the Principal can cancel.

## Every month

**Boarding Attendance (Data Entry).**
1. New Boarding Attendance: company, month, year.
2. In School Working Days add one row per school with the days the school ran.
3. Click Fill Girls. Change hostel days or school days present for any girl who differs. Save and submit.

**Food Expenditure Statement (Data Entry or Store).**
1. Make sure every purchase and consumption of the month is entered and submitted, and salaries and GESCOM are recorded as Cash Bank Vouchers (Payment, account head Salaries or GESCOM).
2. New Food Expenditure Statement: company, month, year. For the first ever statement, tick Is Opening.
3. Click Fill. In an opening statement type the old quantity and amount of each item, then save.
4. Check the lines against the paper statement, then submit. The old balance of the next month comes from this one.

## Money in and out (Data Entry)

Enter a Cash Bank Voucher when money moves, as it happens:
1. New Cash Bank Voucher: company, Receipt or Payment, date, Cash or Bank (choose the bank account for Bank).
2. Choose the account head: for a receipt Govt. grant received, Zohra trust (loan) or Bank interest; for a payment Food, Fuel, Detergent, Salaries, GESCOM, Education, Miscellaneous or Zohra trust (transfer). Enter the amount, cheque number or UTR, and the paper receipt book and number.
3. Submit. The system makes the Journal Entry. To correct a mistake, cancel the voucher (never the Journal Entry) and enter it again.

## Receipts and Payments Account (Principal or Data Entry)

Open the report Receipts and Payments Account, choose the company and the dates (for a half-year 1 April to 30 September). It shows opening balances, receipts, payments and closing balances; the two totals must be equal. Opening balances before 1 April of a new year need an opening Journal Entry, which a Principal or the CA's helper makes once.

## After each exam (Data Entry)

1. New Result Sheet of Inmates: company, academic year, exam, exam date. Click Fill Students.
2. Enter marks obtained and the result (Pass, Fail or Absent) for each girl. The maximum marks come from her class.
3. Save and submit.

## After the Final exam: promotion (Data Entry or Principal)

1. Before promoting, make sure next year's Trust Academic Year exists.
2. On the submitted Final sheet check the Promotion Action of each girl. Pass in classes below the last is Promote, Fail is Repeat. Pass in the last class is Complete (choose where she goes). Absent has no default: choose one. Use Leave for a girl who leaves.
3. Click Promote. Next year's enrollments are made as Planned. If the strength would be exceeded, the system refuses everything: free a seat first (for example mark a leaver) and press Promote again.
4. At the start of the new year the Principal changes each Planned enrollment to Enrolled.

## Closing a month (Principal)

Create an Accounting Period for the unit covering the month and list the closed documents (Boarding Attendance, Material Consumption, Food Expenditure Statement, Purchase Invoice, ...). Nothing in that month can then be entered or changed.

## Not built yet

Report pack and print formats (slices 4 and 6).
