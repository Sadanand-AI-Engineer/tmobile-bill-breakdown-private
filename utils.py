"""
utils.py — tiny shared helpers for money parsing and formatting.

These are pure functions with no dependencies on the rest of the project, so any
module can import them safely.
"""

from config import ASCII_MAP


def money(tok):
    """Turn a money token into a float. '-' (N/A) or empty -> None."""
    if tok is None:
        return None
    tok = tok.strip()
    if tok in ("-", ""):
        return None
    neg = tok.startswith("-")
    val = float(tok.replace("-", "").replace("$", "").replace(",", ""))
    return -val if neg else val


def fmt(v):
    """Format a float as currency; None -> a dash placeholder."""
    if v is None:
        return "    —   "
    if v < 0:
        return f"-${abs(v):,.2f}"
    return f"${v:,.2f}"


def asciiize(s):
    """Replace pretty Unicode glyphs with ASCII so they render in any PDF font."""
    for k, v in ASCII_MAP.items():
        s = s.replace(k, v)
    return s
