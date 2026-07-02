"""
app/user/forms.py – WTForms for the user dashboard area.
"""

from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import (
    StringField, PasswordField, TextAreaField, FloatField, SubmitField
)
from wtforms.validators import DataRequired, Email, Length, Optional, NumberRange, EqualTo


class ProfileForm(FlaskForm):
    name = StringField("Full Name", validators=[DataRequired(), Length(min=2, max=100)])
    email = StringField("Email", validators=[DataRequired(), Email()])
    phone = StringField("Phone Number", validators=[Optional(), Length(max=20)])
    bio = TextAreaField("Bio", validators=[Optional(), Length(max=300)])
    profile_pic = FileField(
        "Profile Picture",
        validators=[FileAllowed(["jpg", "jpeg", "png", "gif", "webp"], "Images only!")],
    )
    submit = SubmitField("Save Changes")


class ChangePasswordForm(FlaskForm):
    current_password = PasswordField("Current Password", validators=[DataRequired()])
    new_password = PasswordField(
        "New Password",
        validators=[DataRequired(), Length(min=8)],
    )
    confirm_password = PasswordField(
        "Confirm New Password",
        validators=[DataRequired(), EqualTo("new_password", message="Passwords must match.")],
    )
    submit = SubmitField("Change Password")


class TaskSubmissionForm(FlaskForm):
    proof_text = TextAreaField(
        "Proof Description",
        validators=[Optional(), Length(max=1000)],
        description="Briefly describe how you completed the task.",
    )
    proof_screenshot = FileField(
        "Proof Screenshot",
        validators=[FileAllowed(["jpg", "jpeg", "png", "gif", "webp"], "Images only!")],
    )
    submit = SubmitField("Submit Task")


class WithdrawalForm(FlaskForm):
    amount = FloatField(
        "Amount (₹)",
        validators=[DataRequired(), NumberRange(min=1, message="Amount must be positive.")],
    )
    upi_id = StringField(
        "UPI ID",
        validators=[DataRequired(), Length(max=100)],
        description="e.g. yourname@upi",
    )
    submit = SubmitField("Request Withdrawal")
