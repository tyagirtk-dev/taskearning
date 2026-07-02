"""
app/auth/forms.py – WTForms for authentication flows.
"""

from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Email, EqualTo, Length, Regexp


class RegistrationForm(FlaskForm):
    name = StringField(
        "Full Name",
        validators=[DataRequired(), Length(min=2, max=100)],
    )
    email = StringField(
        "Email Address",
        validators=[DataRequired(), Email(), Length(max=150)],
    )
    password = PasswordField(
        "Password",
        validators=[
            DataRequired(),
            Length(min=8, message="Password must be at least 8 characters."),
            Regexp(
                r"(?=.*[A-Z])(?=.*\d)",
                message="Password must contain at least one uppercase letter and one digit.",
            ),
        ],
    )
    confirm_password = PasswordField(
        "Confirm Password",
        validators=[DataRequired(), EqualTo("password", message="Passwords must match.")],
    )
    referral_code = StringField("Referral Code (optional)", validators=[Length(max=12)])
    submit = SubmitField("Create Account")


class LoginForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired()])
    remember_me = BooleanField("Remember me")
    submit = SubmitField("Sign In")


class OTPVerificationForm(FlaskForm):
    otp = StringField(
        "Enter OTP",
        validators=[DataRequired(), Length(min=6, max=6, message="OTP must be 6 digits.")],
    )
    submit = SubmitField("Verify")


class ForgotPasswordForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email()])
    submit = SubmitField("Send Reset Code")


class ResetPasswordForm(FlaskForm):
    otp = StringField("OTP Code", validators=[DataRequired(), Length(min=6, max=6)])
    password = PasswordField(
        "New Password",
        validators=[
            DataRequired(),
            Length(min=8),
            Regexp(r"(?=.*[A-Z])(?=.*\d)", message="Must contain uppercase and digit."),
        ],
    )
    confirm_password = PasswordField(
        "Confirm Password",
        validators=[DataRequired(), EqualTo("password", message="Passwords must match.")],
    )
    submit = SubmitField("Reset Password")
