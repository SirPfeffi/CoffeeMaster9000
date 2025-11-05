from flask import Flask, render_template, request, redirect, url_for, flash
from core.account_manager import AccountManager
from db.models import init_db, User
from decimal import Decimal, InvalidOperation
import os

app = Flask(__name__)
app.secret_key = os.environ.get("KAFFEEKASSE_SECRET", "UNSAFE_DEFAULT_KEY")

init_db()
am = AccountManager()

def parse_amount_to_cents(value: str) -> int:
    try:
        d = Decimal(value.replace(",", ".")).quantize(Decimal("0.01"))
        return int(d * 100)
    except InvalidOperation:
        raise ValueError("Ungültiger Betrag")

@app.route("/")
def index():
    users = User.select().order_by(User.name)
    return render_template("index.html", users=users)

@app.route("/deposit", methods=["POST"])
def deposit():
    uid = request.form.get("rfid_uid")
    amount = request.form.get("amount")
    user = am.get_user_by_uid(uid)
    if not user:
        flash("Unbekannter Benutzer.", "danger")
        return redirect(url_for("index"))
    try:
        am.deposit(user, amount)
        flash(f"Einzahlung von {amount} € erfolgreich!", "success")
    except ValueError as e:
        flash(str(e), "danger")
    return redirect(url_for("index"))

@app.route("/coffee/<uid>")
def book_coffee(uid):
    user = am.get_user_by_uid(uid)
    if not user:
        flash("Benutzer nicht gefunden.", "danger")
        return redirect(url_for("index"))
    try:
        am.book_coffee(user)
        flash(f"Kaffee gebucht für {user.name}.", "success")
    except ValueError as e:
        flash(str(e), "danger")
    return redirect(url_for("index"))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)