"""
app/auth/routes.py – Registration, login, OTP verification, password reset.
"""

from datetime import datetime
from flask import (
    render_template, redirect, url_for, flash, request, session, current_app
)
from flask_login import login_user, logout_user, login_required, current_user
from app import db, limiter
from app.models import User, EmailVerificationToken
from app.utils.email import (
    send_verification_email, send_welcome_email, send_password_reset_email
)
from .forms import (
    RegistrationForm, LoginForm, OTPVerificationForm,
    ForgotPasswordForm, ResetPasswordForm
)
from . import auth_bp


# ─────────────────────────────────────────────────────────────────────────────
#  Registration
# ─────────────────────────────────────────────────────────────────────────────

@auth_bp.route("/register", methods=["GET", "POST"])
@limiter.limit("10 per hour")
def register():
    if current_user.is_authenticated:
        return redirect(url_for("user.dashboard"))

    form = RegistrationForm()
    if form.validate_on_submit():
        # Duplicate e-mail check
        if User.query.filter_by(email=form.email.data.lower()).first():
            flash("An account with this email already exists.", "danger")
            return render_template("auth/register.html", form=form)

        # Handle referral
        referrer = None
        if form.referral_code.data:
            referrer = User.query.filter_by(referral_code=form.referral_code.data.upper()).first()

        user = User(
            name=form.name.data.strip(),
            email=form.email.data.lower().strip(),
            referred_by_id=referrer.id if referrer else None,
        )
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.flush()  # get user.id before commit

        # Create OTP
        token = EmailVerificationToken.create(user.id, "email_verify", expire_minutes=15)
        db.session.add(token)
        db.session.commit()

        send_verification_email(user, token.token)

        session["pending_verify_email"] = user.email
        flash("A 6-digit OTP has been sent to your email. Please verify.", "info")
        return redirect(url_for("auth.verify_email"))

    return render_template("auth/register.html", form=form)


# ─────────────────────────────────────────────────────────────────────────────
#  Email OTP Verification
# ─────────────────────────────────────────────────────────────────────────────

@auth_bp.route("/verify-email", methods=["GET", "POST"])
def verify_email():
    email = session.get("pending_verify_email")
    if not email:
        return redirect(url_for("auth.login"))

    user = User.query.filter_by(email=email).first_or_404()
    if user.is_email_verified:
        session.pop("pending_verify_email", None)
        return redirect(url_for("auth.login"))

    form = OTPVerificationForm()
    if form.validate_on_submit():
        token = (
            EmailVerificationToken.query
            .filter_by(user_id=user.id, token_type="email_verify", is_used=False)
            .order_by(EmailVerificationToken.created_at.desc())
            .first()
        )
        if not token or token.is_expired:
            flash("OTP expired. Please request a new one.", "danger")
            return render_template("auth/verify_email.html", form=form, email=email)

        if token.token != form.otp.data.strip():
            flash("Invalid OTP. Please try again.", "danger")
            return render_template("auth/verify_email.html", form=form, email=email)

        token.is_used = True
        user.is_email_verified = True
        db.session.commit()

        send_welcome_email(user)
        session.pop("pending_verify_email", None)
        flash("Email verified! You can now log in.", "success")
        return redirect(url_for("auth.login"))

    return render_template("auth/verify_email.html", form=form, email=email)


@auth_bp.route("/resend-otp")
@limiter.limit("3 per 10 minutes")
def resend_otp():
    email = session.get("pending_verify_email")
    if not email:
        return redirect(url_for("auth.login"))
    user = User.query.filter_by(email=email).first_or_404()
    token = EmailVerificationToken.create(user.id, "email_verify", 15)
    db.session.add(token)
    db.session.commit()
    send_verification_email(user, token.token)
    flash("A new OTP has been sent to your email.", "info")
    return redirect(url_for("auth.verify_email"))


# ─────────────────────────────────────────────────────────────────────────────
#  Login / Logout
# ─────────────────────────────────────────────────────────────────────────────

@auth_bp.route("/login", methods=["GET", "POST"])
@limiter.limit("20 per hour")
def login():
    if current_user.is_authenticated:
        return redirect(url_for("user.dashboard"))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data.lower()).first()

        if not user or not user.check_password(form.password.data):
            flash("Invalid email or password.", "danger")
            return render_template("auth/login.html", form=form)

        if user.is_banned:
            flash(f"Your account has been suspended. Reason: {user.ban_reason}", "danger")
            return render_template("auth/login.html", form=form)

        if not user.is_email_verified:
            session["pending_verify_email"] = user.email
            flash("Please verify your email before logging in.", "warning")
            return redirect(url_for("auth.verify_email"))

        login_user(user, remember=form.remember_me.data)
        user.last_login = datetime.utcnow()
        db.session.commit()

        next_page = request.args.get("next")
        flash(f"Welcome back, {user.name}!", "success")
        return redirect(next_page or url_for("user.dashboard"))

    return render_template("auth/login.html", form=form)


@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You have been logged out.", "info")
    return redirect(url_for("auth.login"))


# ─────────────────────────────────────────────────────────────────────────────
#  Forgot / Reset Password
# ─────────────────────────────────────────────────────────────────────────────

@auth_bp.route("/forgot-password", methods=["GET", "POST"])
@limiter.limit("5 per hour")
def forgot_password():
    form = ForgotPasswordForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data.lower()).first()
        if user:
            token = EmailVerificationToken.create(user.id, "password_reset", expire_minutes=30)
            db.session.add(token)
            db.session.commit()
            send_password_reset_email(user, token.token)
            session["reset_email"] = user.email
        # Always show the same message to avoid email enumeration
        flash("If that email is registered, you'll receive an OTP shortly.", "info")
        return redirect(url_for("auth.reset_password"))

    return render_template("auth/forgot_password.html", form=form)


@auth_bp.route("/reset-password", methods=["GET", "POST"])
def reset_password():
    email = session.get("reset_email")
    if not email:
        return redirect(url_for("auth.forgot_password"))

    form = ResetPasswordForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=email).first_or_404()
        token = (
            EmailVerificationToken.query
            .filter_by(user_id=user.id, token_type="password_reset", is_used=False)
            .order_by(EmailVerificationToken.created_at.desc())
            .first()
        )
        if not token or token.is_expired:
            flash("OTP expired. Please request a new reset.", "danger")
            session.pop("reset_email", None)
            return redirect(url_for("auth.forgot_password"))

        if token.token != form.otp.data.strip():
            flash("Invalid OTP.", "danger")
            return render_template("auth/reset_password.html", form=form)

        token.is_used = True
        user.set_password(form.password.data)
        db.session.commit()

        session.pop("reset_email", None)
        flash("Password reset successfully. Please log in.", "success")
        return redirect(url_for("auth.login"))

    return render_template("auth/reset_password.html", form=form)
