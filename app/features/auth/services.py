import math
import os
from datetime import timedelta

from flask import current_app, request
from flask_login import current_user, login_user
from splent_framework.configuration.configuration import uploads_folder_name
from splent_framework.services.BaseService import BaseService

from app.features.auth.models import AuthRateLimit, User, utc_now_naive
from app.features.auth.repositories import UserRepository, AuthRateLimitRepository
from app.features.profile.models import UserProfile
from app.features.profile.repositories import UserProfileRepository


class AuthenticationService(BaseService):
    def __init__(self):
        super().__init__(UserRepository())
        self.user_profile_repository = UserProfileRepository()

    def login(self, email, password, remember=True):
        user = self.repository.get_by_email(email)
        if user is not None and user.check_password(password):
            login_user(user, remember=remember)
            return True
        return False

    def is_email_available(self, email: str) -> bool:
        return self.repository.get_by_email(email) is None

    def create_with_profile(self, **kwargs):
        try:
            email = kwargs.pop("email", None)
            password = kwargs.pop("password", None)
            name = kwargs.pop("name", None)
            surname = kwargs.pop("surname", None)

            if not email:
                raise ValueError("Email is required.")
            if not password:
                raise ValueError("Password is required.")
            if not name:
                raise ValueError("Name is required.")
            if not surname:
                raise ValueError("Surname is required.")

            user_data = {"email": email, "password": password}

            profile_data = {
                "name": name,
                "surname": surname,
            }

            user = self.create(commit=False, **user_data)
            profile_data["user_id"] = user.id
            self.user_profile_repository.create(**profile_data)
            self.repository.session.commit()
        except Exception as exc:
            self.repository.session.rollback()
            raise exc
        return user

    def get_authenticated_user(self) -> User | None:
        if current_user.is_authenticated:
            return current_user
        return None

    def get_authenticated_user_profile(self) -> UserProfile | None:
        if current_user.is_authenticated:
            return current_user.profile
        return None

    def temp_folder_by_user(self, user: User) -> str:
        return os.path.join(uploads_folder_name(), "temp", str(user.id))


class AuthRateLimitService:
    def __init__(self):
        self.repository = AuthRateLimitRepository()

    @property
    def max_attempts(self) -> int:
        return int(
            current_app.config.get(
                "AUTH_MAX_ATTEMPTS",
                os.getenv("AUTH_MAX_ATTEMPTS", 5),
            )
        )

    @property
    def lockout_seconds(self) -> int:
        return int(
            current_app.config.get(
                "AUTH_LOCKOUT_SECONDS",
                os.getenv("AUTH_LOCKOUT_SECONDS", 300),
            )
        )

    @staticmethod
    def get_client_ip() -> str:
        forwarded_for = request.headers.get("X-Forwarded-For", "")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        return (request.remote_addr or "unknown").strip()

    @staticmethod
    def normalize_email(email: str) -> str:
        return (email or "").strip().lower()

    def _refresh_if_expired(self, record: AuthRateLimit, now) -> None:
        """Reset counter if the lockout or tracking window has elapsed."""
        window_expired = (now - record.window_start).total_seconds() >= self.lockout_seconds
        lockout_expired = record.blocked_until is not None and now >= record.blocked_until

        if lockout_expired or (record.blocked_until is None and window_expired):
            record.attempts = 0
            record.window_start = now
            record.blocked_until = None
            self.repository.save(record)

    def _retry_after(self, record: AuthRateLimit, now) -> int:
        if record.blocked_until and now < record.blocked_until:
            return max(1, math.ceil((record.blocked_until - now).total_seconds()))
        return 0

    def check_rate_limit(self, email: str, ip_address: str, action: str = "login") -> dict:
        """Check whether either the email or IP is currently blocked."""
        now = utc_now_naive()
        norm_email = self.normalize_email(email)
        max_tries = self.max_attempts

        targets = [("ip", ip_address)]
        if norm_email:
            targets.append(("email", norm_email))

        is_blocked = False
        max_retry = 0
        min_attempts_left = max_tries

        for scope, identifier in targets:
            record = self.repository.get_record(action, scope, identifier)
            if record is None:
                continue

            self._refresh_if_expired(record, now)
            retry = self._retry_after(record, now)

            if record.attempts >= max_tries and retry > 0:
                is_blocked = True
                max_retry = max(max_retry, retry)
                min_attempts_left = 0
            else:
                min_attempts_left = min(min_attempts_left, max(0, max_tries - record.attempts))

        return {
            "is_blocked": is_blocked,
            "retry_after": max_retry,
            "attempts_left": min_attempts_left,
        }

    def record_attempt(self, email: str, ip_address: str, action: str = "login") -> dict:
        """Increment failed attempt counters for both email and IP."""
        now = utc_now_naive()
        norm_email = self.normalize_email(email)
        max_tries = self.max_attempts
        lock_duration = self.lockout_seconds

        targets = [("ip", ip_address)]
        if norm_email:
            targets.append(("email", norm_email))

        is_blocked = False
        max_retry = 0
        min_attempts_left = max_tries

        for scope, identifier in targets:
            record = self.repository.get_or_create(action, scope, identifier)
            self._refresh_if_expired(record, now)

            if record.attempts == 0:
                record.window_start = now

            record.attempts += 1

            if record.attempts >= max_tries:
                if record.blocked_until is None or now >= record.blocked_until:
                    record.blocked_until = now + timedelta(seconds=lock_duration)
                is_blocked = True
                max_retry = max(max_retry, self._retry_after(record, now))
                min_attempts_left = 0
            else:
                min_attempts_left = min(min_attempts_left, max_tries - record.attempts)

            self.repository.save(record)

        return {
            "is_blocked": is_blocked,
            "retry_after": max_retry,
            "attempts_left": min_attempts_left,
        }

    # Alias so login code reads naturally
    record_failed_attempt = record_attempt

    def reset_rate_limit(self, email: str, ip_address: str, action: str = "login") -> None:
        """Clear counters after a successful authentication."""
        norm_email = self.normalize_email(email)
        if norm_email:
            self.repository.delete_record(action, "email", norm_email)
        if ip_address:
            self.repository.delete_record(action, "ip", ip_address)
