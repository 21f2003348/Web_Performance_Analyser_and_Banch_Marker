import sqlite3
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

DB_URL = "sqlite:///benchmark.db"

engine = create_engine(DB_URL)
Session = sessionmaker(bind=engine)

def setup_db():
    with engine.begin() as conn:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY,
                name TEXT
            )
        """))
        conn.execute(text("DELETE FROM users"))
        for i in range(1000):
            conn.execute(text("INSERT INTO users (name) VALUES (:n)"), {"n": f"user{i}"})


def fetch_orm(_):
    session = Session()
    result = session.execute(text("SELECT * FROM users")).fetchall()
    session.close()
    return result


def fetch_core(_):
    with engine.connect() as conn:
        return conn.execute(text("SELECT * FROM users")).fetchall()


def fetch_raw(_):
    conn = sqlite3.connect("benchmark.db")
    cur = conn.cursor()
    cur.execute("SELECT * FROM users")
    rows = cur.fetchall()
    conn.close()
    return rows
