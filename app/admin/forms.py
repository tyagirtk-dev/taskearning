"""
app/admin/forms.py – WTForms for the admin panel.
"""

from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import (
    StringField, TextAreaField, FloatField, IntegerField, BooleanField,
    SelectField, PasswordField, SubmitField, URLField
)
from wtforms.validators import DataRequired, Email, Length, Optional, NumberRange


class AdminLoginForm(FlaskForm):
    email = StringField("Admin Email", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField("Sign In")


class TaskForm(FlaskForm):
    title = StringField("Task Title", validators=[DataRequired(), Length(max=200)])
    description = TextAreaField("Description", validators=[DataRequired()])
    instructions = TextAreaField(
        "Step-by-step Instructions", validators=[DataRequired()]
    )
    category = SelectField(
        "Category",
        choices=[
            ("general", "General"),
            ("social", "Social Media"),
            ("survey", "Survey"),
            ("review", "Review"),
            ("app", "App Install"),
            ("youtube", "YouTube"),
            ("other", "Other"),
        ],
    )
    reward = FloatField("Reward (₹)", validators=[DataRequired(), NumberRange(min=0.01)])
    time_limit_hours = IntegerField(
        "Time Limit (hours)", validators=[DataRequired(), NumberRange(min=1, max=720)], default=24
    )
    max_submissions = IntegerField(
        "Max Submissions", validators=[DataRequired(), NumberRange(min=1)], default=100
    )
    external_url = URLField("External URL", validators=[Optional(), Length(max=500)])
    thumbnail = FileField(
        "Thumbnail Image",
        validators=[FileAllowed(["jpg", "jpeg", "png", "gif", "webp"], "Images only!")],
    )
    requires_proof = BooleanField("Require Proof Screenshot", default=True)
    is_active = BooleanField("Active", default=True)
    submit = SubmitField("Save Task")


class ReviewSubmissionForm(FlaskForm):
    action = SelectField(
        "Action",
        choices=[("approve", "Approve"), ("reject", "Reject")],
        validators=[DataRequired()],
    )
    rejection_reason = TextAreaField(
        "Rejection Reason",
        validators=[Optional(), Length(max=500)],
        description="Required if rejecting.",
    )
    submit = SubmitField("Submit Review")


class ReviewWithdrawalForm(FlaskForm):
    action = SelectField(
        "Action",
        choices=[("approve", "Approve"), ("reject", "Reject")],
        validators=[DataRequired()],
    )
    transaction_ref = StringField(
        "Transaction Reference", validators=[Optional(), Length(max=100)]
    )
    rejection_reason = StringField(
        "Rejection Reason", validators=[Optional(), Length(max=300)]
    )
    submit = SubmitField("Submit")


class BanUserForm(FlaskForm):
    ban_reason = StringField("Ban Reason", validators=[DataRequired(), Length(max=300)])
    submit = SubmitField("Confirm Ban")
