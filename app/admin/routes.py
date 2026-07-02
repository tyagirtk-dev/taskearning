"""
app/admin/routes.py – Full admin panel: dashboard, user/task/submission/withdrawal management.
"""

from datetime import datetime
from functools import wraps
from flask import (
    render_template, redirect, url_for, flash, request, session, abort, current_app
)
from app import db
from app.models import (
    Admin, User, Task, TaskSubmission, WalletTransaction, WithdrawalRequest
)
from app.utils.helpers import save_image, delete_file, paginate_query
from app.utils.email import (
    send_task_approved_email, send_task_rejected_email,
    send_withdrawal_approved_email, send_withdrawal_rejected_email
)
from .forms import (
    AdminLoginForm, TaskForm, ReviewSubmissionForm,
    ReviewWithdrawalForm, BanUserForm
)
from . import admin_bp


# ─────────────────────────────────────────────────────────────────────────────
#  Auth guard
# ─────────────────────────────────────────────────────────────────────────────

def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get("admin_id"):
            flash("Please log in as admin.", "warning")
            return redirect(url_for("admin.login"))
        admin = Admin.query.get(session["admin_id"])
        if not admin or not admin.is_active:
            session.pop("admin_id", None)
            abort(403)
        return f(*args, **kwargs)
    return decorated


def get_current_admin():
    return Admin.query.get(session.get("admin_id"))


# ─────────────────────────────────────────────────────────────────────────────
#  Admin login / logout
# ─────────────────────────────────────────────────────────────────────────────

@admin_bp.route("/login", methods=["GET", "POST"])
def login():
    if session.get("admin_id"):
        return redirect(url_for("admin.dashboard"))

    form = AdminLoginForm()
    if form.validate_on_submit():
        admin = Admin.query.filter_by(email=form.email.data.lower()).first()
        if not admin or not admin.check_password(form.password.data):
            flash("Invalid credentials.", "danger")
            return render_template("admin/login.html", form=form)
        if not admin.is_active:
            flash("Your admin account is disabled.", "danger")
            return render_template("admin/login.html", form=form)

        session["admin_id"] = admin.id
        session.permanent = True
        admin.last_login = datetime.utcnow()
        db.session.commit()
        flash(f"Welcome back, {admin.name}!", "success")
        return redirect(url_for("admin.dashboard"))

    return render_template("admin/login.html", form=form)


@admin_bp.route("/logout")
def logout():
    session.pop("admin_id", None)
    flash("Logged out from admin panel.", "info")
    return redirect(url_for("admin.login"))


# ─────────────────────────────────────────────────────────────────────────────
#  Dashboard
# ─────────────────────────────────────────────────────────────────────────────

@admin_bp.route("/")
@admin_required
def dashboard():
    stats = {
        "total_users": User.query.count(),
        "verified_users": User.query.filter_by(is_email_verified=True).count(),
        "total_tasks": Task.query.count(),
        "active_tasks": Task.query.filter_by(is_active=True).count(),
        "pending_submissions": TaskSubmission.query.filter_by(status="pending").count(),
        "approved_submissions": TaskSubmission.query.filter_by(status="approved").count(),
        "pending_withdrawals": WithdrawalRequest.query.filter_by(status="pending").count(),
        "total_payout": db.session.query(
            db.func.sum(WithdrawalRequest.amount)
        ).filter_by(status="approved").scalar() or 0.0,
    }
    recent_users = User.query.order_by(User.created_at.desc()).limit(5).all()
    recent_submissions = (
        TaskSubmission.query
        .filter_by(status="pending")
        .order_by(TaskSubmission.submitted_at.desc())
        .limit(5)
        .all()
    )
    return render_template(
        "admin/dashboard.html",
        stats=stats,
        recent_users=recent_users,
        recent_submissions=recent_submissions,
        admin=get_current_admin(),
    )


# ─────────────────────────────────────────────────────────────────────────────
#  User Management
# ─────────────────────────────────────────────────────────────────────────────

@admin_bp.route("/users")
@admin_required
def users():
    page = request.args.get("page", 1, type=int)
    q = request.args.get("q", "")
    query = User.query
    if q:
        like = f"%{q}%"
        query = query.filter(
            (User.name.ilike(like)) | (User.email.ilike(like))
        )
    query = query.order_by(User.created_at.desc())
    pagination = paginate_query(query, page)
    return render_template(
        "admin/users.html",
        users=pagination.items,
        pagination=pagination,
        q=q,
        admin=get_current_admin(),
    )


@admin_bp.route("/users/<int:user_id>")
@admin_required
def user_detail(user_id):
    user = User.query.get_or_404(user_id)
    submissions = (
        TaskSubmission.query
        .filter_by(user_id=user_id)
        .order_by(TaskSubmission.submitted_at.desc())
        .limit(20)
        .all()
    )
    transactions = (
        WalletTransaction.query
        .filter_by(user_id=user_id)
        .order_by(WalletTransaction.created_at.desc())
        .limit(20)
        .all()
    )
    return render_template(
        "admin/user_detail.html",
        user=user,
        submissions=submissions,
        transactions=transactions,
        admin=get_current_admin(),
    )


@admin_bp.route("/users/<int:user_id>/ban", methods=["POST"])
@admin_required
def ban_user(user_id):
    user = User.query.get_or_404(user_id)
    reason = request.form.get("ban_reason", "Violation of terms")
    user.is_banned = True
    user.ban_reason = reason
    db.session.commit()
    flash(f"User {user.name} has been banned.", "warning")
    return redirect(url_for("admin.user_detail", user_id=user_id))


@admin_bp.route("/users/<int:user_id>/unban", methods=["POST"])
@admin_required
def unban_user(user_id):
    user = User.query.get_or_404(user_id)
    user.is_banned = False
    user.ban_reason = None
    db.session.commit()
    flash(f"User {user.name} has been unbanned.", "success")
    return redirect(url_for("admin.user_detail", user_id=user_id))


@admin_bp.route("/users/<int:user_id>/verify", methods=["POST"])
@admin_required
def verify_user(user_id):
    user = User.query.get_or_404(user_id)
    user.is_email_verified = True
    db.session.commit()
    flash(f"User {user.name} manually verified.", "success")
    return redirect(url_for("admin.user_detail", user_id=user_id))


# ─────────────────────────────────────────────────────────────────────────────
#  Task Management
# ─────────────────────────────────────────────────────────────────────────────

@admin_bp.route("/tasks")
@admin_required
def tasks():
    page = request.args.get("page", 1, type=int)
    tasks_q = Task.query.order_by(Task.created_at.desc())
    pagination = paginate_query(tasks_q, page)
    return render_template(
        "admin/tasks.html",
        tasks=pagination.items,
        pagination=pagination,
        admin=get_current_admin(),
    )


@admin_bp.route("/tasks/new", methods=["GET", "POST"])
@admin_required
def task_create():
    form = TaskForm()
    if form.validate_on_submit():
        thumbnail = None
        if form.thumbnail.data:
            thumbnail = save_image(form.thumbnail.data, "proofs", max_size=(800, 450))

        task = Task(
            title=form.title.data,
            description=form.description.data,
            instructions=form.instructions.data,
            category=form.category.data,
            reward=form.reward.data,
            time_limit_hours=form.time_limit_hours.data,
            max_submissions=form.max_submissions.data,
            external_url=form.external_url.data or None,
            thumbnail=thumbnail,
            requires_proof=form.requires_proof.data,
            is_active=form.is_active.data,
            created_by_id=session["admin_id"],
        )
        db.session.add(task)
        db.session.commit()
        flash("Task created successfully.", "success")
        return redirect(url_for("admin.tasks"))

    return render_template("admin/task_form.html", form=form, title="Create Task", admin=get_current_admin())


@admin_bp.route("/tasks/<int:task_id>/edit", methods=["GET", "POST"])
@admin_required
def task_edit(task_id):
    task = Task.query.get_or_404(task_id)
    form = TaskForm(obj=task)
    if form.validate_on_submit():
        if form.thumbnail.data:
            delete_file("proofs", task.thumbnail)
            task.thumbnail = save_image(form.thumbnail.data, "proofs", max_size=(800, 450))

        task.title = form.title.data
        task.description = form.description.data
        task.instructions = form.instructions.data
        task.category = form.category.data
        task.reward = form.reward.data
        task.time_limit_hours = form.time_limit_hours.data
        task.max_submissions = form.max_submissions.data
        task.external_url = form.external_url.data or None
        task.requires_proof = form.requires_proof.data
        task.is_active = form.is_active.data
        db.session.commit()
        flash("Task updated successfully.", "success")
        return redirect(url_for("admin.tasks"))

    return render_template("admin/task_form.html", form=form, task=task, title="Edit Task", admin=get_current_admin())


@admin_bp.route("/tasks/<int:task_id>/delete", methods=["POST"])
@admin_required
def task_delete(task_id):
    task = Task.query.get_or_404(task_id)
    delete_file("proofs", task.thumbnail)
    db.session.delete(task)
    db.session.commit()
    flash("Task deleted.", "info")
    return redirect(url_for("admin.tasks"))


@admin_bp.route("/tasks/<int:task_id>/toggle", methods=["POST"])
@admin_required
def task_toggle(task_id):
    task = Task.query.get_or_404(task_id)
    task.is_active = not task.is_active
    db.session.commit()
    state = "activated" if task.is_active else "deactivated"
    flash(f"Task {state}.", "info")
    return redirect(url_for("admin.tasks"))


# ─────────────────────────────────────────────────────────────────────────────
#  Submission Management
# ─────────────────────────────────────────────────────────────────────────────

@admin_bp.route("/submissions")
@admin_required
def submissions():
    page = request.args.get("page", 1, type=int)
    status = request.args.get("status", "pending")
    query = TaskSubmission.query
    if status:
        query = query.filter_by(status=status)
    query = query.order_by(TaskSubmission.submitted_at.desc())
    pagination = paginate_query(query, page)
    return render_template(
        "admin/submissions.html",
        submissions=pagination.items,
        pagination=pagination,
        current_status=status,
        admin=get_current_admin(),
    )


@admin_bp.route("/submissions/<int:sub_id>", methods=["GET", "POST"])
@admin_required
def review_submission(sub_id):
    sub = TaskSubmission.query.get_or_404(sub_id)
    form = ReviewSubmissionForm()

    if form.validate_on_submit():
        action = form.action.data
        if action == "approve":
            sub.status = "approved"
            sub.reward_paid = sub.task.reward
            sub.reviewed_at = datetime.utcnow()
            sub.reviewed_by_id = session["admin_id"]

            # Credit wallet
            user = sub.user
            user.wallet_balance += sub.task.reward
            user.total_earned += sub.task.reward

            tx = WalletTransaction(
                user_id=user.id,
                amount=sub.task.reward,
                transaction_type="task_reward",
                description=f"Task approved: {sub.task.title}",
                balance_after=user.wallet_balance,
                reference_id=str(sub.id),
            )
            db.session.add(tx)

            # Referral bonus (only on first approved task)
            _maybe_award_referral_bonus(user)

            db.session.commit()
            send_task_approved_email(user, sub)
            flash("Submission approved and wallet credited.", "success")

        elif action == "reject":
            reason = form.rejection_reason.data
            if not reason:
                flash("Please provide a rejection reason.", "danger")
                return render_template(
                    "admin/review_submission.html", sub=sub, form=form, admin=get_current_admin()
                )
            sub.status = "rejected"
            sub.rejection_reason = reason
            sub.reviewed_at = datetime.utcnow()
            sub.reviewed_by_id = session["admin_id"]
            db.session.commit()
            send_task_rejected_email(sub.user, sub)
            flash("Submission rejected.", "warning")

        return redirect(url_for("admin.submissions"))

    return render_template(
        "admin/review_submission.html", sub=sub, form=form, admin=get_current_admin()
    )


def _maybe_award_referral_bonus(user: User) -> None:
    """Award referral bonus to the referrer on user's first approved task."""
    if not current_app.config.get("REFERRAL_BONUS_ON_FIRST_TASK"):
        return
    if not user.referred_by_id:
        return
    already_awarded = WalletTransaction.query.filter_by(
        user_id=user.referred_by_id,
        transaction_type="referral_bonus",
        reference_id=f"ref_{user.id}",
    ).first()
    if already_awarded:
        return
    first_approval = TaskSubmission.query.filter_by(
        user_id=user.id, status="approved"
    ).count()
    if first_approval != 1:
        return

    referrer = User.query.get(user.referred_by_id)
    if not referrer:
        return
    bonus = current_app.config["REFERRAL_BONUS"]
    referrer.wallet_balance += bonus
    referrer.total_earned += bonus
    tx = WalletTransaction(
        user_id=referrer.id,
        amount=bonus,
        transaction_type="referral_bonus",
        description=f"Referral bonus for {user.name} completing their first task",
        balance_after=referrer.wallet_balance,
        reference_id=f"ref_{user.id}",
    )
    db.session.add(tx)


# ─────────────────────────────────────────────────────────────────────────────
#  Withdrawal Management
# ─────────────────────────────────────────────────────────────────────────────

@admin_bp.route("/withdrawals")
@admin_required
def withdrawals():
    page = request.args.get("page", 1, type=int)
    status = request.args.get("status", "pending")
    query = WithdrawalRequest.query
    if status:
        query = query.filter_by(status=status)
    query = query.order_by(WithdrawalRequest.requested_at.desc())
    pagination = paginate_query(query, page)
    return render_template(
        "admin/withdrawals.html",
        withdrawals=pagination.items,
        pagination=pagination,
        current_status=status,
        admin=get_current_admin(),
    )


@admin_bp.route("/withdrawals/<int:wd_id>/process", methods=["POST"])
@admin_required
def process_withdrawal(wd_id):
    wd = WithdrawalRequest.query.get_or_404(wd_id)
    if wd.status != "pending":
        flash("Withdrawal already processed.", "info")
        return redirect(url_for("admin.withdrawals"))

    action = request.form.get("action")
    wd.processed_at = datetime.utcnow()
    wd.processed_by_id = session["admin_id"]

    if action == "approve":
        wd.status = "approved"
        wd.transaction_ref = request.form.get("transaction_ref", "")
        db.session.commit()
        send_withdrawal_approved_email(wd.user, wd)
        flash("Withdrawal approved.", "success")
    elif action == "reject":
        wd.status = "rejected"
        wd.rejection_reason = request.form.get("rejection_reason", "")
        # Refund balance
        wd.user.wallet_balance += wd.amount
        tx = WalletTransaction(
            user_id=wd.user_id,
            amount=wd.amount,
            transaction_type="adjustment",
            description=f"Withdrawal #{wd.id} rejected – refund",
            balance_after=wd.user.wallet_balance,
            reference_id=str(wd.id),
        )
        db.session.add(tx)
        db.session.commit()
        send_withdrawal_rejected_email(wd.user, wd)
        flash("Withdrawal rejected and balance refunded.", "warning")

    return redirect(url_for("admin.withdrawals"))
