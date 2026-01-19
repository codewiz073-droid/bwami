import sqlite3
from contextlib import closing
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_FILE = os.path.join(BASE_DIR, "chat.db")

def get_connection():
    conn = sqlite3.connect(DB_FILE, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with closing(get_connection()) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS chats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chat_id TEXT,
                role TEXT,
                message TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()

def save_message(chat_id, role, message):
    with closing(get_connection()) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO chats (chat_id, role, message)
            VALUES (?, ?, ?)
        """, (chat_id, role, message))
        conn.commit()

def get_chat_list():
    with closing(get_connection()) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT chat_id,
                   MIN(message) as title
            FROM chats
            GROUP BY chat_id
            ORDER BY MAX(id) DESC
        """)
        return [dict(row) for row in cursor.fetchall()]

def get_chat_history(chat_id):
    with closing(get_connection()) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT role, message
            FROM chats
            WHERE chat_id = ?
            ORDER BY id ASC
        """, (chat_id,))
        return [dict(row) for row in cursor.fetchall()]

def delete_chat(chat_id):
    with closing(get_connection()) as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM chats WHERE chat_id = ?", (chat_id,))
        conn.commit()
