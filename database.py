import sqlite3
import pandas as pd
import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent
DATA_FOLDER = PROJECT_ROOT / "data"
DB_FILE = DATA_FOLDER / "expenses.db"

EXPENSE_CATEGORIES = [
    "Food & Dining", "Rent/Utilities", "Transportation",
    "Shopping", "Entertainment", "Health", "Miscellaneous"
]

os.makedirs(DATA_FOLDER, exist_ok=True)


def init_db():
    """Configures the database schema and performs auto-migrations for multi-user support."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL DEFAULT 'admin',
            date TEXT NOT NULL,
            category TEXT NOT NULL,
            description TEXT,
            amount REAL NOT NULL
        )
    """)
    conn.commit()

    cursor.execute("PRAGMA table_info(expenses)")
    columns = [col[1] for col in cursor.fetchall()]

    if "username" not in columns:
        try:
            cursor.execute("ALTER TABLE expenses ADD COLUMN username TEXT NOT NULL DEFAULT 'admin'")
            conn.commit()
        except sqlite3.OperationalError:
            pass

    conn.close()


def load_data(username):
    """Fetches records from the DB filtered by the logged-in user's name."""
    conn = sqlite3.connect(DB_FILE)
    query = "SELECT * FROM expenses WHERE username = ?"
    df = pd.read_sql_query(query, conn, params=(username,))
    conn.close()

    if not df.empty:
        df['date'] = pd.to_datetime(df['date'])
    return df


def save_expense(expense_dict, username):
    """Saves a new entry tied directly to the current user's profile."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO expenses (username, date, category, description, amount)
        VALUES (?, ?, ?, ?, ?)
    """, (
        username,
        str(expense_dict['date']),
        expense_dict['category'],
        expense_dict['description'],
        expense_dict['amount']
    ))
    conn.commit()
    conn.close()


def delete_expense(expense_id, username):
    """Deletes an entry only if the logged-in user owns it (Security Check)."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM expenses WHERE id = ? AND username = ?", (int(expense_id), username))
    conn.commit()
    conn.close()

init_db()