"""
models.py — the data structures that hold a parsed bill.

`Line`  = one row of the bill (a phone number, watch, tablet, or the shared 'Account').
`Bill`  = the whole bill: header info, section totals, and all its lines.
"""

from dataclasses import dataclass, field


@dataclass
class Line:
    ident: str                       # "(832) 931-5727", "Account", etc.
    ltype: str = ""                  # Voice / Mobile Internet / Wearable / Tablet ...
    plans: float = None
    equipment: float = None
    services: float = None
    total: float = None
    # enrichment ("the why"):
    plan_offer: str = ""             # e.g. "Essentials 4 Line Offer"
    plan_offer_amt: str = ""         # "Included" / "$25.00"
    device: str = ""                 # e.g. "iPhone 17 Pro"
    device_detail: str = ""          # "installment 7 of 24, balance $518.50"
    device_promo: str = ""           # promo/credit note
    notes: list = field(default_factory=list)


@dataclass
class Bill:
    account: str = ""
    issue_date: str = ""
    due_date: str = ""
    total_due: float = None
    last_paid: str = ""
    autopay: str = ""
    period: str = ""
    plan_family: str = ""
    plan_family_desc: str = ""
    plan_greeting: str = ""
    section_plans: float = None
    section_equipment: float = None
    section_services: float = None
    tmo_fees: float = None
    gov_fees: float = None
    lines: list = field(default_factory=list)
    warnings: list = field(default_factory=list)   # things we couldn't break down

    def find(self, ident):
        """Return the Line with this identifier, or None."""
        for line in self.lines:
            if line.ident == ident:
                return line
        return None
