from datetime import datetime, timezone

from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash

from app import db


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)

    email = db.Column(db.String(256), unique=True, nullable=False)
    password = db.Column(db.String(256), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))

    data_sets = db.relationship("DataSet", backref="user", lazy=True)
    profile = db.relationship("UserProfile", backref="user", uselist=False)

    def __init__(self, **kwargs):
        super(User, self).__init__(**kwargs)
        if "password" in kwargs:
            self.set_password(kwargs["password"])

    def __repr__(self):
        return f"<User {self.email}>"

    def set_password(self, password):
        self.password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password, password)

    def temp_folder(self) -> str:
        from app.features.auth.services import AuthenticationService

        return AuthenticationService().temp_folder_by_user(self)


def utc_now_naive() -> datetime:
    """Return naive UTC datetime compatible with MariaDB DATETIME columns."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


# New model to store failed login attemps
class AuthRateLimit(db.Model):
    __tablename__ = "auth_rate_limit"

    id = db.Column(db.Integer, primary_key=True)
    action = db.Column(db.String(32), nullable=False, default="login", index=True)
    scope = db.Column(db.String(16), nullable=False)  # "email" or "ip"
    identifier = db.Column(db.String(255), nullable=False, index=True)
    attempts = db.Column(db.Integer, nullable=False, default=0)
    window_start = db.Column(db.DateTime, nullable=False, default=utc_now_naive)
    blocked_until = db.Column(db.DateTime, nullable=True)

    __table_args__ = (
        db.UniqueConstraint("action", "scope", "identifier", name="uq_auth_rate_limit_key"),
    )
