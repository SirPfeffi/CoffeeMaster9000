from datetime import datetime, timedelta
import csv
import io

from peewee import fn

from db.models import Transaction, User


class ReportingManager:
    def _period_start(self, period: str):
        now = datetime.now()
        if period == "week":
            return now - timedelta(days=7)
        if period == "month":
            return now - timedelta(days=30)
        if period == "year":
            return now - timedelta(days=365)
        return None

    def top_consumers(self, period: str = "overall", limit: int = 3):
        query = (
            Transaction.select(
                User.name.alias("name"),
                fn.SUM(Transaction.coffee_count).alias("coffee_total"),
            )
            .join(User)
            .where(Transaction.kind == "coffee")
            .group_by(User.id)
            .order_by(fn.SUM(Transaction.coffee_count).desc())
            .limit(limit)
        )
        start = self._period_start(period)
        if start:
            query = query.where(Transaction.timestamp >= start)
        return list(query.dicts())

    def debtor_list(self, limit: int = 10):
        query = (
            User.select(User.name, User.balance_cents)
            .where(User.is_active == True)
            .order_by(User.balance_cents.asc())
            .limit(limit)
        )
        return list(query.dicts())

    def kilograms_bought(self, period: str = "overall"):
        query = Transaction.select(fn.SUM(Transaction.kg_bought)).where(Transaction.kind == "topup_beans")
        start = self._period_start(period)
        if start:
            query = query.where(Transaction.timestamp >= start)
        return query.scalar() or 0

    def maintenance_cost_cents(self, period: str = "overall"):
        query = Transaction.select(fn.SUM(Transaction.amount_cents)).where(Transaction.kind == "maintenance")
        start = self._period_start(period)
        if start:
            query = query.where(Transaction.timestamp >= start)
        value = query.scalar() or 0
        return value

    def consumption_by_hour(self):
        query = (
            Transaction.select(
                fn.strftime("%H", Transaction.timestamp).alias("hour"),
                fn.SUM(Transaction.coffee_count).alias("total"),
            )
            .where(Transaction.kind == "coffee")
            .group_by(fn.strftime("%H", Transaction.timestamp))
            .order_by(fn.strftime("%H", Transaction.timestamp))
        )
        return list(query.dicts())

    def consumption_by_weekday(self):
        query = (
            Transaction.select(
                fn.strftime("%w", Transaction.timestamp).alias("weekday"),
                fn.SUM(Transaction.coffee_count).alias("total"),
            )
            .where(Transaction.kind == "coffee")
            .group_by(fn.strftime("%w", Transaction.timestamp))
            .order_by(fn.strftime("%w", Transaction.timestamp))
        )
        return list(query.dicts())

    def consumption_by_month(self):
        query = (
            Transaction.select(
                fn.strftime("%Y-%m", Transaction.timestamp).alias("month"),
                fn.SUM(Transaction.coffee_count).alias("total"),
            )
            .where(Transaction.kind == "coffee")
            .group_by(fn.strftime("%Y-%m", Transaction.timestamp))
            .order_by(fn.strftime("%Y-%m", Transaction.timestamp))
        )
        return list(query.dicts())

    def stats_payload(self):
        return {
            "top_week": self.top_consumers("week"),
            "top_month": self.top_consumers("month"),
            "top_year": self.top_consumers("year"),
            "top_overall": self.top_consumers("overall"),
            "debtors": self.debtor_list(),
            "kg_week": self.kilograms_bought("week"),
            "kg_month": self.kilograms_bought("month"),
            "kg_year": self.kilograms_bought("year"),
            "kg_overall": self.kilograms_bought("overall"),
            "maintenance_month_cents": self.maintenance_cost_cents("month"),
            "maintenance_year_cents": self.maintenance_cost_cents("year"),
            "maintenance_overall_cents": self.maintenance_cost_cents("overall"),
            "hourly": self.consumption_by_hour(),
            "weekday": self.consumption_by_weekday(),
            "monthly": self.consumption_by_month(),
        }

    def export_transactions_csv(self):
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(
            [
                "timestamp",
                "user",
                "kind",
                "description",
                "amount_cents",
                "coffee_count",
                "kg_bought",
                "reference",
            ]
        )
        rows = (
            Transaction.select(Transaction, User.name)
            .join(User)
            .order_by(Transaction.timestamp.desc())
            .limit(5000)
        )
        for tx in rows:
            writer.writerow(
                [
                    tx.timestamp.isoformat(),
                    tx.user.name,
                    tx.kind,
                    tx.description,
                    tx.amount_cents,
                    tx.coffee_count,
                    tx.kg_bought or "",
                    tx.reference or "",
                ]
            )
        return output.getvalue()
