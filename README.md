# T-Mobile Bill Breakdown (modular)

A no-LLM tool that reads a T-Mobile bill PDF and explains, in plain English, who owes
what — and proves every dollar adds up to the printed total.

## How to run

```bash
pip install -r requirements.txt
python main.py BILL.pdf                 # print to screen
python main.py BILL.pdf --pdf           # also save <name>_breakdown.pdf
python main.py BILL.pdf --pdf out.pdf --txt   # save PDF + text to chosen paths
```

## File layout (each file = one job)

```
main.py            entry point — only wires the steps together, no logic
config.py          regex patterns + reference data (plan names, labels, ASCII map)
utils.py           money() / fmt() / asciiize() — tiny shared helpers
models.py          Line and Bill data structures
extractor.py       read text out of the PDF (the only file that uses pdfplumber)
bill_parser.py     PDF text  ->  Bill object (header, summary table, enrichment)
calculations.py    the money math: reconcile() and the per-person split
explanations.py    plain-English phrasing for each line
report.py          assembles the full printed report
pdf_writer.py      writes the report to a PDF
```

### How the pieces call each other

```
main.py
  ├─ bill_parser.parse(pdf)        -> Bill        (uses extractor, models, config, utils)
  ├─ report.build_report(bill)     -> text        (uses calculations, explanations, config, utils)
  └─ pdf_writer.write_pdf(text)    -> PDF file     (uses utils)
```

No circular imports: `config` and `utils` are at the bottom, everything else builds on top.

## Scope & limitations (important)

This is reliable for the standard consumer **postpaid** "Bill Summary" PDF, because that
format contains a self-reconciling per-line table. It is **not** guaranteed to handle
every possible bill. Known gaps:

- Only validated on a small number of bills — other layouts may parse incompletely.
- Prepaid / Metro / Business / Home-Internet-only bills use different formats.
- One-time charges, late fees, mid-cycle plan changes, and proration may not be
  attributed per line.
- Older bills without the summary table fall back to section totals only.
- Scanned/photo PDFs (no text layer) won't work without OCR.
- The plan-name list is a fixed snapshot; brand-new plan names won't be recognized.

The safety net: the tool **reconciles**. If it can't account for a dollar, it prints a
warning under "COULD NOT FULLY BREAK DOWN" instead of hiding it. Trust that check.
