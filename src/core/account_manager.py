from db.models import User, Transaction
from datetime import datetime
from peewee import SqliteDatabase

class AccountManager:
    def __init__(self, db_path="db/kaffeekasse.db"):
        self.db = SqliteDatabase(db_path)
        self.db.connect()
        self.db.create_tables([User, Transaction], safe=True)

    def get_user_by_uid(self, uid):
        try:
            return User.get(User.rfid_uid == uid)
        except User.DoesNotExist:
            return None

    def create_user(self, uid, name="Neuer Nutzer"):
        return User.create(rfid_uid=uid, name=name, balance=0.0)

    def book_coffee(self, user, amount=0.17):
        if user.balance >= amount:
            user.balance -= amount
            user.save()
            Transaction.create(user=user, amount=-amount, description="Kaffee")
            return True
        return False

    def deposit(self, user, amount):
        user.balance += amount
        user.save()
        Transaction.create(user=user, amount=amount, description="Einzahlung")
        return user.balance

    def get_last_transactions(self, user, limit=10):
        return Transaction.select().where(Transaction.user == user).order_by(Transaction.timestamp.desc()).limit(limit)

    def get_total_coffee(self):
        return Transaction.select().where(Transaction.description=="Kaffee").count()

    def get_daily_coffee_counts(self, days=7):
        from datetime import timedelta, datetime
        result = {}
        today = datetime.now().date()
        for i in range(days):
            day = today - timedelta(days=i)
            count = Transaction.select().where(
                (Transaction.description=="Kaffee") &
                (Transaction.timestamp.date()==day)
            ).count()
            result[day.strftime("%d.%m.%Y")] = count
        return dict(sorted(result.items()))
