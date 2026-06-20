"""
calculations.py — the money math (no text, no I/O).

- reconcile():  do all the line totals add up to the printed total?
- per_person(): split the shared 'Account' charge fairly so we can say what each
                phone number actually owes.
- _alloc():     split an amount across IDs so the pieces sum to it exactly.
"""

from utils import money, fmt


def reconcile(bill):
    """Return (ok, line_sum, residual, equation).
    `ok` is True when the lines add up to the printed total."""
    s = sum((l.total or 0) for l in bill.lines)
    eq_terms = [f"{fmt(l.total)} [{l.ident}]" for l in bill.lines]
    equation = "  +  ".join(eq_terms) if eq_terms else "(no lines parsed)"
    residual, ok = None, False
    if bill.total_due is not None:
        residual = round(bill.total_due - s, 2)
        ok = abs(residual) < 0.005
    return ok, round(s, 2), residual, equation


def _alloc(amount, idents):
    """Split `amount` across idents so the pieces sum to it EXACTLY (penny-safe)."""
    out = {i: 0.0 for i in idents}
    if not idents or not amount:
        return out
    per = round(amount / len(idents), 2)
    for i in idents:
        out[i] = per
    drift = round(amount - per * len(idents), 2)
    if abs(drift) >= 0.005:
        out[idents[-1]] = round(out[idents[-1]] + drift, 2)
    return out


def per_person(bill):
    """Work out what each phone number really owes.

    Fair method: the multi-line plan bundle (e.g. the $100 '4 Line Offer') is the plan
    cost for the lines it covers, so it's split ONLY across those lines. Any leftover
    account charge (small account-level taxes/credits) is split evenly across everyone.
    A line added on its own ('add-a-line') already carries its own plan cost in its row,
    so it gets NO slice of the bundle.

    Returns (rows, info) where rows = [(Line, bundle_slice, extra_slice, pay)].
    """
    people = [l for l in bill.lines if l.ident != "Account"]
    acct = bill.find("Account")
    n = len(people)
    info = {"bundle": 0.0, "extras": 0.0, "covered": [], "method": "even"}
    if n == 0:
        return [], info

    acct_total = (acct.total if acct else 0.0) or 0.0

    # The bundle base = the Account row's plan-offer dollar amount (e.g. $100.00).
    base = None
    if acct and acct.plan_offer_amt and acct.plan_offer_amt.startswith("$"):
        base = money(acct.plan_offer_amt)

    covered = [l.ident for l in people if (l.plan_offer_amt or "").lower() == "included"]

    if base is not None and covered:
        bundle, extras, method = base, round(acct_total - base, 2), "fair"
        bundle_alloc = _alloc(bundle, covered)
    elif base is not None:
        bundle, extras, method = base, round(acct_total - base, 2), "even-bundle"
        bundle_alloc = _alloc(bundle, [l.ident for l in people])
    else:
        bundle, extras, method = 0.0, acct_total, "even"
        bundle_alloc = {l.ident: 0.0 for l in people}

    extra_alloc = _alloc(extras, [l.ident for l in people])

    # Each line's underlying PLAN price (separate from taxes) -> can we say "$X each"?
    line_plan = {}
    for l in people:
        if l.ident in covered and covered:
            line_plan[l.ident] = round(bundle / len(covered), 2)
        elif l.plan_offer_amt and l.plan_offer_amt.startswith("$"):
            line_plan[l.ident] = money(l.plan_offer_amt)
        else:
            line_plan[l.ident] = None
    vals = [v for v in line_plan.values() if v is not None]
    total_plan = round(sum(vals), 2) if vals else 0.0
    all_equal = (len(vals) == len(people) and len(vals) > 0
                 and len({round(v, 2) for v in vals}) == 1)
    per_line_plan = vals[0] if all_equal else None

    info.update(bundle=bundle, extras=extras, covered=covered, method=method,
                acct_total=acct_total, line_plan=line_plan,
                total_plan=total_plan, per_line_plan=per_line_plan, n=n)

    rows = []
    for l in people:
        bs = bundle_alloc.get(l.ident, 0.0)
        es = extra_alloc.get(l.ident, 0.0)
        rows.append((l, bs, es, round((l.total or 0) + bs + es, 2)))
    return rows, info
