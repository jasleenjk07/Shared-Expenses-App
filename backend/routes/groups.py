from datetime import datetime

from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from backend.extensions import db
from backend.models import Group, GroupMembership, User

groups_bp = Blueprint("groups", __name__, url_prefix="/api/groups")


def _parse_date(val):
    if not val:
        return None
    return datetime.strptime(val, "%Y-%m-%d").date()


@groups_bp.route("", methods=["GET"])
@jwt_required()
def list_groups():
    user_id = int(get_jwt_identity())
    memberships = GroupMembership.query.filter_by(user_id=user_id).all()
    groups = [Group.query.get(m.group_id) for m in memberships]
    return jsonify([g.to_dict(include_members=True) for g in groups if g])


@groups_bp.route("", methods=["POST"])
@jwt_required()
def create_group():
    user_id = int(get_jwt_identity())
    data = request.get_json() or {}
    name = (data.get("name") or "").strip()
    if not name:
        return jsonify({"error": "name is required"}), 400

    group = Group(name=name, description=data.get("description"), created_by=user_id)
    db.session.add(group)
    db.session.flush()

    db.session.add(
        GroupMembership(
            group_id=group.id,
            user_id=user_id,
            joined_at=_parse_date(data.get("joined_at")) or datetime.utcnow().date(),
            role="admin",
        )
    )
    db.session.commit()
    return jsonify(group.to_dict(include_members=True)), 201


@groups_bp.route("/<int:group_id>", methods=["GET"])
@jwt_required()
def get_group(group_id):
    group = Group.query.get_or_404(group_id)
    return jsonify(group.to_dict(include_members=True))


@groups_bp.route("/<int:group_id>/members", methods=["POST"])
@jwt_required()
def add_member(group_id):
    Group.query.get_or_404(group_id)
    data = request.get_json() or {}
    user_id = data.get("user_id")
    joined_at = _parse_date(data.get("joined_at"))

    if not user_id or not joined_at:
        return jsonify({"error": "user_id and joined_at required"}), 400

    User.query.get_or_404(user_id)
    existing = GroupMembership.query.filter_by(group_id=group_id, user_id=user_id).first()
    if existing and existing.left_at is None:
        return jsonify({"error": "User is already an active member"}), 409

    membership = GroupMembership(group_id=group_id, user_id=user_id, joined_at=joined_at)
    db.session.add(membership)
    db.session.commit()
    return jsonify(membership.to_dict()), 201


@groups_bp.route("/<int:group_id>/members/<int:membership_id>", methods=["PATCH"])
@jwt_required()
def update_membership(group_id, membership_id):
    membership = GroupMembership.query.filter_by(id=membership_id, group_id=group_id).first_or_404()
    data = request.get_json() or {}
    if "left_at" in data:
        membership.left_at = _parse_date(data["left_at"])
    if "joined_at" in data:
        membership.joined_at = _parse_date(data["joined_at"])
    db.session.commit()
    return jsonify(membership.to_dict())


@groups_bp.route("/<int:group_id>/users", methods=["GET"])
@jwt_required()
def list_users_for_group(group_id):
    Group.query.get_or_404(group_id)
    users = User.query.all()
    return jsonify([u.to_dict() for u in users])
