#!/usr/bin/env python3
"""
main.py — entry point for the T-Mobile Bill Breakdown tool.

This file only wires things together (parse -> report -> output). All the real work
lives in the other modules:

    extractor.py     read text from the PDF
    bill_parser.py   text  -> Bill object
    calculations.py  the money math (reconcile, per-person split)
    explanations.py  plain-English phrasing
    report.py        assemble the printed report
    pdf_writer.py    write the report to a PDF
    models.py        Line / Bill data structures
    config.py        regex patterns + reference data
    utils.py         money() / fmt() helpers

Usage:
    python main.py BILL.pdf [--pdf [OUT.pdf]] [--txt [OUT.txt]]

Examples:
    python main.py bill.pdf
    python main.py bill.pdf --pdf
    python main.py bill.pdf --pdf "C:\\out\\breakdown.pdf" --txt
"""

import os
import sys

from bill_parser import parse
from report import build_report
from pdf_writer import write_pdf


def _flag_path(flags, name, stem, default_ext):
    """If `name` is present, return the path to write (explicit, or a default name)."""
    if name not in flags:
        return None
    i = flags.index(name)
    nxt = flags[i + 1] if i + 1 < len(flags) else ""
    if nxt and not nxt.startswith("--"):
        return nxt
    return f"{stem}_breakdown{default_ext}"


def main():
    args = sys.argv[1:]
    if not args or args[0] in ("-h", "--help"):
        sys.exit("Usage: python main.py BILL.pdf [--pdf [OUT.pdf]] [--txt [OUT.txt]]")

    pdf_in, flags = args[0], args[1:]
    stem = os.path.splitext(os.path.basename(pdf_in))[0]

    bill = parse(pdf_in)
    text = build_report(bill)
    print(text)

    txt_out = _flag_path(flags, "--txt", stem, ".txt")
    if txt_out:
        with open(txt_out, "w", encoding="utf-8") as f:
            f.write(text)
        print(f"\nSaved text to: {txt_out}")

    pdf_out = _flag_path(flags, "--pdf", stem, ".pdf")
    if pdf_out:
        write_pdf(text, pdf_out)
        print(f"Saved PDF to:  {pdf_out}")


if __name__ == "__main__":
    main()
