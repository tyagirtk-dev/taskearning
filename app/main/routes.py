from flask import render_template, redirect, url_for
from flask_login import current_user
from app.models import Task, User
from . import main_bp


@main_bp.route("/")
def index():
    if current_user.is_authenticated:
        return redirect(url_for("user.dashboard"))
    task_count = Task.query.filter_by(is_active=True).count()
    user_count = User.query.filter_by(is_email_verified=True).count()
    featured_tasks = Task.query.filter_by(is_active=True).order_by(Task.reward.desc()).limit(3).all()
    return render_template("main/index.html", task_count=task_count,
                           user_count=user_count, featured_tasks=featured_tasks)
