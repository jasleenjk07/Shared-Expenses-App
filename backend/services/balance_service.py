"""Compute group balances and simplified debts."""

from collections import defaultdict
from decimal import Decimal, ROUND_HALF_UP
from typing import Dict, List, Tuple

from backend.extensions import db
from backend.models import Expense, ExpenseSplit, GroupMembership, Settlement, User


def _quantize(amount: Decimal) -> Decimal:
    return amount.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def compute_member_balances(group_id: int) -> Dict[int, Decimal]:
    """
    Positive balance = member is owed money (paid more than share).
    Negative balance = member owes money.
    """
    balances: Dict[int, Decimal] = defaultdict(lambda: Decimal("0"))

    expenses = Expense.query.filter_by(group_id=group_id, status="active").all()
    for expense in expenses:
        if expense.paid_by_user_id:
            balances[expense.paid_by_user_id] += Decimal(str(expense.amount_inr))

        for split in expense.splits:
            balances[split.user_id] -= Decimal(str(split.allocated_amount_inr))

    settlements = Settlement.query.filter_by(group_id=group_id).all()
    for s in settlements:
        balances[s.from_user_id] += Decimal(str(s.amount_inr))
        balances[s.to_user_id] -= Decimal(str(s.amount_inr))

    return {uid: _quantize(bal) for uid, bal in balances.items()}


def simplify_debts(balances: Dict[int, Decimal]) -> List[dict]:
    """Greedy debt simplification: who pays whom."""
    creditors: List[Tuple[int, Decimal]] = []
    debtors: List[Tuple[int, Decimal]] = []

    for uid, bal in balances.items():
        if bal > Decimal("0.01"):
            creditors.append((uid, bal))
        elif bal < Decimal("-0.01"):
            debtors.append((uid, -bal))

    creditors.sort(key=lambda x: x[1], reverse=True)
    debtors.sort(key=lambda x: x[1], reverse=True)

    transactions = []
    ci, di = 0, 0
    while ci < len(creditors) and di < len(debtors):
        c_uid, c_amt = creditors[ci]
        d_uid, d_amt = debtors[di]
        pay = min(c_amt, d_amt)
        if pay > Decimal("0.01"):
            transactions.append(
                {
                    "from_user_id": d_uid,
                    "to_user_id": c_uid,
                    "amount_inr": float(_quantize(pay)),
                }
            )
        creditors[ci] = (c_uid, c_amt - pay)
        debtors[di] = (d_uid, d_amt - pay)
        if creditors[ci][1] <= Decimal("0.01"):
            ci += 1
        if debtors[di][1] <= Decimal("0.01"):
            di += 1

    return transactions


def get_balance_summary(group_id: int) -> dict:
    raw = compute_member_balances(group_id)
    users = {u.id: u for u in User.query.all()}

    member_balances = []
    for uid, bal in raw.items():
        member_balances.append(
            {
                "user_id": uid,
                "user_name": users[uid].name if uid in users else "Unknown",
                "balance_inr": float(bal),
            }
        )

    debts = simplify_debts(raw)
    for d in debts:
        d["from_user_name"] = users[d["from_user_id"]].name
        d["to_user_name"] = users[d["to_user_id"]].name

    return {
        "member_balances": sorted(member_balances, key=lambda x: x["user_name"]),
        "simplified_debts": debts,
    }


def get_member_expense_breakdown(group_id: int, user_id: int) -> dict:
    """Rohan's request: show exactly which expenses make up a member's balance."""
    expenses = (
        Expense.query.filter_by(group_id=group_id, status="active")
        .order_by(Expense.expense_date)
        .all()
    )
    lines = []
    running = Decimal("0")

    for exp in expenses:
        paid = Decimal("0")
        owed = Decimal("0")
        if exp.paid_by_user_id == user_id:
            paid = Decimal(str(exp.amount_inr))
        for split in exp.splits:
            if split.user_id == user_id:
                owed = Decimal(str(split.allocated_amount_inr))

        if paid or owed:
            net = paid - owed
            running += net
            lines.append(
                {
                    "expense_id": exp.id,
                    "date": exp.expense_date.isoformat(),
                    "description": exp.description,
                    "paid_inr": float(paid),
                    "share_inr": float(owed),
                    "net_inr": float(_quantize(net)),
                    "currency": exp.currency,
                    "original_amount": float(exp.amount),
                }
            )

    settlements = Settlement.query.filter_by(group_id=group_id).all()
    for s in settlements:
        if s.from_user_id == user_id:
            running += Decimal(str(s.amount_inr))
            lines.append(
                {
                    "type": "settlement",
                    "date": s.settlement_date.isoformat(),
                    "description": f"Paid {users_name(s.to_user_id)}",
                    "paid_inr": float(s.amount_inr),
                    "share_inr": 0,
                    "net_inr": float(s.amount_inr),
                }
            )
        elif s.to_user_id == user_id:
            running -= Decimal(str(s.amount_inr))
            lines.append(
                {
                    "type": "settlement",
                    "date": s.settlement_date.isoformat(),
                    "description": f"Received from {users_name(s.from_user_id)}",
                    "paid_inr": 0,
                    "share_inr": float(s.amount_inr),
                    "net_inr": float(-s.amount_inr),
                }
            )

    return {
        "user_id": user_id,
        "user_name": users_name(user_id),
        "lines": lines,
        "total_balance_inr": float(_quantize(running)),
    }


def users_name(user_id: int) -> str:
    u = User.query.get(user_id)
    return u.name if u else "Unknown"


def active_members_on(group_id: int, on_date) -> List[int]:
    memberships = GroupMembership.query.filter_by(group_id=group_id).all()
    return [m.user_id for m in memberships if m.is_active_on(on_date)]
