import sqlite3
import os
import threading

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "tickets.db")
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

_lock = threading.Lock()


def _connect():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with _lock, _connect() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS tickets (
                channel_id INTEGER PRIMARY KEY,
                guild_id INTEGER NOT NULL,
                owner_id INTEGER NOT NULL,
                ticket_type TEXT NOT NULL,
                ticket_number INTEGER NOT NULL,
                created_at TEXT NOT NULL,
                closed INTEGER NOT NULL DEFAULT 0
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS ticket_counters (
                ticket_type TEXT PRIMARY KEY,
                last_number INTEGER NOT NULL DEFAULT 0
            )
            """
        )
        conn.commit()


def next_ticket_number(ticket_type: str) -> int:
    with _lock, _connect() as conn:
        cur = conn.execute(
            "SELECT last_number FROM ticket_counters WHERE ticket_type = ?",
            (ticket_type,),
        )
        row = cur.fetchone()
        if row is None:
            new_number = 1
            conn.execute(
                "INSERT INTO ticket_counters (ticket_type, last_number) VALUES (?, ?)",
                (ticket_type, new_number),
            )
        else:
            new_number = row["last_number"] + 1
            conn.execute(
                "UPDATE ticket_counters SET last_number = ? WHERE ticket_type = ?",
                (new_number, ticket_type),
            )
        conn.commit()
        return new_number


def create_ticket(channel_id: int, guild_id: int, owner_id: int, ticket_type: str, ticket_number: int, created_at: str):
    with _lock, _connect() as conn:
        conn.execute(
            """
            INSERT OR REPLACE INTO tickets
                (channel_id, guild_id, owner_id, ticket_type, ticket_number, created_at, closed)
            VALUES (?, ?, ?, ?, ?, ?, 0)
            """,
            (channel_id, guild_id, owner_id, ticket_type, ticket_number, created_at),
        )
        conn.commit()


def get_ticket(channel_id: int):
    with _lock, _connect() as conn:
        cur = conn.execute("SELECT * FROM tickets WHERE channel_id = ?", (channel_id,))
        return cur.fetchone()


def mark_closed(channel_id: int):
    with _lock, _connect() as conn:
        conn.execute("UPDATE tickets SET closed = 1 WHERE channel_id = ?", (channel_id,))
        conn.commit()


def delete_ticket(channel_id: int):
    with _lock, _connect() as conn:
        conn.execute("DELETE FROM tickets WHERE channel_id = ?", (channel_id,))
        conn.commit()
