"""Database handling for Karmabot.

This module provides the KarmaDatabase class, which encapsulates all
CRUD operations for managing user karma in a SQLite database.
"""

import sqlite3

from settings import SQLITE_DB


class KarmaDatabase:
    """
    Handles all CRUD operations for the karma database.

    This class provides methods to initialize the database, add new users,
    update existing users' karma, retrieve karma values, and delete users.
    """

    def __init__(self, db_path=SQLITE_DB):
        """
        Initialize a KarmaDatabase instance and ensure the karma table exists.

        Args:
            db_path (str): Path to the SQLite database file.
        """
        self.db_path = db_path
        self._initialize_db()

    def _initialize_db(self) -> None:
        """
        Create the karma table in the database if it does not already exist.

        This method ensures the database is ready for CRUD operations.
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS karma (
                    user_id INTEGER PRIMARY KEY,
                    karma INTEGER DEFAULT 0
                )
            """
            )

    def create(self, user_id: int, karma: int = 0) -> None:
        """
        Add a new user to the karma table with an initial karma value.

        Args:
            user_id (int): The Discord user ID to add.
            karma (int, optional): The initial karma value. Defaults to 0.
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT OR IGNORE INTO karma (user_id, karma) VALUES (?, ?)",
                (user_id, karma),
            )

    def read(self, user_id: int) -> int | None:
        """
        Retrieve the karma value for a specific user.

        Args:
            user_id (int): The Discord user ID to look up.

        Returns:
            int or None: The user's karma value, or None if the user does not exist.
        """
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.execute("SELECT karma FROM karma WHERE user_id = ?", (user_id,))
            row = cur.fetchone()
            return row[0] if row else None

    def update(self, user_id: int, delta: int) -> None:
        """
        Update the karma value for a specific user by a given delta.

        Args:
            user_id (int): The Discord user ID to update.
            delta (int): The amount to add (or subtract) from the user's karma.
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "UPDATE karma SET karma = karma + ? WHERE user_id = ?", (delta, user_id)
            )

    def delete(self, user_id: int) -> None:
        """
        Remove a user from the karma table.

        Args:
            user_id (int): The Discord user ID to delete.
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("DELETE FROM karma WHERE user_id = ?", (user_id,))
