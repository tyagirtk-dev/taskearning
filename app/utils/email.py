"""
app/utils/email.py – Centralised email sending helpers.
All email rendering and delivery is done here so blueprints stay lean.
"""

from flask import current_app, render_template
from flask_mail import Message
from app import mail


def _send(subject: str, recipients: list[str], html_body: str, text_body: str = "") -> None:
    """Low-level send wrapper with basic error swallowing so app keeps running."""
    msg = Message(subject=subject, recipients=recipients, sender=current_app.config["MAIL_DEFAULT_SENDER"])
    msg.html = html_body
    msg.body = text_body or "Please view this email in an HTML-capable client."
    try:
        mail.send(msg)
    except Exception as exc:
        current_app.logger.error(f"[Mail] Failed to send to {recipients}: {exc}")


def send_verification_email(user, otp: str) -> None:
    html = render_template("emails/verify_email.html", user=user, otp=otp)
    _send(
        subject=f"Verify your {current_app.config['APP_NAME']} account",
        recipients=[user.email],
        html_body=html,
    )


def send_welcome_email(user) -> None:
    html = render_template("emails/welcome.html", user=user)
    _send(
        subject=f"Welcome to {current_app.config['APP_NAME']}!",
        recipients=[user.email],
        html_body=html,
    )


def send_password_reset_email(user, otp: str) -> None:
    html = render_template("emails/password_reset.html", user=user, otp=otp)
    _send(
        subject=f"Reset your {current_app.config['APP_NAME']} password",
        recipients=[user.email],
        html_body=html,
    )


def send_task_approved_email(user, submission) -> None:
    html = render_template("emails/task_approved.html", user=user, submission=submission)
    _send(
        subject="Your task submission was approved! 🎉",
        recipients=[user.email],
        html_body=html,
    )


def send_task_rejected_email(user, submission) -> None:
    html = render_template("emails/task_rejected.html", user=user, submission=submission)
    _send(
        subject="Update on your task submission",
        recipients=[user.email],
        html_body=html,
    )


def send_withdrawal_approved_email(user, withdrawal) -> None:
    html = render_template("emails/withdrawal_approved.html", user=user, withdrawal=withdrawal)
    _send(
        subject="Your withdrawal has been processed ✅",
        recipients=[user.email],
        html_body=html,
    )


def send_withdrawal_rejected_email(user, withdrawal) -> None:
    html = render_template("emails/withdrawal_rejected.html", user=user, withdrawal=withdrawal)
    _send(
        subject="Update on your withdrawal request",
        recipients=[user.email],
        html_body=html,
    )
