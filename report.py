"""
report.py — assemble the full plain-text report from a parsed `Bill`.

This module only lays out text; the numbers come from calculations.py and the phrasing
from explanations.py. Returns one big string (printed to screen and/or written to file).
"""

from config import TYPE_LABEL
from utils import fmt
from calculations import reconcile, per_person
from explanations import justify, pay_components


def hr(c="─", n=78):
    return c * n


def build_report(bill):
    out = []
    A = out.append

    fam = bill.plan_family or bill.plan_greeting or "Unknown plan"
    n_lines = len([l for l in bill.lines if l.ident != "Account"])

    _title(A, bill, fam, n_lines)
    _buckets(A, bill)
    _line_by_line(A, bill)
    rows, info = per_person(bill)
    _who_owes(A, bill, rows, info)
    _check_categories(A, bill)
    _check_total(A, bill)
    _warnings(A, bill)
    _summary(A, bill, fam, n_lines, rows, info)

    return "\n".join(out)


# --------------------------------------------------------------------------- #

def _title(A, bill, fam, n_lines):
    A(hr("═"))
    A(f"  T-MOBILE BILL BREAKDOWN  —  {fam} plan")
    A(hr("═"))
    if bill.plan_family_desc:
        A(f"  Plan: {fam} — {bill.plan_family_desc}")
    A(f"  Account #      : {bill.account or 'unknown'}")
    A(f"  Bill issued    : {bill.issue_date or 'unknown'}")
    if bill.period:
        A(f"  Service period : {bill.period}")
    A(f"  TOTAL DUE      : {fmt(bill.total_due)}   (due {bill.due_date or '?'})")
    if bill.autopay:
        A(f"  AutoPay        : {bill.autopay}")
    if bill.last_paid:
        A(f"  Last payment   : {bill.last_paid}")
    A(f"  Lines on bill  : {n_lines} line(s) + shared 'Account' charges")
    A("")


def _buckets(A, bill):
    A(hr())
    A("  WHAT MAKES UP THE TOTAL (top-level buckets)")
    A(hr())
    A(f"    Plans (service)      : {fmt(bill.section_plans)}")
    A(f"    Equipment (devices)  : {fmt(bill.section_equipment)}")
    A(f"    Services (add-ons)   : {fmt(bill.section_services)}")
    if bill.tmo_fees is not None or bill.gov_fees is not None:
        A(f"      ↳ of Plans, taxes & fees = "
          f"T-Mobile {fmt(bill.tmo_fees)} + Government {fmt(bill.gov_fees)}")
    A("")


def _line_by_line(A, bill):
    A(hr())
    A("  LINE-BY-LINE BREAKDOWN")
    A(hr())
    for l in bill.lines:
        label = TYPE_LABEL.get((l.ltype or "").lower().strip(),
                               l.ltype or ("Shared account" if l.ident == "Account" else "Line"))
        A(f"  ▸ {l.ident}   [{label}]")
        A(f"      Plans {fmt(l.plans)}   Equipment {fmt(l.equipment)}   "
          f"Services {fmt(l.services)}   →  TOTAL {fmt(l.total)}")
        A(f"      Why: {justify(l, bill)}")
        for note in l.notes:
            A(f"           • {note}")
        A("")


def _who_owes(A, bill, rows, info):
    acct = bill.find("Account")
    A(hr())
    A("  WHAT EACH PERSON OWES  (after splitting the shared plan cost)")
    A(hr())
    if info.get("per_line_plan") is not None:
        A(f"  All plan charges across the account add up to {fmt(info['total_plan'])} — "
          f"that's {fmt(info['per_line_plan'])} per line for all {info['n']} lines (everyone's plan is equal).")
        A(f"  On top of that, each line adds its own taxes & fees, its own phone payment "
          f"(if any), and a tiny share of account fees.")
        if info["extras"]:
            A(f"  (The {fmt(info['extras'])} of account-level fees is the part split evenly.)")
    elif info["method"] == "fair":
        A(f"  The shared plan bundle ({acct.plan_offer or 'plan offer'}) is {fmt(info['bundle'])} "
          f"and covers {len(info['covered'])} line(s),")
        A(f"  so it's split only across those = {fmt(info['bundle'] / max(len(info['covered']),1))} each "
          f"(that's each person's plan). Add-a-line pays its own plan in its row.")
        if info["extras"]:
            A(f"  The remaining {fmt(info['extras'])} of account fees is split evenly across all "
              f"{len(rows)} line(s).")
    elif info["method"] == "even-bundle":
        A(f"  Shared plan bundle {fmt(info['bundle'])} split across all {len(rows)} line(s); "
          f"account fees {fmt(info['extras'])} split evenly too.")
    else:
        A(f"  The {fmt(info.get('acct_total', 0))} 'Account' charge is shared and split evenly "
          f"across the {len(rows)} line(s).")
    A("")
    for l, bs, es, pay in rows:
        A(f"  ▸ {l.ident}  pays  {fmt(pay)}")
        A(f"        = {pay_components(l, bs, es, info)}")
    A("")
    psum = round(sum(p for _, _, _, p in rows), 2)
    A("  Add it all up:  " + "  +  ".join(fmt(p) for _, _, _, p in rows))
    A(f"               =  {fmt(psum)}   (bill total {fmt(bill.total_due)})  "
      f"{'✓ matches' if (bill.total_due is not None and abs(psum - bill.total_due) < 0.005) else '✗ check warnings'}")
    A("")


def _check_categories(A, bill):
    A(hr())
    A("  CHECK 1 — each category adds up to what the bill shows")
    A(hr())
    names = {"plans": "Plans (the monthly service)",
             "equipment": "Equipment (phone payments)",
             "services": "Services (extra add-ons)"}
    for attr in ("plans", "equipment", "services"):
        csum = round(sum((getattr(l, attr) or 0) for l in bill.lines), 2)
        sect = getattr(bill, f"section_{attr}")
        if sect is None:
            A(f"    {names[attr]}: the lines add to {fmt(csum)} (bill didn't list a "
              f"separate total to compare).")
        elif abs(csum - sect) < 0.005:
            A(f"    {names[attr]}: the lines add to {fmt(csum)} — same as the bill. Matches. ✓")
        else:
            A(f"    {names[attr]}: the lines add to {fmt(csum)} but the bill says "
              f"{fmt(sect)}. Does NOT match. ✗")
    A("")


def _check_total(A, bill):
    ok, linesum, residual, equation = reconcile(bill)
    A(hr())
    A("  CHECK 2 — do all the lines add up to the bill's TOTAL DUE?")
    A(hr())
    A("    total = " + equation)
    A(f"          = {fmt(linesum)}")
    A(f"    Bill's printed TOTAL DUE = {fmt(bill.total_due)}")
    if bill.total_due is None:
        A("    [?] Could not read the printed total — cannot verify.")
    elif ok:
        A("    [OK ✓] Everything adds up to the printed total exactly.")
    else:
        A(f"    [MISMATCH ✗] Left over and not explained = {fmt(residual)}")
        bill.warnings.append(
            f"${residual:,.2f} on the bill was NOT attributed to any line. "
            "Likely a one-time charge, late fee, account-level credit, or a section this "
            "parser didn't recognize. Check the DETAILED CHARGES pages of the PDF.")
    A("")


def _warnings(A, bill):
    A(hr())
    A("  COULD NOT FULLY BREAK DOWN  (read this if anything looks off)")
    A(hr())
    if bill.warnings:
        for w in bill.warnings:
            A(f"    ⚠ {w}")
    else:
        A("    Nothing — every dollar was explained and all checks passed. ✓")
    for l in bill.lines:
        if (l.total or 0) != 0 and not l.plan_offer and not l.device and l.ident != "Account":
            A(f"    ⚠ {l.ident}: total {fmt(l.total)} has no matching plan/device detail "
              f"in DETAILED CHARGES (amount still counted, reason unknown).")
    A("")


def _summary(A, bill, fam, n_lines, rows, info):
    A(hr("═"))
    A("  SUMMARY — WHO PAYS WHAT")
    A(hr("═"))
    A(f"  {fam} plan, {n_lines} line(s). Bill total {fmt(bill.total_due)}, due "
      f"{bill.due_date or '?'}.")
    if info.get("per_line_plan") is not None:
        A(f"  Everyone's plan is {fmt(info['per_line_plan'])} ({fmt(info['total_plan'])} total ÷ "
          f"{info['n']} lines). Differences below are just taxes and phone payments.")
    elif info["method"] == "fair":
        A(f"  Each covered line's plan is {fmt(info['bundle'] / max(len(info['covered']),1))}; "
          f"add-a-line pays its own.")
    A("")
    for l, bs, es, pay in rows:
        A(f"  • {l.ident} pays {fmt(pay)}   ({pay_components(l, bs, es, info)})")
    A("")
    A(f"  Reconciliation: {'PASSED ✓ — every dollar is accounted for.' if reconcile(bill)[0] else 'SEE WARNINGS ABOVE ✗'}")
    A(hr("═"))
