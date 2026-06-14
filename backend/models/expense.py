from datetime import datetime

from backend.extensions import db


class Expense(db.Model):
    __tablename__ = "expenses"

    id = db.Column(db.Integer, primary_key=True)
    group_id = db.Column(db.Integer, db.ForeignKey("groups.id"), nullable=False)
    description = db.Column(db.String(255), nullable=False)
    amount = db.Column(db.Numeric(12, 2), nullable=False)
    currency = db.Column(db.String(3), default="INR", nullable=False)
    amount_inr = db.Column(db.Numeric(12, 2), nullable=False)
    exchange_rate = db.Column(db.Numeric(10, 4), default=1.0)
    expense_date = db.Column(db.Date, nullable=False)
    paid_by_user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    split_type = db.Column(db.String(20), nullable=False, default="equal")
    notes = db.Column(db.Text)
    status = db.Column(db.String(20), default="active")
    import_row_number = db.Column(db.Integer)
    import_session_id = db.Column(db.Integer, db.ForeignKey("import_sessions.id"))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    group = db.relationship("Group", back_populates="expenses")
    paid_by = db.relationship("User", back_populates="expenses_paid")
    splits = db.relationship(
        "ExpenseSplit", back_populates="expense", lazy=True, cascade="all, delete-orphan"
    )

    def to_dict(self, include_splits: bool = False) -> dict:
        data = {
            "id": self.id,
            "group_id": self.group_id,
            "description": self.description,
            "amount": float(self.amount),
            "currency": self.currency,
            "amount_inr": float(self.amount_inr),
            "exchange_rate": float(self.exchange_rate) if self.exchange_rate else 1.0,
            "expense_date": self.expense_date.isoformat(),
            "paid_by_user_id": self.paid_by_user_id,
            "paid_by_name": self.paid_by.name if self.paid_by else None,
            "split_type": self.split_type,
            "notes": self.notes,
            "status": self.status,
            "import_row_number": self.import_row_number,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
        if include_splits:
            data["splits"] = [s.to_dict() for s in self.splits]
        return data


class ExpenseSplit(db.Model):
    __tablename__ = "expense_splits"

    id = db.Column(db.Integer, primary_key=True)
    expense_id = db.Column(db.Integer, db.ForeignKey("expenses.id"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    share_value = db.Column(db.Numeric(12, 4))
    allocated_amount_inr = db.Column(db.Numeric(12, 2), nullable=False)

    expense = db.relationship("Expense", back_populates="splits")
    user = db.relationship("User", back_populates="expense_splits")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "expense_id": self.expense_id,
            "user_id": self.user_id,
            "user_name": self.user.name if self.user else None,
            "share_value": float(self.share_value) if self.share_value is not None else None,
            "allocated_amount_inr": float(self.allocated_amount_inr),
        }
