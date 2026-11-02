"""Build Zohra_Trust_Flowcharts.pdf: how the documents connect, why each one exists, and what it feeds.

    /home/ameer/Desktop/frappe-bench/env/bin/python apps/zohra_trust/docs/build_flowchart_pdf.py

Diagrams are Graphviz (the `dot` command) drawn from the DOT text below; the document reference is the DOCUMENTS list.
Change the text or the DOT here and run it again.
"""

import subprocess
import tempfile
from html import escape
from pathlib import Path

from weasyprint import HTML

HERE = Path(__file__).parent
OUT = HERE / "Zohra_Trust_Flowcharts.pdf"

STYLE = 'graph [fontname="Liberation Sans", fontsize=11, pad=0.2, nodesep=0.35, ranksep=0.55]; node [fontname="Liberation Sans", fontsize=10, shape=box, style="rounded,filled", fillcolor="#ffffff", color="#555555", margin="0.14,0.08"]; edge [fontname="Liberation Sans", fontsize=8.5, color="#666666", arrowsize=0.7];'
ENTER, KEEP, BUILD, STUDENT = "#dcefe6", "#e3e9f7", "#fdeccb", "#f1e1f4"

DIAGRAMS = {
    "big": (
        "1. The big picture",
        "Three layers. <b>Green</b>: what a person enters, as it happens. <b>Blue</b>: what ERPNext keeps for you (you never type into these). <b>Orange</b>: what is built from the records. Nothing is typed twice.",
        f"""digraph G {{ rankdir=LR; {STYLE}
  subgraph cluster_in {{ label="YOU ENTER"; style="rounded,filled"; fillcolor="#f4fbf7"; color="#8fbfa8";
    SR [label="Stock Reconciliation\\nopening stock (once)", fillcolor="{ENTER}"];
    PI [label="Purchase Invoice\\nevery day, paid in cash", fillcolor="{ENTER}"];
    MC [label="Material Consumption\\nevery day, kitchen use", fillcolor="{ENTER}"];
    CBV [label="Cash Bank Voucher\\nreceipts and payments", fillcolor="{ENTER}"];
    BA [label="Boarding Attendance\\nevery month", fillcolor="{ENTER}"];
    ST [label="Trust Student +\\nStudent Enrollment\\nat admission / each year", fillcolor="{ENTER}"];
    RS [label="Result Sheet of Inmates\\nafter the Final exam", fillcolor="{ENTER}"]; }}
  subgraph cluster_keep {{ label="KEPT BY ERPNEXT"; style="rounded,filled"; fillcolor="#f5f7fd"; color="#9db0dd";
    SL [label="Stock Ledger\\n(quantities in the store)", fillcolor="{KEEP}"];
    GL [label="General Ledger\\n(all money)", fillcolor="{KEEP}"];
    EN [label="Student Enrollment\\n(who is in which class, which year)", fillcolor="{KEEP}"];
    UP [label="Trust Unit Profile\\n(sanction, address, typed texts)", fillcolor="{KEEP}"]; }}
  subgraph cluster_out {{ label="BUILT FOR YOU"; style="rounded,filled"; fillcolor="#fff8ea"; color="#e0b565";
    FES [label="Food Expenditure Statement\\nmonthly 15-column sheet", fillcolor="{BUILD}"];
    RP [label="Receipts and Payments\\nAccount (report)", fillcolor="{BUILD}"];
    PACK [label="Report Pack\\n19-page PDF for the\\nMinority department", fillcolor="{BUILD}"]; }}
  SR -> SL; PI -> SL [label="quantity in"]; PI -> GL [label="expense, cash out"]; MC -> SL [label="quantity out"]; CBV -> GL;
  ST -> EN; EN -> BA [label="Fill Girls"]; EN -> RS [label="Fill Students"]; UP -> BA [label="strength, rate"]; RS -> EN [label="Promote:\\nnext year"];
  SL -> FES [label="old balance"]; PI -> FES [label="purchased"]; MC -> FES [label="consumed"]; GL -> FES [label="vegetables,\\nsalaries..."];
  GL -> RP; FES -> PACK; RP -> PACK; BA -> PACK; RS -> PACK; UP -> PACK [label="letter,\\nAppendix H"]; }}""",
    ),
    "money": (
        "2. Money and stock: what happens when you submit",
        "Each entry makes its effects by itself. You enter one document; ERPNext posts the rest. Purchases are <b>expenses at purchase</b>; the store is tracked in <b>quantities</b> only.",
        f"""digraph G {{ rankdir=LR; {STYLE}
  PI [label="Purchase Invoice\\n(Cash purchase, Update Stock,\\nIs Paid)", fillcolor="{ENTER}"];
  MC [label="Material Consumption\\n(Copy Yesterday)", fillcolor="{ENTER}"];
  CBV [label="Cash Bank Voucher\\n(Receipt / Payment)", fillcolor="{ENTER}"];
  SR [label="Stock Reconciliation\\n(opening count + rate)", fillcolor="{ENTER}"];
  SE [label="Stock Entry\\n(Material Issue)", fillcolor="{KEEP}"];
  JE [label="Journal Entry", fillcolor="{KEEP}"];
  SL [label="Stock Ledger\\n= quantity in the store", fillcolor="{KEEP}"];
  GL [label="General Ledger\\n= Dr expense / Cr cash,\\nDr cash / Cr income", fillcolor="{KEEP}"];
  PI -> SL [label="stock items:\\nquantity in"]; PI -> GL [label="Dr food / vegetables...\\nCr cash"];
  MC -> SE [label="made on submit"]; SE -> SL [label="quantity out\\n(no money posted)"];
  CBV -> JE [label="made on submit"]; JE -> GL [label="grant, loan, salaries,\\ntransfer..."]; SR -> SL [label="opening quantity\\nand rate"];
  GL -> RP [label="cash and bank,\\ncounter-accounts"]; RP [label="Receipts and Payments\\nAccount", fillcolor="{BUILD}"]; }}""",
    ),
    "month": (
        "3. The monthly sheets",
        "At month end two sheets are made. The <b>Food Expenditure Statement</b> is filled, never typed: old balance is the real stock at the end of the day before, valued at the last statement's closing rate; the rest comes from that month's purchases, kitchen use and spending.",
        f"""digraph G {{ rankdir=LR; {STYLE}
  EN [label="Student Enrollment\\n(status Enrolled)", fillcolor="{KEEP}"]; UP [label="Trust Unit Profile\\nsanction 150, Rs 850", fillcolor="{KEEP}"];
  BA [label="Boarding Attendance\\nFill Girls: one row per girl\\nhostel days, school days", fillcolor="{ENTER}"];
  BAT [label="Totals:\\nhostel attendance,\\nschool attendance,\\ngrant = girls x Rs 850", fillcolor="{BUILD}"];
  EN -> BA; UP -> BA; BA -> BAT;
  SL [label="Stock Ledger at the\\nend of the day before", fillcolor="{KEEP}"]; PREV [label="Last submitted statement\\n(closing rate)", fillcolor="{KEEP}"];
  PI [label="Purchase Invoices\\nof the month", fillcolor="{KEEP}"]; MC [label="Material Consumption\\nof the month", fillcolor="{KEEP}"]; GL [label="General Ledger\\nVegetables, Mutton, Milk,\\nFuel, Salaries, GESCOM", fillcolor="{KEEP}"];
  FES [label="Food Expenditure Statement\\nFill: old, purchased, total,\\nexpenditure, balance", fillcolor="{ENTER}"];
  FT [label="Totals: opening, monthly\\npurchase, total, expenditure,\\nremaining balance", fillcolor="{BUILD}"];
  SL -> FES [label="old quantity"]; PREV -> FES [label="old rate"]; PI -> FES; MC -> FES; GL -> FES; FES -> FT; FT -> NEXT [label="next month's rate"]; NEXT [label="next statement", fillcolor="{ENTER}"]; }}""",
    ),
    "student": (
        "4. A girl's year: admission, results, promotion",
        "The same girl is followed from admission to leaving. Last year's enrollment is never edited; promotion makes <b>next year's</b> enrollment as <b>Planned</b>, and a person confirms it.",
        f"""digraph G {{ rankdir=TB; {STYLE}
  A [label="Trust Student\\nname, hostel, admission date,\\nguardian", fillcolor="{STUDENT}"];
  B [label="Student Enrollment\\nacademic year, class, school,\\nregister no.  Status: Enrolled", fillcolor="{STUDENT}"];
  C [label="Boarding Attendance\\nevery month: days + grant", fillcolor="{ENTER}"];
  D [label="Result Sheet of Inmates (Final)\\nFill Students, marks, result", fillcolor="{ENTER}"];
  P [label="Promote  (button)", shape=diamond, style="filled", fillcolor="{BUILD}"];
  E [label="Pass, class below 10\\nPromote", fillcolor="{STUDENT}"]; F [label="Fail\\nRepeat (same class,\\nis_repeating)", fillcolor="{STUDENT}"];
  G [label="Pass in class 10\\nComplete + destination", fillcolor="{STUDENT}"]; H [label="Left with T.C.\\n(any class, also a Fail)", fillcolor="{STUDENT}"];
  E2 [label="Next year's Student Enrollment\\nStatus: Planned", fillcolor="{KEEP}"]; E3 [label="Person confirms:\\nPlanned becomes Enrolled", fillcolor="{ENTER}"];
  G2 [label="Trust Student: Passed Out", fillcolor="{KEEP}"]; H2 [label="Trust Student: Left\\nreason Left with T.C.\\nT.C. number and date later", fillcolor="{KEEP}"];
  A -> B -> C; B -> D; D -> P; P -> E; P -> F; P -> G; P -> H; E -> E2; F -> E2; E2 -> E3; E3 -> B [style=dashed, label="new year"]; G -> G2; H -> H2; }}""",
    ),
    "pack": (
        "5. The half-yearly Report Pack",
        "The Report Pack builds the PDF for the Minority department from the records, in filing order, and warns about anything missing before you print. Pages that are not generated (CA balance sheet, building plan, signed scans) are attached to the pack and merged in. The Grant Bill is pending Zohra's sample.",
        f"""digraph G {{ rankdir=LR; {STYLE}
  subgraph cluster_src {{ label="FROM THE RECORDS"; style="rounded,filled"; fillcolor="#f5f7fd"; color="#9db0dd";
    TS [label="Trust Settings\\nofficer bearers", fillcolor="{KEEP}"]; UP [label="Trust Unit Profile\\nletter text, Appendix H, address", fillcolor="{KEEP}"];
    RPT [label="Receipts and Payments\\nAccount", fillcolor="{KEEP}"]; BA [label="Boarding Attendance\\n(submitted months)", fillcolor="{KEEP}"];
    FES [label="Food Expenditure Statements\\n(submitted months)", fillcolor="{KEEP}"]; EMP [label="Employee\\n(active staff)", fillcolor="{KEEP}"]; RS [label="Result Sheet of Inmates", fillcolor="{KEEP}"]; }}
  subgraph cluster_pg {{ label="PAGES, IN FILING ORDER"; style="rounded,filled"; fillcolor="#fff8ea"; color="#e0b565";
    P1 [label="1 Letter + enclosures", fillcolor="{BUILD}"]; P2 [label="2 Receipts and payments", fillcolor="{BUILD}"]; P3 [label="3 Abstract of attendance", fillcolor="{BUILD}"];
    P4 [label="4 Food statements\\n(one per month, landscape)", fillcolor="{BUILD}"]; P5 [label="5 Appendix - H", fillcolor="{BUILD}"]; P6 [label="6 List of officer bearer", fillcolor="{BUILD}"];
    P7 [label="7 List of staff", fillcolor="{BUILD}"]; P8 [label="8 Result sheet", fillcolor="{BUILD}"]; P9 [label="9 Attendance registers\\n(per school and month, Kannada)", fillcolor="{BUILD}"]; }}
  UPL [label="Uploaded pages\\nCA pages, building plan,\\nsigned scans", fillcolor="{ENTER}"]; PACK [label="Report Pack\\nPreview with warnings,\\nDownload PDF", fillcolor="{ENTER}"]; PDF [label="One merged PDF\\nportrait + landscape", shape=note, fillcolor="{BUILD}"];
  TS -> P1; UP -> P1; RPT -> P2; BA -> P3; FES -> P4; UP -> P5; TS -> P6; EMP -> P7; RS -> P8; BA -> P9;
  P1 -> PACK; P2 -> PACK; P3 -> PACK; P4 -> PACK; P5 -> PACK; P6 -> PACK; P7 -> PACK; P8 -> PACK; P9 -> PACK; UPL -> PACK; PACK -> PDF; }}""",
    ),
}

# (document, why we made it, who and when, fed by, feeds)
DOCUMENTS = [
    ("Trust Settings", "One place for the trust's name, registration number and the officer bearers, so the letterhead is typed once.", "Administrator, once; edit when a bearer changes.", "Typed.", "Every report page's letterhead; List of officer bearer."),
    ("Trust Unit Profile (with Unit Sanction)", "What each hostel tracks, its address, the sanction history (strength and grant rate from a date) and the typed texts. A change of strength or rate is a new row, never an edit.", "Administrator, once; add a row when the department changes the sanction.", "Typed.", "Boarding Attendance (strength, rate), Letter, Appendix - H, food statement header."),
    ("Trust School, Trust Class, Trust Exam, Trust Academic Year", "Lists the system needs: the two schools, classes with their next class and maximum marks (data, not code), the exams, the year. Promotion and result sheets read them.", "Administrator, once (classes by seed_classes).", "Typed.", "Enrollment, Result Sheet, Promote."),
    ("Trust Student", "The girl: who she is, when she joined and left, her guardian, her T.C. number and date. Class and register number live on the enrollment.", "Office, at admission.", "Typed.", "Student Enrollment; result sheet (guardian's name)."),
    ("Student Enrollment", "One record per girl per academic year: class, school, register number. Last year's record is never edited. Refuses a girl above the sanctioned strength.", "Office, at admission and each year; Promote makes next year's.", "Trust Student; Promote.", "Boarding Attendance, Result Sheet, the roll."),
    ("Stock Reconciliation (standard)", "The go-live count of the store with a valuation rate for each item, so the first food statement has real opening amounts.", "Store, once.", "Physical count.", "Stock Ledger; Food Expenditure Statement (old balance)."),
    ("Purchase Invoice (standard)", "The daily shopping, paid in cash. Stock items add quantity; vegetables, mutton, milk and fuel are only expenses.", "Store or Data Entry, daily.", "Typed; items and heads chosen from lists.", "Stock Ledger, General Ledger, Food Expenditure Statement, Receipts and Payments."),
    ("Material Consumption", "What the kitchen used that day. Opens with yesterday's items so a day takes seconds. One per hostel per day.", "Store, daily.", "Copy Yesterday.", "Stock Entry (quantity out), Food Expenditure Statement."),
    ("Cash Bank Voucher", "Every receipt and payment that is not a shop purchase: grant, loan, bank interest, salaries, transfer to the Trust. Simple for low-literacy users: one form instead of a journal.", "Data Entry, as money moves.", "Typed.", "Journal Entry, General Ledger, Receipts and Payments, food statement (salaries and similar)."),
    ("Boarding Attendance", "Hostel days and school days of every girl for the month, and the grant (girls x rate). The abstract and the Kannada registers come from it.", "Data Entry, monthly.", "Student Enrollment, Unit Profile (Fill Girls).", "Abstract, attendance registers, grant."),
    ("Food Expenditure Statement", "The monthly 15-column sheet the department requires: old balance, purchased, total, expenditure, balance for each food item and amount-only rows. Built, not typed.", "Store, monthly, after the month's entries.", "Stock Ledger, Purchase Invoices, Material Consumption, General Ledger, previous statement.", "Next month's old rate; Report Pack."),
    ("Receipts and Payments Account (report)", "The account of money in and out for the period, with opening and closing cash and bank; both sides must equal.", "Anyone, any time; for the half-year.", "General Ledger.", "Report Pack."),
    ("Result Sheet of Inmates", "Marks and result of every girl after an exam, and (for the Final) what happens to her next: promote, repeat, complete, or leave with a T.C.", "Administrator, once a year (and per exam).", "Student Enrollment, Trust Class marks.", "Promote; Report Pack."),
    ("Report Pack", "Gathers all pages of the half-yearly report in filing order, shows what is missing, attaches pages that are not generated, and makes one PDF.", "Administrator or Principal, every half-year.", "All of the above; uploaded files; Employee.", "The PDF for the Minority department."),
    ("Employee (standard)", "The staff list: name, designation, qualification.", "Office, when staff change.", "Typed.", "List of staff page."),
]

PAGES = [
    ("Letter", "The covering letter to the District Minority Officer, with the seven enclosures listed.", "Trust Settings, Unit Profile letter text"),
    ("Receipts and payments account", "Shows where the money came from and went for the period; the department checks the grant is used.", "Receipts and Payments report"),
    ("Abstract statement of attendance", "One line per month: sanction strength, hostel attendance, school attendance.", "Boarding Attendance"),
    ("Food expenditure statement", "Month by month proof of what food was bought and used (landscape).", "Food Expenditure Statements"),
    ("Appendix - H", "The department's application form for the grant (free text typed once).", "Unit Profile"),
    ("List of officer bearer", "Who runs the trust.", "Trust Settings"),
    ("List of staff", "Who is employed at the hostel.", "Employee"),
    ("Result sheet of inmates", "Marks and result of every girl.", "Result Sheet of Inmates"),
    ("School: College attendance register", "Per school and month: days the school ran and each girl attended, signed by the school (Kannada heading).", "Boarding Attendance"),
    ("Grant bill", "Pending: Zohra has not yet sent the format. It will sum six months of attendance at Rs 850.", "Boarding Attendance (later)"),
]

CSS = """
@page { size: A4; margin: 15mm 13mm; @bottom-center { content: "Zohra Trust ERPNext: flowcharts  -  page " counter(page); font-size: 8pt; color: #777; } }
body { font-family: "Liberation Sans", Arial, sans-serif; font-size: 9.5pt; color: #222; line-height: 1.38; }
h1 { font-size: 22pt; margin: 0 0 4pt; color: #1b4d3e; } h2 { font-size: 14pt; color: #1b4d3e; border-bottom: 2px solid #1b4d3e; padding-bottom: 2pt; margin: 0 0 6pt; }
.sub { color: #555; font-size: 11pt; margin-bottom: 12pt; } .intro { margin-bottom: 8pt; }
.diagram { text-align: center; page-break-inside: avoid; } .diagram img { max-width: 100%; max-height: 215mm; }
.break { page-break-before: always; }
@page wide { size: A4 landscape; margin: 12mm 13mm; @bottom-center { content: "Zohra Trust ERPNext: flowcharts  -  page " counter(page); font-size: 8pt; color: #777; } }
.wide { page: wide; } .wide .diagram img { max-height: 150mm; width: 100%; } .first .diagram img { max-height: 100mm; width: auto; max-width: 100%; }
table { border-collapse: collapse; width: 100%; font-size: 8.5pt; } th, td { border: 1px solid #999; padding: 3pt 4pt; vertical-align: top; text-align: left; } th { background: #e6e6e6; } tr { page-break-inside: avoid; }
.legend span { display: inline-block; padding: 2pt 8pt; margin-right: 6pt; border: 1px solid #888; border-radius: 4pt; }
"""


def draw(name, dot_text, folder):
    dot_file = Path(folder) / f"{name}.dot"
    svg_file = Path(folder) / f"{name}.svg"
    dot_file.write_text(dot_text, encoding="utf-8")
    subprocess.run(["dot", "-Tsvg", str(dot_file), "-o", str(svg_file)], check=True)
    return svg_file


def build():
    with tempfile.TemporaryDirectory() as folder:
        parts = [
            '<h1>Zohra Trust ERPNext</h1><div class="sub">Flowcharts: which document is made, why, and how it flows.</div>',
            '<div class="legend"><span style="background:#dcefe6">entered by a person</span><span style="background:#e3e9f7">kept by ERPNext</span><span style="background:#fdeccb">built for you</span><span style="background:#f1e1f4">student record</span></div>',
            "<p class=intro>Read the diagrams first (arrows show where information moves), then the document reference: for each document, why we made it, who enters it and when, what feeds it and what it feeds.</p>",
        ]
        cover, parts = "".join(parts), []
        for n, (key, (title, intro, dot_text)) in enumerate(DIAGRAMS.items()):
            svg = draw(key, dot_text, folder)
            wide = key != "student"
            parts.append(f'<div class="{"break" if n else "first"} {"wide" if wide else ""}">{cover if n == 0 else ""}<h2>{title}</h2><p class="intro">{intro}</p><div class="diagram"><img src="{svg.as_uri()}"></div></div>')
        rows = "".join(f"<tr><td><b>{escape(a)}</b></td><td>{escape(b)}</td><td>{escape(c)}</td><td>{escape(d)}</td><td>{escape(e)}</td></tr>" for a, b, c, d, e in DOCUMENTS)
        parts.append(f'<div class="break"><h2>6. Document reference: why each document exists</h2><table><tr><th>Document</th><th>Why we made it</th><th>Who, when</th><th>Fed by</th><th>Feeds</th></tr>{rows}</table></div>')
        rows = "".join(f"<tr><td><b>{escape(a)}</b></td><td>{escape(b)}</td><td>{escape(c)}</td></tr>" for a, b, c in PAGES)
        parts.append(f'<div class="break"><h2>7. The pages of the half-yearly report</h2><p class="intro">What each page is for and where its content comes from.</p><table><tr><th>Page</th><th>What it shows, and why the department wants it</th><th>Built from</th></tr>{rows}</table></div>')
        html = f"<html><head><meta charset='utf-8'><style>{CSS}</style></head><body>{''.join(parts)}</body></html>"
        HTML(string=html, base_url=folder).write_pdf(OUT)
    print("wrote", OUT)


if __name__ == "__main__":
    build()
