import json

from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from backend.extensions import db
from backend.models import Group, ImportAnomaly, ImportSession
from backend.services.import_service import import_csv_to_group

import_bp = Blueprint("import", __name__, url_prefix="/api/groups/<int:group_id>/import")


@import_bp.route("", methods=["POST"])
@jwt_required()
def import_csv(group_id):
    Group.query.get_or_404(group_id)
    user_id = int(get_jwt_identity())

    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files["file"]
    content = file.read()
    if not content:
        return jsonify({"error": "Empty file"}), 400

    result = import_csv_to_group(group_id, user_id, content, file.filename)
    return jsonify(result), 201


@import_bp.route("/sessions", methods=["GET"])
@jwt_required()
def list_sessions(group_id):
    sessions = (
        ImportSession.query.filter_by(group_id=group_id)
        .order_by(ImportSession.created_at.desc())
        .all()
    )
    return jsonify(
        [
            {
                "id": s.id,
                "filename": s.filename,
                "status": s.status,
                "created_at": s.created_at.isoformat(),
                "report": json.loads(s.report_json) if s.report_json else None,
            }
            for s in sessions
        ]
    )


@import_bp.route("/sessions/<int:session_id>", methods=["GET"])
@jwt_required()
def get_session_report(group_id, session_id):
    session = ImportSession.query.filter_by(id=session_id, group_id=group_id).first_or_404()
    anomalies = ImportAnomaly.query.filter_by(import_session_id=session.id).all()
    return jsonify(
        {
            "id": session.id,
            "filename": session.filename,
            "status": session.status,
            "created_at": session.created_at.isoformat(),
            "report": json.loads(session.report_json) if session.report_json else None,
            "anomalies": [a.to_dict() for a in anomalies],
        }
    )


@import_bp.route("/anomalies/<int:anomaly_id>", methods=["PATCH"])
@jwt_required()
def resolve_anomaly(group_id, anomaly_id):
    anomaly = ImportAnomaly.query.get_or_404(anomaly_id)
    data = request.get_json() or {}
    anomaly.status = data.get("status", "approved")
    if "action_taken" in data:
        anomaly.action_taken = data["action_taken"]
    db.session.commit()
    return jsonify(anomaly.to_dict())
