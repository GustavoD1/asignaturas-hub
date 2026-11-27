"""HTTP integration tests for auth via the Flask test client."""

import time

import pytest

from app import db
from app.features.auth.models import User

pytestmark = pytest.mark.integration


def test_login_page_renders(test_client):
    response = test_client.get("/login")
    assert response.status_code == 200


def test_signup_page_renders(test_client):
    response = test_client.get("/signup/")
    assert response.status_code == 200


def test_signup_then_login_round_trip(test_client):
    signup = test_client.post(
        "/signup/",
        data={
            "email": "carol@example.com",
            "password": "carolpass",
            "name": "Carol",
            "surname": "Smith",
        },
        follow_redirects=False,
    )
    assert signup.status_code in (302, 303)

    # Logout to clear the session, then log back in with the new credentials.
    test_client.get("/logout", follow_redirects=False)
    login = test_client.post(
        "/login",
        data={"email": "carol@example.com", "password": "carolpass"},
        follow_redirects=False,
    )
    assert login.status_code in (302, 303)


def test_login_with_invalid_credentials_keeps_form(test_client):
    response = test_client.post(
        "/login",
        data={"email": "nobody@example.com", "password": "wrong"},
        follow_redirects=False,
    )
    assert response.status_code == 200


def test_login_blocks_after_n_failed_attempts_for_existing_user(test_client):
    """
    After N failed login attempts, the (N + 1)th attempt must be blocked
    with HTTP 429 — even if the correct password is supplied.
    """
    email = "bruteforce_target@example.com"
    password = "ValidPassword123!"

    with test_client.application.app_context():
        user = User.query.filter_by(email=email).first()
        if not user:
            user = User(email=email)
            user.set_password(password)
            db.session.add(user)
            db.session.commit()

    max_attempts = 3
    test_client.application.config["AUTH_MAX_ATTEMPTS"] = max_attempts
    test_client.application.config["AUTH_LOCKOUT_SECONDS"] = 300
    client_ip = "203.0.113.10"

    for attempt in range(max_attempts):
        response = test_client.post(
            "/login",
            data={"email": email, "password": f"WrongPassword_{attempt}!"},
            environ_base={"REMOTE_ADDR": client_ip},
            follow_redirects=False,
        )
        assert response.status_code == 200

    # Attempt N + 1: must be blocked even with the valid password
    blocked_response = test_client.post(
        "/login",
        data={"email": email, "password": password},
        environ_base={"REMOTE_ADDR": client_ip},
        follow_redirects=False,
    )

    assert blocked_response.status_code == 429
    page_text = blocked_response.get_data(as_text=True).lower()
    assert "try again" in page_text or "too many" in page_text


def test_login_blocks_after_n_failed_attempts_for_nonexistent_email(test_client):
    """
    Repeated failed logins for a non-existent email must also trigger
    a block after N attempts.
    """
    max_attempts = 3
    test_client.application.config["AUTH_MAX_ATTEMPTS"] = max_attempts
    test_client.application.config["AUTH_LOCKOUT_SECONDS"] = 300
    client_ip = "203.0.113.11"
    unknown_email = "nobody_here@example.com"

    for i in range(max_attempts):
        response = test_client.post(
            "/login",
            data={"email": unknown_email, "password": "WrongPassword123!"},
            environ_base={"REMOTE_ADDR": client_ip},
            follow_redirects=False,
        )
        assert response.status_code == 200

    blocked_response = test_client.post(
        "/login",
        data={"email": unknown_email, "password": "WrongPassword123!"},
        environ_base={"REMOTE_ADDR": client_ip},
        follow_redirects=False,
    )

    assert blocked_response.status_code == 429


def test_successful_login_resets_failed_attempt_counter(test_client):
    """
    Failing (N - 1) times and then logging in with valid credentials
    must reset the counter so the user gets a fresh N attempts afterward.
    """
    email = "reset_target@example.com"
    password = "ValidPassword123!"

    with test_client.application.app_context():
        user = User.query.filter_by(email=email).first()
        if not user:
            user = User(email=email)
            user.set_password(password)
            db.session.add(user)
            db.session.commit()

    max_attempts = 3
    test_client.application.config["AUTH_MAX_ATTEMPTS"] = max_attempts
    test_client.application.config["AUTH_LOCKOUT_SECONDS"] = 300
    client_ip = "203.0.113.12"

    # Fail (N - 1) times
    for i in range(max_attempts - 1):
        res = test_client.post(
            "/login",
            data={"email": email, "password": "WrongPassword!"},
            environ_base={"REMOTE_ADDR": client_ip},
            follow_redirects=False,
        )
        assert res.status_code == 200

    # Valid login must succeed and reset counter
    ok_res = test_client.post(
        "/login",
        data={"email": email, "password": password},
        environ_base={"REMOTE_ADDR": client_ip},
        follow_redirects=False,
    )
    assert ok_res.status_code == 302

    test_client.get("/logout", follow_redirects=False)

    # Should have a full N attempts available again before being blocked
    for i in range(max_attempts):
        res = test_client.post(
            "/login",
            data={"email": email, "password": "WrongPassword!"},
            environ_base={"REMOTE_ADDR": client_ip},
            follow_redirects=False,
        )
        assert res.status_code == 200


def test_login_lockout_expires_after_window(test_client):
    """
    Once blocked after N failed attempts, login must be allowed again
    after AUTH_LOCKOUT_SECONDS has elapsed.
    """
    email = "expire_target@example.com"
    password = "ValidPassword123!"

    with test_client.application.app_context():
        user = User.query.filter_by(email=email).first()
        if not user:
            user = User(email=email)
            user.set_password(password)
            db.session.add(user)
            db.session.commit()

    max_attempts = 2
    test_client.application.config["AUTH_MAX_ATTEMPTS"] = max_attempts
    test_client.application.config["AUTH_LOCKOUT_SECONDS"] = 1
    client_ip = "203.0.113.13"

    for i in range(max_attempts):
        test_client.post(
            "/login",
            data={"email": email, "password": "WrongPassword!"},
            environ_base={"REMOTE_ADDR": client_ip},
            follow_redirects=False,
        )

    blocked_res = test_client.post(
        "/login",
        data={"email": email, "password": password},
        environ_base={"REMOTE_ADDR": client_ip},
        follow_redirects=False,
    )
    assert blocked_res.status_code == 429

    # Wait for lockout window to expire
    time.sleep(3.1)

    # First wrong attempt after expiration must NOT immediately re-lock the user
    wrong_after_expiry = test_client.post(
        "/login",
        data={"email": email, "password": "WrongPassword!"},
        environ_base={"REMOTE_ADDR": client_ip},
        follow_redirects=False,
    )
    assert wrong_after_expiry.status_code == 200

    # 2. Valid login on the remaining attempt must succeed
    unblocked_res = test_client.post(
        "/login",
        data={"email": email, "password": password},
        environ_base={"REMOTE_ADDR": client_ip},
        follow_redirects=False,
    )
    assert unblocked_res.status_code == 302


def test_signup_blocks_after_n_failed_attempts_and_ignores_blank_fields(test_client):
    """
    - Blank required fields must NOT consume signup rate-limit attempts.
    - After N failed signup attempts (existing email) from an IP,
      attempt N + 1 must be blocked with HTTP 429.
    """
    existing_email = "signup_probe@example.com"
    with test_client.application.app_context():
        user = User.query.filter_by(email=existing_email).first()
        if not user:
            user = User(email=existing_email)
            user.set_password("ValidPassword123!")
            db.session.add(user)
            db.session.commit()

    max_attempts = 2
    test_client.application.config["AUTH_MAX_ATTEMPTS"] = max_attempts
    test_client.application.config["AUTH_LOCKOUT_SECONDS"] = 300
    client_ip = "203.0.113.20"

    # 1. Missing required fields must NOT consume attempts
    for _ in range(max_attempts + 1):
        blank_res = test_client.post(
            "/signup/",
            data={"email": "", "password": "", "name": "", "surname": ""},
            environ_base={"REMOTE_ADDR": client_ip},
            follow_redirects=False,
        )
        assert blank_res.status_code == 200

    # 2. N failed signups (email already in use) exhaust the quota
    for i in range(max_attempts):
        probe_res = test_client.post(
            "/signup/",
            data={
                "email": existing_email,
                "password": "ValidPassword123!",
                "name": "Test",
                "surname": "User",
            },
            environ_base={"REMOTE_ADDR": client_ip},
            follow_redirects=False,
        )
        assert probe_res.status_code == 200

    # 3. Attempt N + 1 from the same IP must be blocked with 429
    blocked_res = test_client.post(
        "/signup/",
        data={
            "email": "brand_new_account@example.com",
            "password": "ValidPassword123!",
            "name": "Test",
            "surname": "User",
        },
        environ_base={"REMOTE_ADDR": client_ip},
        follow_redirects=False,
    )
    assert blocked_res.status_code == 429
    assert b"rate-limit-alert" in blocked_res.data


def test_signup_blank_fields_do_not_consume_attempts(test_client):
    """Submitting /signup/ with missing required fields must not count toward the rate limit."""
    max_attempts = 2
    test_client.application.config["AUTH_MAX_ATTEMPTS"] = max_attempts
    test_client.application.config["AUTH_LOCKOUT_SECONDS"] = 300
    client_ip = "203.0.113.23"

    # Submit blank fields more times than max_attempts
    for _ in range(max_attempts + 1):
        blank_res = test_client.post(
            "/signup/",
            data={"email": "", "password": "", "name": "", "surname": ""},
            environ_base={"REMOTE_ADDR": client_ip},
            follow_redirects=False,
        )
        assert blank_res.status_code == 200

    # A valid signup afterward must still succeed (quota was untouched)
    valid_res = test_client.post(
        "/signup/",
        data={
            "email": "after_blank_signup@example.com",
            "password": "ValidPassword123!",
            "name": "Test",
            "surname": "User",
        },
        environ_base={"REMOTE_ADDR": client_ip},
        follow_redirects=False,
    )
    assert valid_res.status_code == 302


def test_signup_blocks_after_n_successful_registrations_from_same_ip(test_client):
    """
    Successful signups must also count toward the IP rate limit (never reset on success)
    so a single IP cannot spam unlimited new accounts.
    """
    max_attempts = 2
    test_client.application.config["AUTH_MAX_ATTEMPTS"] = max_attempts
    test_client.application.config["AUTH_LOCKOUT_SECONDS"] = 300
    client_ip = "203.0.113.21"

    for i in range(max_attempts):
        res = test_client.post(
            "/signup/",
            data={
                "email": f"spam_user_{i}@example.com",
                "password": "ValidPassword123!",
                "name": "Spam",
                "surname": f"User{i}",
            },
            environ_base={"REMOTE_ADDR": client_ip},
            follow_redirects=False,
        )
        assert res.status_code == 302
        # Log out so the next request reaches the signup rate limiter
        test_client.get("/logout", follow_redirects=False)

    # Attempt N + 1 from the same IP must be blocked with 429
    blocked_res = test_client.post(
        "/signup/",
        data={
            "email": "spam_user_blocked@example.com",
            "password": "ValidPassword123!",
            "name": "Spam",
            "surname": "Blocked",
        },
        environ_base={"REMOTE_ADDR": client_ip},
        follow_redirects=False,
    )
    assert blocked_res.status_code == 429


def test_signup_lockout_expires_after_window(test_client):
    """
    Once signup is blocked after N attempts, new signup attempts from that IP
    must be allowed again with a fresh N-attempt quota after AUTH_LOCKOUT_SECONDS.
    """
    existing_email = "signup_expire_probe@example.com"
    with test_client.application.app_context():
        user = User.query.filter_by(email=existing_email).first()
        if not user:
            user = User(email=existing_email)
            user.set_password("ValidPassword123!")
            db.session.add(user)
            db.session.commit()

    max_attempts = 2
    test_client.application.config["AUTH_MAX_ATTEMPTS"] = max_attempts
    test_client.application.config["AUTH_LOCKOUT_SECONDS"] = 2
    client_ip = "203.0.113.22"

    for i in range(max_attempts):
        test_client.post(
            "/signup/",
            data={
                "email": existing_email,
                "password": "ValidPassword123!",
                "name": "Test",
                "surname": "User",
            },
            environ_base={"REMOTE_ADDR": client_ip},
            follow_redirects=False,
        )

    blocked_res = test_client.post(
        "/signup/",
        data={
            "email": "after_expiry_signup@example.com",
            "password": "ValidPassword123!",
            "name": "Test",
            "surname": "User",
        },
        environ_base={"REMOTE_ADDR": client_ip},
        follow_redirects=False,
    )
    assert blocked_res.status_code == 429

    # Wait for lockout window to expire (2s + margin for MariaDB DATETIME truncation)
    time.sleep(2.1)

    # First failed attempt after expiration must use 1 of 2 fresh attempts (not re-lock)
    probe_after_expiry = test_client.post(
        "/signup/",
        data={
            "email": existing_email,
            "password": "ValidPassword123!",
            "name": "Test",
            "surname": "User",
        },
        environ_base={"REMOTE_ADDR": client_ip},
        follow_redirects=False,
    )
    assert probe_after_expiry.status_code == 200

    # Second attempt (valid signup) must succeed with 302
    unblocked_res = test_client.post(
        "/signup/",
        data={
            "email": "after_expiry_signup@example.com",
            "password": "ValidPassword123!",
            "name": "Test",
            "surname": "User",
        },
        environ_base={"REMOTE_ADDR": client_ip},
        follow_redirects=False,
    )
    assert unblocked_res.status_code == 302
