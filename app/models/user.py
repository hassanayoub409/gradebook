import enum
from datetime import datetime

from flask_login import UserMixin

from app.extensions import db


class RoleEnum(str, enum.Enum):
    STUDENT = "student"
    INSTRUCTOR = "instructor"
    TA = "ta"
    ADMIN = "admin"


class ApprovalStatusEnum(str, enum.Enum):
    APPROVED = "approved"
    PENDING = "pending"
    REJECTED = "rejected"


class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    full_name = db.Column(db.String(120), nullable=False)
    password_hash = db.Column(db.String(255), nullable=True)

    role = db.Column(db.Enum(RoleEnum), nullable=False, default=RoleEnum.STUDENT)

    approval_status = db.Column(db.Enum(ApprovalStatusEnum), nullable=True)
    reviewed_by = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    reviewed_at = db.Column(db.DateTime, nullable=True)

    google_id = db.Column(db.String(255), unique=True, nullable=True)
    avatar_url = db.Column(db.String(255), nullable=True)

    is_active_flag = db.Column("is_active", db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    reviewer = db.relationship("User", remote_side=[id], foreign_keys=[reviewed_by])

    # --- Permission / state properties (§6, §5.2) ---

    @property
    def is_staff(self):
        return self.role in (RoleEnum.INSTRUCTOR, RoleEnum.TA)

    @property
    def is_admin(self):
        return self.role == RoleEnum.ADMIN

    @property
    def is_gated_role(self):
        return self.role in (RoleEnum.INSTRUCTOR, RoleEnum.TA, RoleEnum.ADMIN)

    @property
    def is_approved(self):
        return self.role == RoleEnum.STUDENT or self.approval_status == ApprovalStatusEnum.APPROVED

    # UserMixin's `is_active` expects a property; we backed it with a real
    # column named is_active (mapped to is_active_flag above) to avoid clashing.
    @property
    def is_active(self):
        return self.is_active_flag

    def __repr__(self):
        return f"<User {self.username} ({self.role.value})>"