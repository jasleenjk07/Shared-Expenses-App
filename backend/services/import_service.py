"""CSV import with anomaly detection and documented policies."""

import csv
import io
import json
from datetime import date
from decimal import Decimal
from typing import Optional

from flask import current_app

from sqlalchemy import func

from backend.extensions import db
from backend.models import Group, GroupMembership, ImportAnomaly, ImportSession, Settlement, User
from backend.services.csv_parser import (
    parse_amount,
    parse_date,
    parse_split_details,
    parse_split_with,
)
from backend.services.expense_service import create_expense
from backend.services.name_utils import (
    DEFAULT_MEMBERSHIP,
    descriptions_similar,
    is_unknown_person,
    looks_like_settlement,
    normalize_name,
)


class ImportReport:
    def __init__(self):
        self.anomalies = []
        self.imported_expenses = 0
        self.imported_settlements = 0
        self.skipped_rows = 0
        self.pending_approval = []

    def add(self, row_num, anomaly_type, description, raw_data="", suggested_action="",
            action_taken="", requires_approval=False, status="auto_resolved"):
        entry = {
            "row_number": row_num,
            "anomaly_type": anomaly_type,
            "description": description,
            "raw_data": raw_data,
            "suggested_action": suggested_action,
            "action_taken": action_taken,
            "requires_approval": requires_approval,
            "status": status,
        }
        self.anomalies.append(entry)
        if requires_approval:
            self.pending_approval.append(entry)

    def to_dict(self):
        return {
            "total_anomalies": len(self.anomalies),
            "imported_expenses": self.imported_expenses,
            "imported_settlements": self.imported_settlements,
            "skipped_rows": self.skipped_rows,
            "pending_approval_count": len(self.pending_approval),
            "anomalies": self.anomalies,
        }


def ensure_group_members(group: Group, name_to_user: dict) -> dict:
    """Ensure all flatmates exist as users and group members."""
    name_to_user_id = {}
    for name, timeline in DEFAULT_MEMBERSHIP.items():
        user = User.query.filter(func.lower(User.name) == name.lower()).first()
        if not user:
            user = User(
                email=f"{name.lower()}@flatmates.local",
                name=name,
            )
            user.set_password("flatmate123")
            db.session.add(user)
            db.session.flush()

        name_to_user_id[name] = user.id

        existing = GroupMembership.query.filter_by(group_id=group.id, user_id=user.id).first()
        if not existing:
            db.session.add(
                GroupMembership(
                    group_id=group.id,
                    user_id=user.id,
                    joined_at=timeline["joined"],
                    left_at=timeline["left"],
                )
            )
    db.session.commit()
    return name_to_user_id


def import_csv_to_group(
    group_id: int,
    user_id: int,
    file_content: bytes,
    filename: str = "expenses_export.csv",
) -> dict:
    group = Group.query.get_or_404(group_id)
    report = ImportReport()
    usd_rate = Decimal(str(current_app.config["USD_TO_INR_RATE"]))

    session = ImportSession(
        group_id=group_id,
        uploaded_by=user_id,
        filename=filename,
        status="processing",
    )
    db.session.add(session)
    db.session.flush()

    name_to_user_id = ensure_group_members(group, {})

    text = file_content.decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(text))
    rows = list(reader)

    # Track for duplicate detection
    seen_expenses = []  # (date, amount, paid_by, description_norm)
    pending_duplicates = []

    prev_date = None

    for idx, row in enumerate(rows, start=2):  # row 1 is header
        raw_snapshot = json.dumps(row)
        description = (row.get("description") or "").strip()
        paid_by_raw = row.get("paid_by") or ""
        amount_raw = row.get("amount")
        currency_raw = (row.get("currency") or "").strip().upper()
        split_type = (row.get("split_type") or "").strip().lower()
        split_with_raw = row.get("split_with") or ""
        split_details_raw = row.get("split_details") or ""
        notes = (row.get("notes") or "").strip()

        row_anomalies = []

        # --- Date ---
        expense_date, date_anomalies = parse_date(row.get("date"), prev_date)
        row_anomalies.extend(date_anomalies)
        if expense_date:
            # Flag classic DD-MM vs MM-DD ambiguity (e.g. 04-05-2026)
            raw_date = (row.get("date") or "").strip()
            parts = raw_date.replace("/", "-").split("-")
            if len(parts) == 3:
                try:
                    d, mo = int(parts[0]), int(parts[1])
                    if d <= 12 and mo <= 12 and d != mo:
                        row_anomalies.append(
                            {
                                "type": "AMBIGUOUS_DATE",
                                "desc": f"Date '{raw_date}' could be DD-MM or MM-DD",
                                "action": f"Used DD-MM-YYYY (Indian convention) → {expense_date.isoformat()}",
                            }
                        )
                except ValueError:
                    pass
            prev_date = expense_date

        # --- Amount ---
        amount, amount_anomalies = parse_amount(amount_raw)
        row_anomalies.extend(amount_anomalies)

        # Skip zero amount
        if amount is not None and amount == 0:
            for a in row_anomalies:
                report.add(idx, a["type"], a["desc"], raw_snapshot, action_taken=a.get("action", ""))
            report.skipped_rows += 1
            continue

        if amount is None or expense_date is None:
            for a in row_anomalies:
                report.add(idx, a["type"], a["desc"], raw_snapshot, action_taken="Row skipped")
            report.skipped_rows += 1
            continue

        # --- Settlement detection ---
        if looks_like_settlement(description, notes, split_type):
            payer = normalize_name(paid_by_raw)
            split_names = parse_split_with(split_with_raw)
            recipient = normalize_name(split_names[0]) if split_names else None

            action = f"Recorded as settlement: {payer} → {recipient}, ₹{abs(amount)}"
            report.add(
                idx, "SETTLEMENT_AS_EXPENSE", f"'{description}' is a payment not an expense",
                raw_snapshot, "Convert to settlement record", action,
            )

            if payer and recipient and payer in name_to_user_id and recipient in name_to_user_id:
                db.session.add(
                    Settlement(
                        group_id=group_id,
                        from_user_id=name_to_user_id[payer],
                        to_user_id=name_to_user_id[recipient],
                        amount_inr=abs(amount),
                        settlement_date=expense_date,
                        notes=notes or description,
                        import_row_number=idx,
                        import_session_id=session.id,
                    )
                )
                report.imported_settlements += 1
            continue

        # --- Payer normalization ---
        payer_name = normalize_name(paid_by_raw)
        if payer_name and payer_name != paid_by_raw.strip():
            report.add(
                idx, "PAYER_NAME_VARIANT",
                f"Payer '{paid_by_raw}' normalized to '{payer_name}'",
                raw_snapshot, action_taken=f"Mapped to user {payer_name}",
            )
        if not payer_name:
            report.add(
                idx, "MISSING_PAYER",
                "No payer specified — cannot determine who paid",
                raw_snapshot,
                "Assign payer manually or split cost as group advance",
                "Expense imported with null payer; excluded from balance until resolved",
                requires_approval=True,
                status="pending",
            )
            payer_user_id = None
        elif payer_name not in name_to_user_id:
            report.add(
                idx, "UNKNOWN_PAYER", f"Unknown payer '{payer_name}'",
                raw_snapshot, action_taken="Row skipped",
            )
            report.skipped_rows += 1
            continue
        else:
            payer_user_id = name_to_user_id[payer_name]

        # --- Currency ---
        currency = currency_raw or "INR"
        if not currency_raw:
            report.add(
                idx, "MISSING_CURRENCY",
                "Currency field empty",
                raw_snapshot, action_taken="Defaulted to INR",
            )
        exchange_rate = Decimal("1")
        amount_inr = amount
        if currency == "USD":
            exchange_rate = usd_rate
            amount_inr = (amount * usd_rate).quantize(Decimal("0.01"))
            report.add(
                idx, "FOREIGN_CURRENCY",
                f"Expense in USD ({amount}) — spreadsheet treated 1 USD = 1 INR",
                raw_snapshot,
                f"Converted at ₹{usd_rate}/USD → ₹{amount_inr}",
                f"Stored original {amount} USD, amount_inr={amount_inr}",
            )

        # --- Split participants ---
        split_names_raw = parse_split_with(split_with_raw)
        split_names = []
        for sn in split_names_raw:
            canonical = normalize_name(sn)
            if is_unknown_person(sn):
                report.add(
                    idx, "UNKNOWN_SPLIT_MEMBER",
                    f"'{sn}' is not a flatmate — excluded from split",
                    raw_snapshot,
                    "Redistribute share among known members",
                    f"Removed {sn} from split",
                )
                continue
            if canonical:
                split_names.append(canonical)

        # Remove inactive members (Sam's request)
        active_on_date = {
            name: uid
            for name, uid in name_to_user_id.items()
            if _member_active(group_id, uid, expense_date)
        }
        filtered_names = []
        for name in split_names:
            if name not in name_to_user_id:
                continue
            if name not in active_on_date:
                report.add(
                    idx, "INACTIVE_MEMBER_IN_SPLIT",
                    f"{name} was not an active member on {expense_date}",
                    raw_snapshot,
                    f"Remove {name} from split — share redistributed",
                    f"Excluded {name}; remaining members absorb share",
                )
                continue
            filtered_names.append(name)

        if not filtered_names:
            # Fall back to active members on date
            filtered_names = list(active_on_date.keys())

        participant_ids = [name_to_user_id[n] for n in filtered_names]

        # --- Split type ---
        effective_split_type = split_type or "equal"
        split_details = parse_split_details(split_details_raw, effective_split_type)

        if split_type == "equal" and split_details:
            effective_split_type = "share"
            report.add(
                idx, "SPLIT_TYPE_MISMATCH",
                "split_type is 'equal' but split_details contains share values",
                raw_snapshot,
                "Use share split from details",
                "Applied share-based split from split_details",
            )

        if effective_split_type == "percentage" and split_details:
            total = sum(split_details.values())
            if total != 100:
                report.add(
                    idx, "PERCENTAGE_NOT_100",
                    f"Percentages sum to {total}%, not 100%",
                    raw_snapshot,
                    "Normalize proportionally to 100%",
                    f"Each share scaled by {100/total:.4f}",
                )

        # --- Duplicate detection ---
        desc_norm = description.lower()
        is_dup = False
        for seen in seen_expenses:
            if (
                seen["date"] == expense_date
                and seen["amount"] == amount
                and seen["paid_by"] == payer_name
                and descriptions_similar(seen["description"], description)
            ):
                is_dup = True
                report.add(
                    idx, "DUPLICATE_EXPENSE",
                    f"Likely duplicate of row {seen['row']}: '{seen['description']}'",
                    raw_snapshot,
                    "Keep first entry, skip duplicate (requires approval to delete)",
                    f"Skipped duplicate — kept row {seen['row']}",
                    requires_approval=True,
                    status="pending",
                )
                break

        # Conflicting duplicates (same event, different amounts)
        for seen in seen_expenses:
            if (
                seen["date"] == expense_date
                and seen["paid_by"] != payer_name
                and descriptions_similar(seen["description"], description)
                and seen["amount"] != amount
            ):
                report.add(
                    idx, "DUPLICATE_CONFLICT",
                    f"Same event as row {seen['row']} but different amount ({amount} vs {seen['amount']})",
                    raw_snapshot,
                    "Keep first logged entry; flag conflict for review",
                    f"Skipped row {idx}; kept row {seen['row']} (₹{seen['amount']})",
                    requires_approval=True,
                    status="pending",
                )
                is_dup = True
                break

        if is_dup:
            report.skipped_rows += 1
            continue

        # Record all row-level anomalies
        for a in row_anomalies:
            report.add(idx, a["type"], a["desc"], raw_snapshot, action_taken=a.get("action", ""))

        # Negative amount = refund: import as expense with negative amount_inr
        status = "active"

        create_expense(
            group_id=group_id,
            description=description,
            amount=abs(amount),
            currency=currency,
            amount_inr=amount_inr if amount >= 0 else -abs(amount_inr),
            exchange_rate=exchange_rate,
            expense_date=expense_date,
            paid_by_user_id=payer_user_id,
            split_type=effective_split_type,
            participant_user_ids=participant_ids,
            split_details=split_details,
            name_to_user_id=name_to_user_id,
            notes=notes,
            import_row_number=idx,
            import_session_id=session.id,
            status=status,
        )
        report.imported_expenses += 1
        seen_expenses.append(
            {
                "row": idx,
                "date": expense_date,
                "amount": amount,
                "paid_by": payer_name,
                "description": description,
            }
        )

    # Persist anomalies
    report_dict = report.to_dict()
    for a in report.anomalies:
        db.session.add(
            ImportAnomaly(
                import_session_id=session.id,
                row_number=a["row_number"],
                anomaly_type=a["anomaly_type"],
                description=a["description"],
                raw_data=a["raw_data"],
                suggested_action=a["suggested_action"],
                action_taken=a["action_taken"],
                status=a["status"],
                requires_approval=a["requires_approval"],
            )
        )

    session.status = "completed" if not report.pending_approval else "pending_review"
    session.report_json = json.dumps(report_dict, indent=2)
    db.session.commit()

    return {
        "import_session_id": session.id,
        "report": report_dict,
    }


def _member_active(group_id: int, user_id: int, on_date: date) -> bool:
    m = GroupMembership.query.filter_by(group_id=group_id, user_id=user_id).first()
    return m.is_active_on(on_date) if m else False
