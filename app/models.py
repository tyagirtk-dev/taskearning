"""
app/models.py – All SQLAlchemy ORM models.
One file keeps cross-model relationships easy to read.
"""

import uuid
import secrets
from datetime import datetime, timedelta
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app import db, login_manager


# ─────────────────────────────────────────────────────────────────────────────
#  Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _uuid() -> str:
    return str(uuid.uuid4())


# ─────────────────────────────────────────────────────────────────────────────
#  User
# ─────────────────────────────────────────────────────────────────────────────

class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    uid = db.Column(db.String(36), unique=True, default=_uuid, nullable=False)

    # Profile
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    profile_pic = db.Column(db.String(200), default="default.png")
    phone = db.Column(db.String(20), nullable=True)
    bio = db.Column(db.Text, nullable=True)

    # Status
    is_active = db.Column(db.Boolean, default=True)
    is_email_verified = db.Column(db.Boolean, default=False)
    is_banned = db.Column(db.Boolean, default=False)
    ban_reason = db.Column(db.String(300), nullable=True)

    # Wallet
    wallet_balance = db.Column(db.Float, default=0.0)
    total_earned = db.Column(db.Float, default=0.0)

    # Referral
    referral_code = db.Column(db.String(12), unique=True)
    referred_by_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)

    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime, nullable=True)

    # Relationships
    submissions = db.relationship("TaskSubmission", backref="user", lazy="dynamic")
    transactions = db.relationship("WalletTransaction", backref="user", lazy="dynamic")
    withdrawal_requests = db.relationship("WithdrawalRequest", backref="user", lazy="dynamic")
    referrals_made = db.relationship(
        "User",
        backref=db.backref("referred_by", remote_side=[id]),
        lazy="dynamic",
        foreign_keys=[referred_by_id],
    )

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if not self.referral_code:
            self.referral_code = secrets.token_urlsafe(8)[:10].upper()

    def set_password(self, password: str) -> None:
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)

    @property
    def pending_submissions(self):
        return self.submissions.filter_by(status="pending").count()

    @property
    def completed_tasks(self):
        return self.submissions.filter_by(status="approved").count()

    @property
    def referral_count(self):
        return self.referrals_made.count()

    def __repr__(self):
        return f"<User {self.email}>"


@login_manager.user_loader
def load_user(user_id: str):
    return User.query.get(int(user_id))


# ─────────────────────────────────────────────────────────────────────────────
#  Admin
# ─────────────────────────────────────────────────────────────────────────────

class Admin(db.Model):
    __tablename__ = "admins"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    is_super_admin = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime, nullable=True)

    def set_password(self, password: str) -> None:
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f"<Admin {self.email}>"


# ─────────────────────────────────────────────────────────────────────────────
#  Task
# ─────────────────────────────────────────────────────────────────────────────

class Task(db.Model):
    __tablename__ = "tasks"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    instructions = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(50), default="general")
    reward = db.Column(db.Float, nullable=False)
    time_limit_hours = db.Column(db.Integer, default=24)
    max_submissions = db.Column(db.Integer, default=100)
    thumbnail = db.Column(db.String(200), nullable=True)
    external_url = db.Column(db.String(500), nullable=True)

    is_active = db.Column(db.Boolean, default=True)
    requires_proof = db.Column(db.Boolean, default=True)

    created_by_id = db.Column(db.Integer, db.ForeignKey("admins.id"))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    submissions = db.relationship("TaskSubmission", backref="task", lazy="dynamic")
    created_by = db.relationship("Admin", backref="tasks")

    @property
    def submission_count(self):
        return self.submissions.filter_by(status="approved").count()

    @property
    def is_available(self):
        return self.is_active and self.submission_count < self.max_submissions

    def __repr__(self):
        return f"<Task {self.title}>"


# ─────────────────────────────────────────────────────────────────────────────
#  Task Submission
# ─────────────────────────────────────────────────────────────────────────────

class TaskSubmission(db.Model):
    __tablename__ = "task_submissions"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    task_id = db.Column(db.Integer, db.ForeignKey("tasks.id"), nullable=False)
    proof_screenshot = db.Column(db.String(200), nullable=True)
    proof_text = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(20), default="pending")  # pending/approved/rejected
    rejection_reason = db.Column(db.String(500), nullable=True)
    reward_paid = db.Column(db.Float, default=0.0)

    submitted_at = db.Column(db.DateTime, default=datetime.utcnow)
    reviewed_at = db.Column(db.DateTime, nullable=True)
    reviewed_by_id = db.Column(db.Integer, db.ForeignKey("admins.id"), nullable=True)

    reviewed_by = db.relationship("Admin", backref="reviewed_submissions")

    __table_args__ = (
        db.UniqueConstraint("user_id", "task_id", name="unique_user_task"),
    )

    def __repr__(self):
        return f"<Submission user={self.user_id} task={self.task_id} status={self.status}>"


# ─────────────────────────────────────────────────────────────────────────────
#  Wallet Transaction
# ─────────────────────────────────────────────────────────────────────────────

class WalletTransaction(db.Model):
    __tablename__ = "wallet_transactions"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    transaction_type = db.Column(db.String(30), nullable=False)
    # Types: task_reward / referral_bonus / withdrawal / adjustment
    description = db.Column(db.String(300), nullable=True)
    balance_after = db.Column(db.Float, nullable=False)
    reference_id = db.Column(db.String(50), nullable=True)  # submission_id / withdrawal_id
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<Tx user={self.user_id} type={self.transaction_type} amount={self.amount}>"


# ─────────────────────────────────────────────────────────────────────────────
#  Withdrawal Request
# ─────────────────────────────────────────────────────────────────────────────

class WithdrawalRequest(db.Model):
    __tablename__ = "withdrawal_requests"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    upi_id = db.Column(db.String(100), nullable=False)
    status = db.Column(db.String(20), default="pending")  # pending/approved/rejected
    rejection_reason = db.Column(db.String(300), nullable=True)
    transaction_ref = db.Column(db.String(100), nullable=True)

    requested_at = db.Column(db.DateTime, default=datetime.utcnow)
    processed_at = db.Column(db.DateTime, nullable=True)
    processed_by_id = db.Column(db.Integer, db.ForeignKey("admins.id"), nullable=True)

    processed_by = db.relationship("Admin", backref="processed_withdrawals")

    def __repr__(self):
        return f"<Withdrawal user={self.user_id} amount={self.amount} status={self.status}>"


# ─────────────────────────────────────────────────────────────────────────────
#  Email Verification Token
# ─────────────────────────────────────────────────────────────────────────────

class EmailVerificationToken(db.Model):
    __tablename__ = "email_verification_tokens"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    token = db.Column(db.String(6), nullable=False)   # 6-digit OTP
    token_type = db.Column(db.String(20), default="email_verify")
    # Types: email_verify / password_reset
    expires_at = db.Column(db.DateTime, nullable=False)
    is_used = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship("User", backref="verification_tokens")

    @classmethod
    def create(cls, user_id: int, token_type: str = "email_verify", expire_minutes: int = 15):
        otp = secrets.randbelow(900000) + 100000  # 6-digit
        obj = cls(
            user_id=user_id,
            token=str(otp),
            token_type=token_type,
            expires_at=datetime.utcnow() + timedelta(minutes=expire_minutes),
        )
        return obj

    @property
    def is_expired(self) -> bool:
        return datetime.utcnow() > self.expires_at

    def __repr__(self):
        return f"<Token user={self.user_id} type={self.token_type}>"
