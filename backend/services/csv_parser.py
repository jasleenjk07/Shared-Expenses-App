"""Parse dates and amounts from messy CSV values."""

import re
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from typing import Optional, Tuple


def parse_amount(raw) -> Tuple[Optional[Decimal], list]:
    """Return (amount, anomalies)."""
    anomalies = []
    if raw is None or (isinstance(raw, float) and str(raw) == "nan"):
        return None, [{"type": "MISSING_AMOUNT", "desc": "Amount is empty"}]

    text = str(raw).strip()
    if text == "":
        return None, [{"type": "MISSING_AMOUNT", "desc": "Amount is empty"}]

    had_comma = "," in text
    cleaned = text.replace(",", "")
    try:
        value = Decimal(cleaned)
    except InvalidOperation:
        return None, [{"type": "INVALID_AMOUNT", "desc": f"Cannot parse amount: {raw}"}]

    if had_comma:
        anomalies.append(
            {
                "type": "COMMA_IN_AMOUNT",
                "desc": f"Amount contained comma separator: {raw}",
                "action": f"Parsed as {value}",
            }
        )

    original = value
    if value != value.quantize(Decimal("0.01")):
        rounded = value.quantize(Decimal("0.01"))
        anomalies.append(
            {
                "type": "AMOUNT_ROUNDING",
                "desc": f"Amount {original} has extra precision",
                "action": f"Rounded to {rounded}",
            }
        )
        value = rounded

    if value == 0:
        anomalies.append(
            {
                "type": "ZERO_AMOUNT",
                "desc": "Amount is zero",
                "action": "Row skipped — zero-amount expense not imported",
            }
        )

    if value < 0:
        anomalies.append(
            {
                "type": "NEGATIVE_AMOUNT",
                "desc": f"Negative amount {value} detected",
                "action": "Treated as refund — reduces payer's share of the expense",
            }
        )

    return value, anomalies


def parse_date(raw, row_context: Optional[date] = None) -> Tuple[Optional[date], list]:
    """Parse date from multiple formats. Assumes DD-MM-YYYY for ambiguous numeric dates."""
    anomalies = []
    if raw is None or str(raw).strip() == "":
        return None, [{"type": "MISSING_DATE", "desc": "Date is empty"}]

    text = str(raw).strip()

    # Mar-14 style
    m = re.match(r"^([A-Za-z]{3})-(\d{1,2})$", text)
    if m:
        month_str, day = m.group(1), int(m.group(2))
        year = row_context.year if row_context else 2026
        try:
            dt = datetime.strptime(f"{day}-{month_str}-{year}", "%d-%b-%Y")
            anomalies.append(
                {
                    "type": "DATE_FORMAT_INCONSISTENT",
                    "desc": f"Date '{text}' uses month-day abbreviation format",
                    "action": f"Interpreted as {dt.date().isoformat()} (year inferred from context)",
                }
            )
            return dt.date(), anomalies
        except ValueError:
            pass

    formats = ["%d-%m-%Y", "%Y-%m-%d", "%m-%d-%Y", "%d/%m/%Y"]
    for fmt in formats:
        try:
            dt = datetime.strptime(text, fmt)
            parsed = dt.date()
            return parsed, anomalies
        except ValueError:
            continue

    return None, [{"type": "INVALID_DATE", "desc": f"Cannot parse date: {text}"}]


def parse_split_with(raw: str) -> list:
    if not raw or str(raw).strip() == "":
        return []
    return [p.strip() for p in str(raw).split(";") if p.strip()]


def parse_split_details(raw: str, split_type: str) -> dict:
    """Parse split_details into {name: value}."""
    if not raw or str(raw).strip() == "":
        return {}

    result = {}
    parts = str(raw).split(";")
    for part in parts:
        part = part.strip()
        if not part:
            continue
        m = re.match(r"^(.+?)\s+(\d+(?:\.\d+)?)\s*%?$", part)
        if m:
            name, val = m.group(1).strip(), Decimal(m.group(2))
            if "%" in part or split_type == "percentage":
                result[name] = val  # percentage
            else:
                result[name] = val  # share count or amount
    return result
