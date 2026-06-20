"""
pdf_writer.py — render the plain-text report into a simple, readable PDF.

Uses a monospace font so the alignment is preserved, and wraps long lines so nothing
runs off the page.
"""

import sys
import textwrap

from utils import asciiize


def write_pdf(report_text, out_path):
    try:
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import letter
    except ImportError:
        sys.exit("PDF output needs reportlab. Run:  pip install reportlab")

    W, H = letter
    margin, font, size, leading = 36, "Courier", 8, 10
    max_chars = int((W - 2 * margin) / (size * 0.6)) - 1     # chars that fit per line

    c = canvas.Canvas(out_path, pagesize=letter)
    c.setFont(font, size)
    y = H - margin
    for raw in report_text.split("\n"):
        line = asciiize(raw)
        if len(line) > max_chars:
            indent = len(line) - len(line.lstrip())
            pieces = textwrap.wrap(line, width=max_chars,
                                   subsequent_indent=" " * (indent + 4),
                                   break_long_words=False, break_on_hyphens=False) or [line]
        else:
            pieces = [line]
        for piece in pieces:
            if y < margin:
                c.showPage(); c.setFont(font, size); y = H - margin
            c.drawString(margin, y, piece)
            y -= leading
    c.showPage()
    c.save()
