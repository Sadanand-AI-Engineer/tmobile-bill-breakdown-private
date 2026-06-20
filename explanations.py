"""
explanations.py — turn one line's numbers into plain-English phrases.

- justify():        the one-line "Why:" reason in the line-by-line breakdown.
- pay_components(): the "= a + b + c" breakdown of what one person pays.

These produce text only; all the math lives in calculations.py.
"""

from utils import money, fmt


def justify(line, bill):
    """One-line plain-English reason for this line's total."""
    parts = []

    if line.ident == "Account":
        if line.plan_offer:
            parts.append(f"shared plan base '{line.plan_offer}' ({line.plan_offer_amt})")
        if bill.tmo_fees is not None or bill.gov_fees is not None:
            parts.append("plus account-level taxes & fees")
        if not parts:
            parts.append("account-level charges")
        return "; ".join(parts)

    # plan portion
    if line.plan_offer:
        if line.plan_offer_amt.lower() == "included":
            parts.append(f"plan '{line.plan_offer}' included in the multi-line offer; "
                         f"this charge is the line's share of taxes & fees")
        else:
            parts.append(f"plan '{line.plan_offer}' billed at {line.plan_offer_amt} "
                         f"(+ its taxes & fees)")
    elif line.plans:
        parts.append(f"plan/taxes for this line = {fmt(line.plans)}")

    # equipment portion
    if line.equipment is not None and line.equipment != 0:
        if line.device:
            note = f"device {line.device}"
            if line.device_detail:
                note += f" ({line.device_detail})"
            if line.device_promo:
                note += f", {line.device_promo}"
            note += f" → {fmt(line.equipment)}/mo"
            parts.append(note)
        else:
            parts.append(f"equipment installment {fmt(line.equipment)}")
    elif line.equipment == 0 and line.device:
        parts.append(f"device {line.device} fully offset by promo credit → $0.00")

    # services
    if line.services:
        parts.append(f"add-on services {fmt(line.services)}")

    return "; ".join(parts) if parts else "charge present but no detail line matched"


def pay_components(line, bundle_slice, extra_slice, info):
    """Plain-English '= a + b + c' breakdown of what one number pays."""
    parts = []
    covered = line.ident in info.get("covered", [])
    own_plan = (money(line.plan_offer_amt)
                if (line.plan_offer_amt and line.plan_offer_amt.startswith("$")) else None)

    if bundle_slice and covered:
        parts.append(f"{fmt(bundle_slice)} (your plan)")
        if line.plans:
            parts.append(f"{fmt(line.plans)} (your taxes & fees)")
    elif own_plan is not None and line.plans is not None:
        taxes = round(line.plans - own_plan, 2)
        parts.append(f"{fmt(own_plan)} (your plan)")
        if abs(taxes) >= 0.005:
            parts.append(f"{fmt(taxes)} (your taxes & fees)")
    elif line.plans is not None:
        parts.append(f"{fmt(line.plans)} (this line's plan taxes & fees)")

    if line.equipment is not None:
        if line.equipment == 0:
            parts.append("$0.00 (phone — fully covered by promo)")
        elif line.equipment < 0:
            parts.append(f"{fmt(line.equipment)} (phone promo credit)")
        else:
            dev = f" for {line.device}" if line.device else ""
            parts.append(f"{fmt(line.equipment)} (phone payment{dev})")

    if line.services:
        parts.append(f"{fmt(line.services)} (add-on services)")

    if extra_slice:
        parts.append(f"{fmt(extra_slice)} (share of account fees)")

    return " + ".join(parts)
