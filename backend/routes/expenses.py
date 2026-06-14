from datetime import datetime
from decimal import Decimal

from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required

from backend.extensions import db
from backend.models import Expense, Group, Settlement, User
from backend.services.balance_service import get_balance_summary, get_member_expense_breakdown
from backend.services.expense_service import create_expense

expenses_bp = Blueprint("expenses", __name__, url_prefix="/api/groups/<int:group_id>")


def _parse_date(val):
    return datetime.strptime(val, "%Y-%m-%d").date()


@expenses_bp.route("/expenses", methods=["GET"])
@jwt_required()
def list_expenses(group_id):
    Group.query.get_or_404(group_id)
    expenses = (
        Expense.query.filter_by(group_id=group_id)
        .order_by(Expense.expense_date.desc())
        .all()
    )
    return jsonify([e.to_dict(include_splits=True) for e in expenses])


@expenses_bp.route("/expenses", methods=["POST"])
@jwt_required()
def add_expense(group_id):
    Group.query.get_or_404(group_id)
    data = request.get_json() or {}

    amount = Decimal(str(data["amount"]))
    currency = data.get("currency", "INR")
    rate = Decimal(str(data.get("exchange_rate", 1)))
    amount_inr = amount * rate if currency != "INR" else amount

    split_details = {}
    if data.get("split_details"):
        split_details = {k: Decimal(str(v)) for k, v in data["split_details"].items()}

    name_to_user = {u.name: u.id for u in User.query.all()}

    expense = create_expense(
        group_id=group_id,
        description=data["description"],
        amount=amount,
        currency=currency,
        amount_inr=amount_inr.quantize(Decimal("0.01")),
        exchange_rate=rate,
        expense_date=_parse_date(data["expense_date"]),
        paid_by_user_id=data.get("paid_by_user_id"),
        split_type=data.get("split_type", "equal"),
        participant_user_ids=data["participant_user_ids"],
        split_details=split_details,
        name_to_user_id=name_to_user,
        notes=data.get("notes", ""),
    )
    return jsonify(expense.to_dict(include_splits=True)), 201


@expenses_bp.route("/expenses/<int:expense_id>", methods=["GET"])
@jwt_required()
def get_expense(group_id, expense_id):
    expense = Expense.query.filter_by(id=expense_id, group_id=group_id).first_or_404()
    return jsonify(expense.to_dict(include_splits=True))


@expenses_bp.route("/expenses/<int:expense_id>", methods=["DELETE"])
@jwt_required()
def delete_expense(group_id, expense_id):
    expense = Expense.query.filter_by(id=expense_id, group_id=group_id).first_or_404()
    db.session.delete(expense)
    db.session.commit()
    return jsonify({"message": "deleted"})


@expenses_bp.route("/settlements", methods=["GET"])
@jwt_required()
def list_settlements(group_id):
    settlements = Settlement.query.filter_by(group_id=group_id).all()
    return jsonify([s.to_dict() for s in settlements])


@expenses_bp.route("/settlements", methods=["POST"])
@jwt_required()
def add_settlement(group_id):
    Group.query.get_or_404(group_id)
    data = request.get_json() or {}
    settlement = Settlement(
        group_id=group_id,
        from_user_id=data["from_user_id"],
        to_user_id=data["to_user_id"],
        amount_inr=Decimal(str(data["amount_inr"])),
        settlement_date=_parse_date(data["settlement_date"]),
        notes=data.get("notes", ""),
    )
    db.session.add(settlement)
    db.session.commit()
    return jsonify(settlement.to_dict()), 201


@expenses_bp.route("/balances", methods=["GET"])
@jwt_required()
def balances(group_id):
    Group.query.get_or_404(group_id)
    return jsonify(get_balance_summary(group_id))


@expenses_bp.route("/balances/<int:user_id>", methods=["GET"])
@jwt_required()
def member_breakdown(group_id, user_id):
    Group.query.get_or_404(group_id)
    return jsonify(get_member_expense_breakdown(group_id, user_id))
