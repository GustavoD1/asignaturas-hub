from flask import redirect, render_template, request, url_for
from flask_login import current_user, login_user, logout_user
from splent_framework.utils.form_helpers import form_error

from app.features.auth import auth_bp
from app.features.auth.forms import LoginForm, SignupForm
from app.features.auth.services import AuthenticationService, AuthRateLimitService
from app.features.profile.services import UserProfileService

authentication_service = AuthenticationService()
user_profile_service = UserProfileService()
rate_limit_service = AuthRateLimitService()


@auth_bp.route("/signup/", methods=["GET", "POST"])
def show_signup_form():
    if current_user.is_authenticated:
        return redirect(url_for("public.index"))

    form = SignupForm()

    # Rate limit for registered users on signup
    rate_limit = {"is_blocked": False, "retry_after": 0, "attempts_left": None}

    if request.method == "POST":
        email = (form.email.data or request.form.get("email", "")).strip()
        ip_address = rate_limit_service.get_client_ip()

        current_status = rate_limit_service.check_rate_limit(
            email, ip_address, action="signup"
        )
        if current_status["is_blocked"]:
            return (
                render_template(
                    "auth/signup_form.html",
                    form=form,
                    rate_limit=current_status,
                ),
                429,
            )

    if form.validate_on_submit():
        email = form.email.data
        if not authentication_service.is_email_available(email):
            rate_limit = rate_limit_service.record_attempt(
                    email, ip_address, action="signup"
                )
            form.email.errors = list(form.email.errors) + [f"{email} in use"]
            return (
                render_template(
                    "auth/signup_form.html",
                    form=form,
                    rate_limit=rate_limit,
                ),
                200,
            )

        # Tracking successful signup to rate limit signups spams
        rate_limit_service.record_attempt(email, ip_address, action="signup") 
        
        user = authentication_service.create_with_profile(**form.data)
        login_user(user, remember=True)
        return redirect(url_for("public.index"))

    return render_template("auth/signup_form.html", form=form, rate_limit=rate_limit), 200


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("public.index"))

    form = LoginForm()
    rate_limit = {"is_blocked": False, "retry_after": 0, "attempts_left": None}
    
    if request.method == "POST":
        email = (form.email.data or request.form.get("email", "")).strip()
        ip_address = rate_limit_service.get_client_ip()

        # 1. Pre-check: block immediately with HTTP 429 if already locked out
        current_status = rate_limit_service.check_rate_limit(email, ip_address, action="login")
        if current_status["is_blocked"]:
            return (
                render_template(
                    "auth/login_form.html",
                    form=form,
                    rate_limit=current_status,
                ),
                429,
            )

        # 2. Validate credentials if form passes WTForms validation
        if form.validate_on_submit():
            if authentication_service.login(email, form.password.data):
                rate_limit_service.reset_rate_limit(email, ip_address, action="login")
                return redirect(url_for("public.index"))

            # 3. Record failure for BOTH existing and non-existent emails
            rate_limit = rate_limit_service.record_failed_attempt(email, ip_address, action="login")

    return render_template("auth/login_form.html", form=form, rate_limit=rate_limit), 200


@auth_bp.route("/logout")
def logout():
    logout_user()
    return redirect(url_for("public.index"))
