
import sqlite3
from contextlib import closing

DB_NAME = "data.db"

def init_db():
    with closing(sqlite3.connect(DB_NAME)) as conn:
        with conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY,
                    username TEXT,
                    points INTEGER DEFAULT 2,
                    referrals INTEGER DEFAULT 0,
                    ref_by INTEGER
                )
            """)

def user_exists(user_id):
    with closing(sqlite3.connect(DB_NAME)) as conn:
        cur = conn.execute("SELECT 1 FROM users WHERE id = ?", (user_id,))
        return cur.fetchone() is not None

def save_user(user_id, username, points=2, referrals=0, ref_by=None):
    with closing(sqlite3.connect(DB_name)) as conn:
        with conn:
            conn.execute(
                "INSERT OR IGNORE INTO users (id, username, points, referrals, ref_by) VALUES (?, ?, ?, ?, ?)",
                (user_id, username, points, referrals, ref_by)
            )

def get_user_data(user_id):
    with closing(sqlite3.connect(DB_NAME)) as conn:
        cur = conn.execute("SELECT id, username, points, referrals, ref_by FROM users WHERE id = ?", (user_id,))
        row = cur.fetchone()
        if row:
            return {
                "id": row[0],
                "username": row[1],
                "points": row[2],
                "referrals": row[3],
                "ref_by": row[4]
            }
        return None

def update_user_points(user_id, new_points):
    with closing(sqlite3.connect(DB_NAME)) as conn:
        with conn:
            conn.execute("UPDATE users SET points = ? WHERE id = ?", (new_points, user_id))

def add_points(user_id, amount):
    with closing(sqlite3.connect(DB_NAME)) as conn:
        with conn:
            conn.execute("UPDATE users SET points = points + ? WHERE id = ?", (amount, user_id))

def increment_referrals(user_id):
    with closing(sqlite3.connect(DB_NAME)) as conn:
        with conn:
            conn.execute("UPDATE users SET referrals = referrals + 1 WHERE id = ?", (user_id,))

def get_all_user_ids():
    with closing(sqlite3.connect(DB_NAME)) as conn:
        cur = conn.execute("SELECT id FROM users")
        return [row[0] for row in cur.fetchall()]

def gift_all_users(amount):
    with closing(sqlite3.connect(DB_NAME)) as conn:
        with conn:
            conn.execute("UPDATE users SET points = points + ?", (amount,))
