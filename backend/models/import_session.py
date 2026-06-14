from datetime import datetime

from backend.extensions import db


class ImportSession(db.Model):
    __tablename__ = "import_sessions"

    id = db.Column(db.Integer, primary_key=True)
    group_id = db.Column(db.Integer, db.ForeignKey("groups.id"), nullable=False)
    uploaded_by = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    filename = db.Column(db.String(255), nullable=False)
    status = db.Column(db.String(30), default="completed")
    report_json = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    group = db.relationship("Group")
    uploader = db.relationship("User")
    anomalies = db.relationship(
        "ImportAnomaly", back_populates="import_session", lazy=True, cascade="all, delete-orphan"
    )


class ImportAnomaly(db.Model):
    __tablename__ = "import_anomalies"

    id = db.Column(db.Integer, primary_key=True)
    import_session_id = db.Column(db.Integer, db.ForeignKey("import_sessions.id"), nullable=False)
    row_number = db.Column(db.Integer, nullable=False)
    anomaly_type = db.Column(db.String(50), nullable=False)
    description = db.Column(db.Text, nullable=False)
    raw_data = db.Column(db.Text)
    suggested_action = db.Column(db.Text)
    action_taken = db.Column(db.Text)
    status = db.Column(db.String(20), default="auto_resolved")
    requires_approval = db.Column(db.Boolean, default=False)

    import_session = db.relationship("ImportSession", back_populates="anomalies")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "import_session_id": self.import_session_id,
            "row_number": self.row_number,
            "anomaly_type": self.anomaly_type,
            "description": self.description,
            "raw_data": self.raw_data,
            "suggested_action": self.suggested_action,
            "action_taken": self.action_taken,
            "status": self.status,
            "requires_approval": self.requires_approval,
        }
