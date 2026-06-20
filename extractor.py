"""
extractor.py — pull raw text out of a PDF.

This is the only module that talks to pdfplumber, so if you ever swap the PDF library
(or add OCR for scanned bills), this is the single place to change.
"""

import sys

try:
    import pdfplumber
except ImportError:
    sys.exit("Missing dependency. Run:  pip install pdfplumber")


def extract_text(pdf_path):
    """Return a list of strings, one per page. Accepts a file path or file-like object."""
    pages = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            pages.append(page.extract_text() or "")
    return pages
