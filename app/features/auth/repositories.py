from splent_framework.repositories.BaseRepository import BaseRepository

from app.features.auth.models import User

from typing import Optional
from sqlalchemy.exc import IntegrityError
from app import db
from app.features.auth.models import AuthRateLimit, utc_now_naive


class UserRepository(BaseRepository):
    def __init__(self):
        super().__init__(User)

    def create(self, commit: bool = True, **kwargs):
        password = kwargs.pop("password")
        instance = self.model(**kwargs)
        instance.set_password(password)
        self.session.add(instance)
        if commit:
            self.session.commit()
        else:
            self.session.flush()
        return instance

    def get_by_email(self, email: str):
        return self.model.query.filter_by(email=email).first()


# Methods to handle db operations for AuthRateLimit model
class AuthRateLimitRepository(BaseRepository):
    def __init__(self):
        super().__init__(AuthRateLimit)

    def get_record(self, action: str, scope: str, identifier: str) -> Optional[AuthRateLimit]:
        return (
            AuthRateLimit.query.filter_by(
                action=action,
                scope=scope,
                identifier=identifier,
            )
            .first()
        )

    def get_or_create(self, action: str, scope: str, identifier: str) -> AuthRateLimit:
        record = self.get_record(action, scope, identifier)
        if record is not None:
            return record
        
        record = AuthRateLimit(
            action=action,
            scope=scope,
            identifier=identifier,
            attempts=0,
            window_start=utc_now_naive(),
            blocked_until=None,
        )
        try:
            db.session.add(record)
            db.session.commit()
            return record
        except IntegrityError:
            db.session.rollback()
            return self.get_record(action, scope, identifier)

    def save(self, record: AuthRateLimit) -> AuthRateLimit:
        db.session.add(record)
        db.session.commit()
        return record

    def delete_record(self, action: str, scope: str, identifier: str) -> None:
        record = self.get_record(action, scope, identifier)
        if record is not None:
            db.session.delete(record)
            db.session.commit()