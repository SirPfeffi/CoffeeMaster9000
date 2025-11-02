import os
import datetime
from flask import Flask, render_template, redirect, url_for, request, flash
from models import User, Transaction, db  # dein bestehendes Peewee-Modell
from account_manager import AccountManager  # deine bestehende Logik


# Pfad zur SQLite-Datenbank
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "kaffeekasse.db")

# Verbindung herstellen
db.init(DB_PATH)
account_manager = AccountManager()  # nutzt automatisch dasselbe DB-Objekt

app = Flask(__name__)
app.secret_key = "dein_geheimes_schluesselwort"  # für Flash-Messages

account_manager = AccountManager()

# Startseite
@app.route("/")
def index():
    total_coffee = account_manager.get_total_coffee()
    return render_template("index.html", total_coffee=total_coffee)

# Benutzerliste
@app.route("/users")
def users():
    all_users = User.select()
    return render_template("users.html", users=all_users)

# Benutzer-Details + Guthaben bearbeiten
@app.route("/user/<int:user_id>", methods=["GET", "POST"])
def user_detail(user_id):
    user = User.get_by_id(user_id)
    if request.method == "POST":
        try:
            amount = float(request.form["amount"])
            account_manager.deposit(user, amount)
            flash(f"{amount:.2f} € eingezahlt für {user.name}", "success")
            return redirect(url_for("user_detail", user_id=user.id))
        except ValueError:
            flash("Ungültiger Betrag!", "danger")
    transactions = Transaction.select().where(Transaction.user == user).order_by(Transaction.timestamp.desc()).limit(10)
    return render_template("user_detail.html", user=user, transactions=transactions)

# Statistikseite
@app.route("/stats")
def stats():
    daily_counts = account_manager.get_daily_coffee_counts(days=7)
    total_coffee = account_manager.get_total_coffee()
    return render_template("stats.html", daily_counts=daily_counts, total_coffee=total_coffee)

# Backup starten
@app.route("/backup")
def backup():
    try:
        account_manager.perform_backup()
        flash("Backup erfolgreich erstellt!", "success")
    except Exception as e:
        flash(f"Backup fehlgeschlagen: {e}", "danger")
    return redirect(url_for("index"))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
