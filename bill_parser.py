"""
bill_parser.py — turn the raw PDF text into a structured `Bill`.

Strategy: the "THIS BILL SUMMARY" table is the source of truth (it reconciles to the
penny). We parse that for the authoritative per-line numbers, then enrich each line
with the "why" (plan offer, device, promo) from the DETAILED CHARGES section.

Named `bill_parser` (not `parser`) on purpose — `parser` is a reserved stdlib name.
"""

import re

from config import MONEY, MONEY_OR_DASH, PHONE, PLAN_FAMILIES, DEVICE_HINTS
from utils import money
from models import Bill, Line
from extractor import extract_text


def trailing_amounts(text, n):
    """Return the last n money-or-dash tokens in `text` as floats (None for '-'),
    plus the substring that precedes them (the 'Type')."""
    matches = list(re.finditer(MONEY_OR_DASH, text))
    if len(matches) < n:
        return None, text
    last = matches[-n:]
    head = text[:last[0].start()].rstrip()
    return [money(m.group()) for m in last], head


def parse(pdf_path):
    """Read a T-Mobile bill PDF and return a populated `Bill`."""
    pages = extract_text(pdf_path)
    full = "\n".join(pages)
    lines_txt = full.split("\n")
    b = Bill()

    _parse_header(b, full)
    _parse_plan_family(b, full)
    _parse_section_totals(b, full)
    _parse_summary_table(b, lines_txt)
    _enrich_from_detailed_charges(b, lines_txt)
    return b


# --------------------------------------------------------------------------- #
# Header / plan / section totals                                              #
# --------------------------------------------------------------------------- #

def _parse_header(b, full):
    m = re.search(r"Account\s+Page\s*\n\s*([A-Za-z]{3} \d{1,2}, \d{4})\s+(\d{6,})", full)
    if m:
        b.issue_date, b.account = m.group(1), m.group(2)
    if not b.account:
        m = re.search(r"\bAccount\b[^\d]*(\d{8,})", full)
        if m:
            b.account = m.group(1)

    m = re.search(r"TOTAL DUE\s*\n\s*(\$[\d,]+\.\d{2})", full)
    if m:
        b.total_due = money(m.group(1))

    m = re.search(r"due by\s+([A-Za-z]{3} \d{1,2}, \d{4})", full)
    if m:
        b.due_date = m.group(1)

    m = re.search(r"last bill of (\$[\d,]+\.\d{2})\s*\n?\s*on ([A-Za-z]{3} \d{1,2}, \d{4})", full)
    if m:
        b.last_paid = f"{m.group(1)} on {m.group(2)}"

    m = re.search(r"AutoPay is scheduled for ([A-Za-z]{3} \d{1,2}, \d{4}) using "
                  r"(Visa|MasterCard|Mastercard|Discover|American Express|Amex|"
                  r"bank account|Bank Account|debit card|Debit Card|credit card|Credit Card)", full)
    if m:
        card = m.group(2)
        mask = re.search(r"\*{2,}\s?(\d{4})", full[m.end():m.end() + 60])
        if mask:
            card += f" ****{mask.group(1)}"
        b.autopay = f"{m.group(1)} via {card}"

    m = re.search(r"bill period\s+([A-Za-z]{3} \d{1,2})\s*-\s*([A-Za-z]{3} \d{1,2})", full)
    if not m:
        m = re.search(r"Charged in advance for bill period\s+([A-Za-z]{3} \d{1,2}) - ([A-Za-z]{3} \d{1,2})", full)
    if m:
        b.period = f"{m.group(1)} – {m.group(2)}"


def _parse_plan_family(b, full):
    m = re.search(r"With your T-Mobile ([^\n]+?) plan", full)
    if m:
        b.plan_greeting = m.group(1).strip()
    for name, desc in PLAN_FAMILIES:
        if re.search(rf"\b{re.escape(name)}\b", full):
            b.plan_family, b.plan_family_desc = name, desc
            break
    if not b.plan_family and b.plan_greeting:
        b.plan_family = b.plan_greeting


def _parse_section_totals(b, full):
    for label, attr in (("PLANS", "section_plans"),
                        ("EQUIPMENT", "section_equipment"),
                        ("SERVICES", "section_services")):
        m = re.search(rf"^{label}\b.*?({MONEY})", full, re.MULTILINE)
        if m:
            setattr(b, attr, money(m.group(1)))
    m = re.search(rf"T-Mobile fees & charges\s+({MONEY})", full)
    if m:
        b.tmo_fees = money(m.group(1))
    m = re.search(rf"Government taxes & fees\s+({MONEY})", full)
    if m:
        b.gov_fees = money(m.group(1))


# --------------------------------------------------------------------------- #
# The summary table (source of truth)                                         #
# --------------------------------------------------------------------------- #

def _parse_summary_table(b, lines_txt):
    summary = {}
    totals_row = None
    for ln in lines_txt:
        s = ln.strip()
        if s.startswith("Totals "):
            amts, _ = trailing_amounts(s, 4)
            if amts:
                totals_row = amts
            continue
        if s.startswith("Account "):
            amts, _ = trailing_amounts(s, 4)
            if amts:
                summary["Account"] = ("Account", amts)
            continue
        pm = re.match(rf"^({PHONE})\b(.*)$", s)
        if pm:
            ident, rest = pm.group(1), pm.group(2)
            amts, head = trailing_amounts(rest, 4)
            if amts:
                ltype = head.strip() or "Voice"
                summary[ident] = (ltype, amts)

    for ident, (ltype, amts) in summary.items():
        b.lines.append(Line(ident=ident, ltype=ltype,
                            plans=amts[0], equipment=amts[1],
                            services=amts[2], total=amts[3]))

    # The "Totals" row IS the authoritative bucket split.
    if totals_row:
        b.section_plans, b.section_equipment, b.section_services = (
            totals_row[0], totals_row[1], totals_row[2])
        if b.total_due is None:
            b.total_due = totals_row[3]

    if not b.lines:
        b.warnings.append(
            "No 'THIS BILL SUMMARY' table found — this PDF may be an older/different "
            "format. Per-line breakdown unavailable; only section totals were read.")


# --------------------------------------------------------------------------- #
# Enrichment from DETAILED CHARGES (the "why")                                #
# --------------------------------------------------------------------------- #

def _enrich_from_detailed_charges(b, lines_txt):
    # Restrict to the DETAILED CHARGES region so summary rows can't be mistaken
    # for device rows.
    det_start = 0
    for k, ln in enumerate(lines_txt):
        if ln.strip().startswith("DETAILED CHARGES"):
            det_start = k
            break
    det_lines = lines_txt[det_start:]

    _enrich_plan_offers(b, det_lines)
    _enrich_devices(b, det_lines)


def _enrich_plan_offers(b, det_lines):
    for ln in det_lines:
        s = ln.strip()
        m = re.match(rf"^(Account|{PHONE})\s+(.+?)\s+(Included|{MONEY})\b", s)
        if m and ("Offer" in s or "Plan" in s or "plan" in s or "Essentials" in s
                  or "Experience" in s or "Magenta" in s or "Go5G" in s or "Line" in s):
            ident, offer, amt = m.group(1), m.group(2).strip(), m.group(3)
            if re.search(MONEY, offer):      # offer name must not contain a $ amount
                continue
            tgt = b.find(ident)
            if tgt and not tgt.plan_offer:
                tgt.plan_offer = offer
                tgt.plan_offer_amt = amt


def _enrich_devices(b, det_lines):
    for i, ln in enumerate(det_lines):
        s = ln.strip()
        m = re.match(rf"^({PHONE})\s+(.+?)\s+({MONEY})$", s)
        if not m:
            continue
        ident, dev, amt = m.group(1), m.group(2).strip(), m.group(3)
        if re.search(MONEY, dev):            # reject summary rows (multiple $ amounts)
            continue

        # "look" window = this device's own detail lines, up to the next device row.
        win = [s]
        for j in range(i + 1, min(i + 6, len(det_lines))):
            nxt = det_lines[j].strip()
            if not nxt:
                break
            if re.match(rf"^{PHONE}\s+.+\s+{MONEY}$", nxt):
                break
            win.append(nxt)
        look = " ".join(win)

        # confirm it's a real device row (installment/ID/Balance detail, or device name)
        if not re.search(r"Installment\s+\d+\s+of\s+\d+|ID:\s|Balance:", look) and \
           not re.search(DEVICE_HINTS, s, re.I):
            continue

        tgt = b.find(ident)
        if not tgt:
            continue
        if tgt.device:                       # a line can finance multiple devices
            tgt.notes.append(f"additional device: {dev} ({amt})")
        else:
            tgt.device = dev
            inst = re.search(r"Installment\s+(\d+)\s+of\s+(\d+)", look)
            bal = re.search(r"Balance:\s*(\$[\d,]+\.\d{2})", look)
            promo = re.search(r"with\s+(\$[\d,]+\.\d{2})\s+([A-Z0-9][\w .&-]*?Promo)\b", look)
            bits = []
            if inst:
                bits.append(f"installment {inst.group(1)} of {inst.group(2)}")
            if bal:
                bits.append(f"balance {bal.group(1)}")
            tgt.device_detail = ", ".join(bits)
            if promo:
                tgt.device_promo = f"{promo.group(2).strip()} (-{promo.group(1)}/mo credit)"
