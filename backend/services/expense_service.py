"""Create expenses with computed splits."""

from decimal import Decimal, ROUND_HALF_UP
from typing import Dict, List, Optional

from backend.extensions import db
from backend.models import Expense, ExpenseSplit, User


def _quantize(amount: Decimal) -> Decimal:
    return amount.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def compute_splits(
    amount_inr: Decimal,
    split_type: str,
    participants: List[int],
    split_details: Optional[Dict[str, Decimal]] = None,
    name_to_user_id: Optional[Dict[str, int]] = None,
) -> List[dict]:
    """
    Return list of {user_id, share_value, allocated_amount_inr}.
    Handles equal, unequal, percentage, share split types.
    """
    if not participants:
        return []

    split_details = split_details or {}
    name_to_user_id = name_to_user_id or {}

    if split_type == "equal":
        per_person = _quantize(amount_inr / len(participants))
        splits = []
        remainder = amount_inr
        for i, uid in enumerate(participants):
            if i == len(participants) - 1:
                alloc = _quantize(remainder)
            else:
                alloc = per_person
                remainder -= alloc
            splits.append({"user_id": uid, "share_value": None, "allocated_amount_inr": alloc})
        return splits

    if split_type == "unequal":
        splits = []
        total_assigned = Decimal("0")
        assigned_users = set()
        for name, val in split_details.items():
            uid = name_to_user_id.get(name)
            if uid and uid in participants:
                splits.append(
                    {"user_id": uid, "share_value": val, "allocated_amount_inr": _quantize(val)}
                )
                total_assigned += _quantize(val)
                assigned_users.add(uid)
        # Remaining participants split the rest equally
        remaining = [u for u in participants if u not in assigned_users]
        leftover = amount_inr - total_assigned
        if remaining and leftover > 0:
            per = _quantize(leftover / len(remaining))
            rem = leftover
            for i, uid in enumerate(remaining):
                alloc = _quantize(rem) if i == len(remaining) - 1 else per
                if i < len(remaining) - 1:
                    rem -= alloc
                splits.append({"user_id": uid, "share_value": None, "allocated_amount_inr": alloc})
        return splits

    if split_type == "percentage":
        total_pct = sum(split_details.values()) if split_details else Decimal("0")
        anomalies_note = None
        if total_pct and total_pct != 100:
            anomalies_note = total_pct
            # Normalize proportionally
            factor = Decimal("100") / total_pct
            split_details = {k: v * factor for k, v in split_details.items()}

        if split_details:
            splits = []
            remainder = amount_inr
            items = list(split_details.items())
            for i, (name, pct) in enumerate(items):
                uid = name_to_user_id.get(name)
                if uid is None or uid not in participants:
                    continue
                if i == len(items) - 1:
                    alloc = _quantize(remainder)
                else:
                    alloc = _quantize(amount_inr * pct / 100)
                    remainder -= alloc
                splits.append({"user_id": uid, "share_value": pct, "allocated_amount_inr": alloc})
            return splits

        # Equal percentages if no details
        return compute_splits(amount_inr, "equal", participants)

    if split_type == "share":
        if split_details:
            total_shares = sum(
                split_details.get(name, Decimal("1"))
                for name in split_details
                if name_to_user_id.get(name) in participants
            )
            if total_shares == 0:
                total_shares = Decimal(len(participants))
            splits = []
            remainder = amount_inr
            items = [
                (name_to_user_id[n], split_details[n])
                for n in split_details
                if name_to_user_id.get(n) in participants
            ]
            for i, (uid, shares) in enumerate(items):
                if i == len(items) - 1:
                    alloc = _quantize(remainder)
                else:
                    alloc = _quantize(amount_inr * shares / total_shares)
                    remainder -= alloc
                splits.append({"user_id": uid, "share_value": shares, "allocated_amount_inr": alloc})
            return splits
        return compute_splits(amount_inr, "equal", participants)

    return compute_splits(amount_inr, "equal", participants)


def create_expense(
    group_id: int,
    description: str,
    amount: Decimal,
    currency: str,
    amount_inr: Decimal,
    exchange_rate: Decimal,
    expense_date,
    paid_by_user_id: Optional[int],
    split_type: str,
    participant_user_ids: List[int],
    split_details: Optional[Dict[str, Decimal]] = None,
    name_to_user_id: Optional[Dict[str, int]] = None,
    notes: str = "",
    import_row_number: int = None,
    import_session_id: int = None,
    status: str = "active",
) -> Expense:
    expense = Expense(
        group_id=group_id,
        description=description,
        amount=amount,
        currency=currency,
        amount_inr=amount_inr,
        exchange_rate=exchange_rate,
        expense_date=expense_date,
        paid_by_user_id=paid_by_user_id,
        split_type=split_type,
        notes=notes,
        status=status,
        import_row_number=import_row_number,
        import_session_id=import_session_id,
    )
    db.session.add(expense)
    db.session.flush()

    split_rows = compute_splits(
        amount_inr, split_type, participant_user_ids, split_details, name_to_user_id
    )
    for row in split_rows:
        db.session.add(
            ExpenseSplit(
                expense_id=expense.id,
                user_id=row["user_id"],
                share_value=row["share_value"],
                allocated_amount_inr=row["allocated_amount_inr"],
            )
        )

    db.session.commit()
    return expense
