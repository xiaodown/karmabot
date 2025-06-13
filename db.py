""" Database handling"""

import sqlite3

from settings import SQLITE_DB


class KarmaDatabase:
    """Handles CRUD operations."""
    def __init__(self, db_path=SQLITE_DB):
        self.db_path = db_path
        self._initialize_db()

    def _initialize_db(self):
        """Initialize the database by creating the karma table if it doesn't exist."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS karma (
                    user_id INTEGER PRIMARY KEY,
                    karma INTEGER DEFAULT 0
                )
            ''')

    def create(self, user_id: int, karma: int = 0):
        """Add a user to the database with an initial karma value."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                'INSERT OR IGNORE INTO karma (user_id, karma) VALUES (?, ?)',
                (user_id, karma)
            )

    def read(self, user_id: int):
        """Retrieve the karma value for a user."""
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.execute(
                'SELECT karma FROM karma WHERE user_id = ?',
                (user_id,)
            )
            row = cur.fetchone()
            return row[0] if row else None

    def update(self, user_id: int, delta: int):
        """Update the karma value for a user."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                'UPDATE karma SET karma = karma + ? WHERE user_id = ?',
                (delta, user_id)
            )

    def delete(self, user_id: int):
        """Delete a user from the database."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                'DELETE FROM karma WHERE user_id = ?',
                (user_id,)
            )
