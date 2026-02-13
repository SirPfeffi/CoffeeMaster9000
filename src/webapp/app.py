import os
from functools import wraps
from datetime import datetime, timedelta

from flask import Flask, Response, flash, redirect, render_template, request, session, url_for

from core.account_manager import AccountManager
from core.auth_manager import AuthManager
from core.backup_manager import BackupManager
from core.i18n import DEFAULT_LANG, SUPPORTED_LANGS, translate
from core.machine_sync_manager import MachineSyncManager
from core.reporting_manager import ReportingManager
from db.models import AdminUser, DB_PATH, BackupRun, MachineEvent, Transaction, User, init_db
from peewee import fn

app = Flask(__name__)
app.secret_key = os.environ.get("KAFFEEKASSE_SECRET")
if not app.secret_key:
    raise RuntimeError("KAFFEEKASSE_SECRET must be set")

init_db()
am = AccountManager()
auth = AuthManager()
reporting = ReportingManager()
machine_sync = MachineSyncManager.from_env()


def _build_backup_manager() -> BackupManager:
    db_path = os.environ.get("COFFEEMASTER_DB_PATH", DB_PATH)
    usb_path = os.environ.get("COFFEEMASTER_USB_BACKUP_PATH", "/media/usb")
    network_path = os.environ.get("COFFEEMASTER_NETWORK_BACKUP_PATH")
    max_retries = int(os.environ.get("COFFEEMASTER_BACKUP_MAX_RETRIES", "10"))
    return BackupManager(
        db_path=db_path,
        usb_path=usb_path,
        network_path=network_path,
        max_retries=max_retries,
    )


def _current_lang() -> str:
    code = session.get("lang", DEFAULT_LANG)
    return code if code in SUPPORTED_LANGS else DEFAULT_LANG


def _msg(key: str, fallback: str = None, **kwargs) -> str:
    text = translate(key, _current_lang(), fallback=fallback or key)
    if kwargs:
        try:
            return text.format(**kwargs)
        except Exception:
            return text
    return text


def _is_admin_logged_in() -> bool:
    return bool(session.get("admin_user"))


@app.context_processor
def inject_i18n():
    lang = _current_lang()
    return {
        "lang": lang,
        "tr": lambda key, fallback=None: translate(key, lang, fallback=fallback),
    }


def admin_required(view_func):
    @wraps(view_func)
    def wrapper(*args, **kwargs):
        if not _is_admin_logged_in():
            flash(_msg("flash.auth_required"), "danger")
            return redirect(url_for("login"))
        return view_func(*args, **kwargs)

    return wrapper


def _ensure_bootstrap_admin():
    bootstrap_user = os.environ.get("COFFEEMASTER_BOOTSTRAP_ADMIN")
    bootstrap_password = os.environ.get("COFFEEMASTER_BOOTSTRAP_PASSWORD")
    if bootstrap_user and bootstrap_password and not AdminUser.select().exists():
        auth.create_admin(bootstrap_user, bootstrap_password)


_ensure_bootstrap_admin()


@app.route("/lang/<code>")
def switch_lang(code: str):
    session["lang"] = code if code in SUPPORTED_LANGS else DEFAULT_LANG
    return redirect(request.referrer or url_for("index"))


@app.route("/")
def index():
    users = User.select().where(User.is_active == True).order_by(User.name)
    total_coffees = (
        Transaction.select()
        .where(Transaction.kind == "coffee")
        .count()
    )
    return render_template(
        "index.html",
        users=users,
        total_coffee=total_coffees,
        is_admin=_is_admin_logged_in(),
    )


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "")
        password = request.form.get("password", "")
        admin = auth.verify_admin(username, password)
        if not admin:
            flash(_msg("flash.invalid_credentials"), "danger")
            return render_template("login.html", is_admin=_is_admin_logged_in())
        session["admin_user"] = admin.username
        flash(_msg("flash.login_success"), "success")
        return redirect(url_for("users"))
    return render_template("login.html", is_admin=_is_admin_logged_in())


@app.route("/logout")
def logout():
    session.pop("admin_user", None)
    flash(_msg("flash.logout_success"), "success")
    return redirect(url_for("index"))


@app.route("/users")
@admin_required
def users():
    all_users = User.select().where(User.is_active == True).order_by(User.name)
    return render_template("users.html", users=all_users, is_admin=True)


@app.route("/users/<int:user_id>", methods=["GET", "POST"])
@admin_required
def user_detail(user_id: int):
    user = User.get_or_none(User.id == user_id)
    if not user:
        flash(_msg("flash.user_not_found"), "danger")
        return redirect(url_for("users"))

    if request.method == "POST":
        action = request.form.get("action", "")
        try:
            if action == "deposit":
                amount = request.form.get("amount", "")
                am.deposit(user, amount)
                flash(_msg("flash.deposit_success"), "success")
            elif action == "beans_topup":
                kg = int(request.form.get("kg", "0"))
                amount = request.form.get("amount", "")
                am.topup_by_beans(user, kg=kg, amount_euro=amount)
                flash(_msg("flash.beans_topup_success"), "success")
            elif action == "correction":
                amount = request.form.get("amount", "")
                reason = request.form.get("reason", "")
                am.add_correction(user, amount_euro=amount, reason=reason)
                flash(_msg("flash.correction_success"), "success")
            elif action == "maintenance":
                amount = request.form.get("amount", "")
                reason = request.form.get("reason", "")
                am.add_maintenance_entry(user, amount_euro=amount, reason=reason, affects_balance=False)
                flash(_msg("flash.maintenance_success"), "success")
            else:
                flash(_msg("flash.unsupported_action"), "danger")
        except (ValueError, PermissionError) as exc:
            flash(str(exc), "danger")
        return redirect(url_for("user_detail", user_id=user.id))

    transactions = am.get_user_transactions(user, limit=100)
    return render_template("users_detail.html", user=user, transactions=transactions, is_admin=True)


@app.route("/stats")
@admin_required
def stats():
    total_coffees = Transaction.select().where(Transaction.kind == "coffee").count()
    payload = reporting.stats_payload()
    return render_template("stats.html", total_coffee=total_coffees, stats=payload, is_admin=True)


@app.route("/stats/export.csv")
@admin_required
def stats_export():
    csv_content = reporting.export_transactions_csv()
    return Response(
        csv_content,
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=coffeemaster_transactions.csv"},
    )


@app.route("/backup")
@admin_required
def backup():
    manager = _build_backup_manager()
    files = manager.list_backup_files()
    runs = manager.recent_runs(limit=30)

    last_success = (
        BackupRun.select()
        .where(BackupRun.status == "success")
        .order_by(BackupRun.created_at.desc())
        .first()
    )
    no_success_24h = True
    if last_success:
        delta = datetime.now() - last_success.created_at
        no_success_24h = delta.total_seconds() > 86400

    return render_template(
        "backup.html",
        is_admin=True,
        backup_files=files,
        backup_runs=runs,
        no_success_24h=no_success_24h,
    )


@app.route("/backup/run", methods=["POST"])
@admin_required
def backup_run():
    manager = _build_backup_manager()
    results = manager.backup_all()
    flash(_msg("flash.backup_triggered", results=results), "success")
    return redirect(url_for("backup"))


@app.route("/backup/preview", methods=["POST"])
@admin_required
def backup_preview():
    manager = _build_backup_manager()
    path = request.form.get("backup_path", "").strip()
    try:
        preview = manager.preview_restore(path)
    except Exception as exc:
        flash(str(exc), "danger")
        return redirect(url_for("backup"))

    files = manager.list_backup_files()
    runs = manager.recent_runs(limit=30)
    last_success = (
        BackupRun.select()
        .where(BackupRun.status == "success")
        .order_by(BackupRun.created_at.desc())
        .first()
    )
    no_success_24h = True
    if last_success:
        no_success_24h = (datetime.now() - last_success.created_at).total_seconds() > 86400
    return render_template(
        "backup.html",
        is_admin=True,
        backup_files=files,
        backup_runs=runs,
        restore_preview=preview,
        no_success_24h=no_success_24h,
    )


@app.route("/backup/restore", methods=["POST"])
@admin_required
def backup_restore():
    manager = _build_backup_manager()
    path = request.form.get("backup_path", "").strip()
    confirm = request.form.get("confirm_restore", "") == "yes"
    if not confirm:
        flash(_msg("flash.restore_confirm_missing"), "danger")
        return redirect(url_for("backup"))
    try:
        result = manager.restore_from_backup(path)
        flash(_msg("flash.restore_success", result=result), "success")
    except Exception as exc:
        flash(str(exc), "danger")
    return redirect(url_for("backup"))


@app.route("/integrations")
@admin_required
def integrations():
    from_time = datetime.now() - timedelta(hours=24)
    brewed_24h = (
        MachineEvent.select(fn.SUM(MachineEvent.count))
        .where(
            (MachineEvent.source == "we8")
            & (MachineEvent.event_type == "coffee_brewed")
            & (MachineEvent.created_at >= from_time)
        )
        .scalar()
        or 0
    )
    booked_24h = (
        Transaction.select(fn.SUM(Transaction.coffee_count))
        .where((Transaction.kind == "coffee") & (Transaction.timestamp >= from_time))
        .scalar()
        or 0
    )
    return render_template(
        "integrations.html",
        is_admin=True,
        we8_status=machine_sync.status(),
        we8_brewed_24h=brewed_24h,
        booked_24h=booked_24h,
        delta_24h=brewed_24h - booked_24h,
    )


@app.route("/integrations/we8/poll", methods=["POST"])
@admin_required
def integrations_we8_poll():
    events = machine_sync.poll_once()
    if events:
        flash(_msg("flash.we8_events_detected", count=len(events)), "success")
    else:
        flash(_msg("flash.we8_no_events"), "success")
    return redirect(url_for("integrations"))


@app.route("/coffee/<uid>")
def book_coffee(uid):
    user = am.get_user_by_uid(uid)
    if not user:
        flash(_msg("flash.user_not_found"), "danger")
        return redirect(url_for("index"))
    try:
        am.book_coffee(user)
        flash(_msg("flash.coffee_booked", name=user.name), "success")
    except ValueError as exc:
        flash(str(exc), "danger")
    return redirect(url_for("index"))


@app.route("/deposit", methods=["POST"])
def deposit():
    uid = request.form.get("rfid_uid")
    amount = request.form.get("amount")
    user = am.get_user_by_uid(uid)
    if not user:
        flash(_msg("flash.unknown_user"), "danger")
        return redirect(url_for("index"))
    try:
        am.deposit(user, amount)
        flash(_msg("flash.deposit_amount_success", amount=amount), "success")
    except ValueError as exc:
        flash(str(exc), "danger")
    return redirect(url_for("index"))


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
