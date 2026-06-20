# T-Mobile Bill Breakdown

> **Your bill stays on your computer. Period.**
> No AI. No internet. No servers. Your data never leaves your machine.

A tool that reads your T-Mobile bill PDF and explains — in plain English — who owes
what, and **proves** every dollar adds up to the printed total.

---

## Why this exists

Your T-Mobile bill is confusing. Shared plan costs, device installments, promo credits,
taxes split across lines — it's hard to know what each person actually owes.

Most "bill analyzer" tools send your PDF to a server or an AI. **This one does not.**

- ✅ Runs 100% on your own computer
- ✅ No AI, no LLM, no API calls
- ✅ No data sent to any website or server
- ✅ Your bill PDF never leaves your machine
- ✅ Works offline — no internet needed after install
- ✅ Open source — you can read every line of code and verify this yourself

The code is split into small, readable files. If you want to confirm no data is sent
anywhere, open `extractor.py` — it reads your PDF locally using `pdfplumber`, a
standard Python library. That's it. Nothing is uploaded.

---

## What it does

- Reads the official T-Mobile bill PDF (downloaded from t-mobile.com or the T-Life app)
- Breaks down every line: each phone number, watch, tablet, or hotspot — what it costs and **why**
- Splits the shared plan cost fairly so each person knows their exact amount
- Proves the math: `line 1 + line 2 + ... = printed total` — or tells you what it couldn't explain
- Saves the breakdown as a PDF you can share

---

## Quick start

### Windows

```powershell
# 1. Open PowerShell and go to the project folder
cd "C:\My Projects\tmobilebreakdown"

# 2. Create a virtual environment
python -m venv venv

# 3. Activate it
venv\Scripts\Activate.ps1

# If you get a permissions error, run this first, then try step 3 again:
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# 4. Install dependencies
pip install -r requirements.txt

# 5. Run it
python main.py "C:\path\to\your\June2026BillSummary.pdf"

# Save output as PDF too
python main.py "C:\path\to\your\June2026BillSummary.pdf" --pdf

# Save as both PDF and text file
python main.py "C:\path\to\your\June2026BillSummary.pdf" --pdf --txt
```

### Mac

```bash
# 1. Open Terminal and go to the project folder
cd ~/Projects/tmobilebreakdown

# 2. Create a virtual environment
python3 -m venv venv

# 3. Activate it
source venv/bin/activate

# 4. Install dependencies
pip install -r requirements.txt

# 5. Run it
python main.py ~/Downloads/June2026BillSummary.pdf

# Save output as PDF too
python main.py ~/Downloads/June2026BillSummary.pdf --pdf

# Save as both PDF and text file
python main.py ~/Downloads/June2026BillSummary.pdf --pdf --txt
```

---

## Where to get your bill PDF

1. Go to **t-mobile.com** → sign in → **Bill** → **Download PDF**
2. Or open the **T-Life app** → Bill → Download

Use the "Bill Summary" PDF. It must be the official downloaded PDF — a photo or scan of
a printed bill won't work (no text layer).

---

## Output files

| Flag | What it saves | Default filename |
|------|--------------|-----------------|
| *(none)* | Prints to screen only | — |
| `--pdf` | Saves a PDF breakdown | `<billname>_breakdown.pdf` |
| `--txt` | Saves a plain text file | `<billname>_breakdown.txt` |
| `--pdf myfile.pdf` | Saves PDF to a specific path | your chosen name |

Files are saved in the same folder you run the command from.

---

## File structure

```
main.py          Entry point — only wires steps together, no logic
config.py        Regex patterns + reference data (plan names, line labels)
utils.py         Shared helpers: money(), fmt(), asciiize()
models.py        Line and Bill data structures
extractor.py     Reads text from the PDF (only file using pdfplumber)
bill_parser.py   PDF text → Bill object (header, summary table, enrichment)
calculations.py  Money math: reconcile() and per-person split
explanations.py  Plain-English phrasing per line
report.py        Assembles the full printed report
pdf_writer.py    Writes the report to a PDF file
requirements.txt pip dependencies
```

---

## Requirements

- Python 3.8 or higher
- `pdfplumber` — reads text from PDFs
- `reportlab` — writes the breakdown PDF (only needed for `--pdf`)

Install both with:
```bash
pip install -r requirements.txt
```

---

## What it handles

- Any number of lines (5, 10, 12+)
- Line types: Voice (phone), Mobile Internet / hotspot, Wearable (watch), Tablet, DIGITS
- Plan families: Experience Beyond / More, Essentials, Go5G, Magenta, Magenta MAX, Simple Choice, ONE
- Device installments with promo credits (including negative net charges)
- Multiple devices on one line
- Add-a-line (AAL) — fairly excluded from the shared bundle split
- AutoPay info, taxes & fees split (T-Mobile vs government), billing period

## Known limitations

- Only validated on standard consumer **postpaid** bills — Prepaid / Metro / Business /
  Home-Internet-only use different formats and may not parse fully
- One-time charges, late fees, mid-cycle changes, and proration may not be attributed
  per line (the reconciliation check will flag any leftover amount)
- Older bills without the "THIS BILL SUMMARY" table fall back to section totals only
- Scanned / photographed bills (no text layer) need OCR first
- Plan names added by T-Mobile after this version won't be recognized by name

The safety net: if the tool can't account for a dollar, it prints a warning under
**"COULD NOT FULLY BREAK DOWN"** instead of silently hiding it.

---

## License

MIT — do whatever you want with it.
