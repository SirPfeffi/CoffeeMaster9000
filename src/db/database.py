from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from db.models import Base, User

DB_PATH = "data/kaffeekasse.db"

def init_db():
    """Initialisiert die SQLite-Datenbank und erstellt ggf. Tabellen."""
    import os
    os.makedirs("data", exist_ok=True)
    engine = create_engine(f"sqlite:///{DB_PATH}")
    Base.metadata.create_all(engine)
    return engine

def get_session():
    """Erstellt eine neue DB-Session."""
    engine = create_engine(f"sqlite:///{DB_PATH}")
    Session = sessionmaker(bind=engine)
    return Session()

# Initial-Admin anlegen, falls DB leer ist
def create_default_admin():
    session = get_session()
    if not session.query(User).first():
        admin = User(name="Admin", rfid_uid="00000000", balance=0.0, is_admin=True)
        session.add(admin)
        session.commit()
        print("[DB] Standard-Admin angelegt (UID=00000000)")
    session.close()
