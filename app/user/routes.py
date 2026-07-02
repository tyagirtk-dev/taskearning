"""
app/user/routes.py – All user-facing dashboard routes.
"""

from datetime import datetime
from flask import (
    render_template, redirect, url_for, flash, request, current_app, abort
)
from flask_login import login_required, current_user

from app import db
from app.models import (
    Task, TaskSubmission, WalletTransaction, WithdrawalRequest, User
)
from app.utils.helpers import save_image, delete_file, paginate_query
from .forms import ProfileForm, ChangePasswordForm, TaskSubmissionForm, WithdrawalForm
from . import user_bp


# ─────────────────────────────────────────────────────────────────────────────
#  Dashboard
# ─────────────────────────────────────────────────────────────────────────────

@user_bp.route("/")
@login_required
def dashboard():
    recent_submissions = (
        TaskSubmission.query
        .filter_by(user_id=current_user.id)
        .order_by(TaskSubmission.submitted_at.desc())
        .limit(5)
        .all()
    )
    recent_transactions = (
        WalletTransaction.query
        .filter_by(user_id=current_user.id)
        .order_by(WalletTransaction.created_at.desc())
        .limit(5)
        .all()
    )
    available_tasks = Task.query.filter_by(is_active=True).count()
    return render_template(
        "user/dashboard.html",
        recent_submissions=recent_submissions,
        recent_transactions=recent_transactions,
        available_tasks=available_tasks,
    )


# ─────────────────────────────────────────────────────────────────────────────
#  Profile
# ─────────────────────────────────────────────────────────────────────────────

@user_bp.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    form = ProfileForm(obj=current_user)
    if form.validate_on_submit():
        # Handle profile picture upload
        if form.profile_pic.data and hasattr(form.profile_pic.data, "filename"):
            old_pic = current_user.profile_pic
            filename = save_image(form.profile_pic.data, "profiles", max_size=(300, 300))
            current_user.profile_pic = filename
            delete_file("profiles", old_pic)

        current_user.name = form.name.data.strip()
        current_user.phone = form.phone.data.strip() if form.phone.data else None
        current_user.bio = form.bio.data.strip() if form.bio.data else None
        db.session.commit()
        flash("Profile updated successfully.", "success")
        return redirect(url_for("user.profile"))

    return render_template("user/profile.html", form=form)


@user_bp.route("/change-password", methods=["GET", "POST"])
@login_required
def change_password():
    form = ChangePasswordForm()
    if form.validate_on_submit():
        if not current_user.check_password(form.current_password.data):
            flash("Current password is incorrect.", "danger")
            return render_template("user/change_password.html", form=form)
        current_user.set_password(form.new_password.data)
        db.session.commit()
        flash("Password changed successfully.", "success")
        return redirect(url_for("user.profile"))
    return render_template("user/change_password.html", form=form)


# ─────────────────────────────────────────────────────────────────────────────
#  Tasks
# ─────────────────────────────────────────────────────────────────────────────

@user_bp.route("/tasks")
@login_required
def tasks():
    category = request.args.get("category", "")
    page = request.args.get("page", 1, type=int)

    query = Task.query.filter_by(is_active=True)
    if category:
        query = query.filter_by(category=category)
    query = query.order_by(Task.created_at.desc())

    pagination = paginate_query(query, page, per_page=12)
    tasks_list = pagination.items

    # Which tasks the current user has already submitted
    submitted_ids = {
        s.task_id for s in TaskSubmission.query.filter_by(user_id=current_user.id).all()
    }

    categories = db.session.query(Task.category).distinct().all()
    categories = [c[0] for c in categories]

    return render_template(
        "user/tasks.html",
        tasks=tasks_list,
        pagination=pagination,
        submitted_ids=submitted_ids,
        categories=categories,
        current_category=category,
    )


@user_bp.route("/tasks/<int:task_id>", methods=["GET", "POST"])
@login_required
def task_detail(task_id):
    task = Task.query.get_or_404(task_id)
    if not task.is_active:
        abort(404)

    existing = TaskSubmission.query.filter_by(
        user_id=current_user.id, task_id=task_id
    ).first()

    form = TaskSubmissionForm()
    if form.validate_on_submit():
        if existing:
            flash("You have already submitted this task.", "warning")
            return redirect(url_for("user.task_detail", task_id=task_id))

        screenshot_filename = None
        if form.proof_screenshot.data and hasattr(form.proof_screenshot.data, "filename"):
            screenshot_filename = save_image(
                form.proof_screenshot.data, "proofs", max_size=(1920, 1080)
            )
        elif task.requires_proof:
            flash("A proof screenshot is required for this task.", "danger")
            return render_template("user/task_detail.html", task=task, form=form, existing=existing)

        submission = TaskSubmission(
            user_id=current_user.id,
            task_id=task_id,
            proof_screenshot=screenshot_filename,
            proof_text=form.proof_text.data,
        )
        db.session.add(submission)
        db.session.commit()
        flash("Task submitted successfully! Awaiting admin review.", "success")
        return redirect(url_for("user.my_submissions"))

    return render_template("user/task_detail.html", task=task, form=form, existing=existing)


@user_bp.route("/submissions")
@login_required
def my_submissions():
    page = request.args.get("page", 1, type=int)
    status = request.args.get("status", "")
    query = TaskSubmission.query.filter_by(user_id=current_user.id)
    if status:
        query = query.filter_by(status=status)
    query = query.order_by(TaskSubmission.submitted_at.desc())
    pagination = paginate_query(query, page)
    return render_template(
        "user/submissions.html",
        submissions=pagination.items,
        pagination=pagination,
        current_status=status,
    )


# ─────────────────────────────────────────────────────────────────────────────
#  Wallet
# ─────────────────────────────────────────────────────────────────────────────

@user_bp.route("/wallet")
@login_required
def wallet():
    page = request.args.get("page", 1, type=int)
    transactions = (
        WalletTransaction.query
        .filter_by(user_id=current_user.id)
        .order_by(WalletTransaction.created_at.desc())
    )
    pagination = paginate_query(transactions, page)
    return render_template(
        "user/wallet.html",
        transactions=pagination.items,
        pagination=pagination,
    )


# ─────────────────────────────────────────────────────────────────────────────
#  Withdrawals
# ─────────────────────────────────────────────────────────────────────────────

@user_bp.route("/withdraw", methods=["GET", "POST"])
@login_required
def withdraw():
    form = WithdrawalForm()
    min_wd = current_app.config["MIN_WITHDRAWAL"]
    max_wd = current_app.config["MAX_WITHDRAWAL"]

    if form.validate_on_submit():
        amount = form.amount.data
        if amount < min_wd:
            flash(f"Minimum withdrawal is ₹{min_wd:.0f}.", "danger")
        elif amount > max_wd:
            flash(f"Maximum withdrawal is ₹{max_wd:.0f}.", "danger")
        elif amount > current_user.wallet_balance:
            flash("Insufficient wallet balance.", "danger")
        else:
            # Deduct balance immediately; reversal on rejection
            current_user.wallet_balance -= amount

            wd = WithdrawalRequest(
                user_id=current_user.id,
                amount=amount,
                upi_id=form.upi_id.data.strip(),
            )
            db.session.add(wd)
            db.session.flush()

            tx = WalletTransaction(
                user_id=current_user.id,
                amount=-amount,
                transaction_type="withdrawal",
                description=f"Withdrawal request #{wd.id}",
                balance_after=current_user.wallet_balance,
                reference_id=str(wd.id),
            )
            db.session.add(tx)
            db.session.commit()

            flash("Withdrawal request submitted successfully!", "success")
            return redirect(url_for("user.withdrawal_history"))

    return render_template(
        "user/withdraw.html",
        form=form,
        min_wd=min_wd,
        max_wd=max_wd,
    )


@user_bp.route("/withdrawals")
@login_required
def withdrawal_history():
    page = request.args.get("page", 1, type=int)
    withdrawals = (
        WithdrawalRequest.query
        .filter_by(user_id=current_user.id)
        .order_by(WithdrawalRequest.requested_at.desc())
    )
    pagination = paginate_query(withdrawals, page)
    return render_template(
        "user/withdrawal_history.html",
        withdrawals=pagination.items,
        pagination=pagination,
    )


# ─────────────────────────────────────────────────────────────────────────────
#  Referral
# ─────────────────────────────────────────────────────────────────────────────

@user_bp.route("/referral")
@login_required
def referral():
    referrals = (
        User.query
        .filter_by(referred_by_id=current_user.id)
        .order_by(User.created_at.desc())
        .all()
    )
    referral_earnings = (
        WalletTransaction.query
        .filter_by(user_id=current_user.id, transaction_type="referral_bonus")
        .all()
    )
    total_referral_earnings = sum(t.amount for t in referral_earnings)
    base_url = current_app.config["BASE_URL"]
    referral_link = f"{base_url}/auth/register?ref={current_user.referral_code}"
    return render_template(
        "user/referral.html",
        referrals=referrals,
        referral_link=referral_link,
        total_referral_earnings=total_referral_earnings,
    )
