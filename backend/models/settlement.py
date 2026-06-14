from datetime import datetime

from backend.extensions import db


class Settlement(db.Model):
    __tablename__ = "settlements"

    id = db.Column(db.Integer, primary_key=True)
    group_id = db.Column(db.Integer, db.ForeignKey("groups.id"), nullable=False)
    from_user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    to_user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    amount_inr = db.Column(db.Numeric(12, 2), nullable=False)
    settlement_date = db.Column(db.Date, nullable=False)
    notes = db.Column(db.Text)
    import_row_number = db.Column(db.Integer)
    import_session_id = db.Column(db.Integer, db.ForeignKey("import_sessions.id"))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    group = db.relationship("Group", back_populates="settlements")
    from_user = db.relationship("User", foreign_keys=[from_user_id])
    to_user = db.relationship("User", foreign_keys=[to_user_id])

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "group_id": self.group_id,
            "from_user_id": self.from_user_id,
            "from_user_name": self.from_user.name if self.from_user else None,
            "to_user_id": self.to_user_id,
            "to_user_name": self.to_user.name if self.to_user else None,
            "amount_inr": float(self.amount_inr),
            "settlement_date": self.settlement_date.isoformat(),
            "notes": self.notes,
            "import_row_number": self.import_row_number,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
