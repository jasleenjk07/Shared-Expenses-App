"""Name normalization and member resolution for CSV import."""

import re
from datetime import date
from typing import Optional

# Canonical name aliases from the messy spreadsheet
NAME_ALIASES = {
    "priya s": "Priya",
    "priya": "Priya",
    "rohan": "Rohan",
    "aisha": "Aisha",
    "meera": "Meera",
    "dev": "Dev",
    "sam": "Sam",
}

# Known flatmate membership timeline (used when bootstrapping group from CSV)
DEFAULT_MEMBERSHIP = {
    "Aisha": {"joined": date(2026, 2, 1), "left": None},
    "Rohan": {"joined": date(2026, 2, 1), "left": None},
    "Priya": {"joined": date(2026, 2, 1), "left": None},
    "Meera": {"joined": date(2026, 2, 1), "left": date(2026, 3, 30)},
    "Dev": {"joined": date(2026, 2, 8), "left": date(2026, 3, 15)},
    "Sam": {"joined": date(2026, 4, 8), "left": None},
}

SETTLEMENT_KEYWORDS = ("paid back", "settlement", "settle up", "repay", "repaid", "not an expense")


def normalize_name(raw: str) -> Optional[str]:
    if not raw or not str(raw).strip():
        return None
    cleaned = str(raw).strip()
    key = cleaned.lower()
    if key in NAME_ALIASES:
        return NAME_ALIASES[key]
    # Title-case known first names
    for canonical in DEFAULT_MEMBERSHIP:
        if key == canonical.lower():
            return canonical
    return cleaned


def is_unknown_person(name: str) -> bool:
    normalized = normalize_name(name)
    if not normalized:
        return True
    return normalized not in DEFAULT_MEMBERSHIP


def looks_like_settlement(description: str, notes: str, split_type: str) -> bool:
    desc = description.lower()
    text = f"{description} {notes}".lower()
    if any(kw in text for kw in SETTLEMENT_KEYWORDS):
        return True
    if "paid" in desc and "back" in desc:
        return True
    if "deposit" in desc and "paid" in notes.lower():
        return True
    if not (split_type or "").strip() and "back" in desc:
        return True
    return False


def normalize_description(desc: str) -> str:
    if not desc:
        return ""
    return re.sub(r"[^a-z0-9]", "", desc.lower())


def _description_tokens(desc: str) -> set:
    return set(re.findall(r"[a-z0-9]+", desc.lower()))


def descriptions_similar(a: str, b: str) -> bool:
    na, nb = normalize_description(a), normalize_description(b)
    if not na or not nb:
        return False
    if na == nb:
        return True
    if na in nb or nb in na:
        return True
    ta, tb = _description_tokens(a), _description_tokens(b)
    overlap = ta & tb
    if len(overlap) >= 2 and len(overlap) >= min(len(ta), len(tb)) - 1:
        return True
    return False
