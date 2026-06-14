from datetime import datetime

from backend.extensions import db


class Group(db.Model):
    __tablename__ = "groups"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    description = db.Column(db.Text)
    created_by = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    creator = db.relationship("User", foreign_keys=[created_by])
    memberships = db.relationship(
        "GroupMembership", back_populates="group", lazy=True, cascade="all, delete-orphan"
    )
    expenses = db.relationship("Expense", back_populates="group", lazy=True)
    settlements = db.relationship("Settlement", back_populates="group", lazy=True)

    def to_dict(self, include_members: bool = False) -> dict:
        data = {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "created_by": self.created_by,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
        if include_members:
            data["members"] = [m.to_dict() for m in self.memberships]
        return data


class GroupMembership(db.Model):
    __tablename__ = "group_memberships"

    id = db.Column(db.Integer, primary_key=True)
    group_id = db.Column(db.Integer, db.ForeignKey("groups.id"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    joined_at = db.Column(db.Date, nullable=False)
    left_at = db.Column(db.Date, nullable=True)
    role = db.Column(db.String(20), default="member")

    group = db.relationship("Group", back_populates="memberships")
    user = db.relationship("User", back_populates="memberships")

    def is_active_on(self, on_date) -> bool:
        if on_date < self.joined_at:
            return False
        if self.left_at and on_date > self.left_at:
            return False
        return True

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "group_id": self.group_id,
            "user_id": self.user_id,
            "user_name": self.user.name if self.user else None,
            "joined_at": self.joined_at.isoformat() if self.joined_at else None,
            "left_at": self.left_at.isoformat() if self.left_at else None,
            "role": self.role,
        }
