import sqlite3
from contextlib import contextmanager
from config import DATABASE_PATH


def init_db():
    with get_conn() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS sent_promos (
                product_id TEXT PRIMARY KEY,
                title TEXT,
                price REAL,
                sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)


@contextmanager
def get_conn():
    conn = sqlite3.connect(DATABASE_PATH)
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def already_sent(product_id: str) -> bool:
    with get_conn() as conn:
        cur = conn.execute(
            "SELECT 1 FROM sent_promos WHERE product_id = ?", (product_id,)
        )
        return cur.fetchone() is not None


def mark_as_sent(product_id: str, title: str, price: float):
    with get_conn() as conn:
        conn.execute(
            "INSERT OR IGNORE INTO sent_promos (product_id, title, price) VALUES (?, ?, ?)",
            (product_id, title, price),
        )
