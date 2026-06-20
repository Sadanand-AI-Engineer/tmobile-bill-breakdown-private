"""
config.py — constants only (no logic).

Holds the regular-expression patterns and the reference data (plan names, line-type
labels, ASCII map) used across the project. Keeping these in one place makes them easy
to update when T-Mobile changes wording or adds new plans.
"""

# --- regex building blocks -------------------------------------------------- #
MONEY = r"-?\$[\d,]+\.\d{2}"                 # $5.90, -$3.34, $1,234.56
MONEY_OR_DASH = rf"{MONEY}|(?<=\s)-(?=\s)"   # money, or a bare '-' (N/A) between spaces
PHONE = r"\(\d{3}\)\s?\d{3}-\d{4}"           # (832) 931-5727


# --- reference data --------------------------------------------------------- #
# Known plan families, longest/most-specific first so we match correctly.
PLAN_FAMILIES = [
    ("Experience Beyond", "Premium postpaid plan (replaced Go5G Next, Apr 2025). Taxes & fees extra."),
    ("Experience More",   "Mid/premium postpaid plan (replaced Go5G Plus, Apr 2025). Taxes & fees extra."),
    ("Essentials Saver",  "Lowest-cost postpaid plan, limited features."),
    ("Essentials",        "Entry-level unlimited plan. Taxes & fees billed separately."),
    ("Go5G Next",         "Legacy premium plan with yearly upgrades (pre-2025)."),
    ("Go5G Plus",         "Legacy premium plan (pre-2025)."),
    ("Go5G",              "Legacy plan (pre-2025)."),
    ("Magenta MAX",       "Legacy top-tier unlimited plan (tax-inclusive)."),
    ("Magenta",           "Legacy unlimited plan (tax-inclusive)."),
    ("Simple Choice",     "Older legacy plan."),
    ("ONE",               "Older legacy 'T-Mobile ONE' plan."),
]

# How a line "Type" in the summary table maps to a human label.
TYPE_LABEL = {
    "voice": "Phone line",
    "mobile internet": "Mobile Internet / hotspot line",
    "wearable": "Wearable (smartwatch) line",
    "tablet": "Tablet line",
    "digits": "DIGITS extra-number line",
    "data": "Data line",
}

# Device-name hints used to confirm a row really is a financed device.
DEVICE_HINTS = (r"iPhone|Galaxy|Pixel|razr|Watch|iPad|Tab|SyncUP|Hotspot|"
                r"Gateway|moto|OnePlus|Flip|Fold")

# Map the pretty Unicode used on screen to plain ASCII, so the PDF renders with the
# built-in Courier font on any machine (no special fonts needed).
ASCII_MAP = {"─": "-", "═": "=", "▸": ">", "•": "*", "↳": "->", "→": "->",
             "✓": "OK", "✗": "X", "–": "-", "—": "-", "−": "-"}
