from peewee import *
from datetime import datetime

db = SqliteDatabase("db/kaffeekasse.db")

class BaseModel(Model):
    class Meta:
        database = db

class User(BaseModel):
    rfid_uid = CharField(unique=True)
    name = CharField()
    balance = FloatField(default=0.0)

class Transaction(BaseModel):
    user = ForeignKeyField(User, backref='transactions')
    amount = FloatField()
    description = CharField()
    timestamp = DateTimeField(default=datetime.now)
