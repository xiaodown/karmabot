"""Database handling for Karmabot.

This module provides the KarmaDatabase class, which encapsulates all
CRUD operations for managing user karma in a SQLite database.
"""

import sqlite3
import time

from settings import SQLITE_DB, KARMA_SPAM_DELAY


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

    def _get_conn(self) -> sqlite3.Connection:
        """Return a sqlite connection configured for this app."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    def _initialize_db(self) -> None:
        """
        Create or migrate the database schema.
        """
        with self._get_conn() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS karma (
                    user_id INTEGER PRIMARY KEY,
                    karma INTEGER DEFAULT 0,
                    last_karma INTEGER DEFAULT 0
                )
            """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS guilds (
                    guild_id INTEGER PRIMARY KEY,
                    guild_name TEXT NOT NULL DEFAULT ''
                )
            """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    user_name TEXT NOT NULL DEFAULT ''
                )
            """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS user_nicknames (
                    user_id INTEGER NOT NULL,
                    guild_id INTEGER NOT NULL,
                    nickname TEXT,
                    PRIMARY KEY (user_id, guild_id),
                    FOREIGN KEY (user_id) REFERENCES users(user_id),
                    FOREIGN KEY (guild_id) REFERENCES guilds(guild_id)
                )
            """
            )
            columns = {
                row["name"]
                for row in conn.execute("PRAGMA table_info(user_nicknames)").fetchall()
            }
            if "is_member" not in columns:
                conn.execute(
                    "ALTER TABLE user_nicknames ADD COLUMN is_member INTEGER"
                )
            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_karma_karma_desc
                ON karma (karma DESC, user_id ASC)
            """
            )
            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_karma_karma_asc
                ON karma (karma ASC, user_id ASC)
            """
            )
            conn.commit()

    def create(self, user_id: int, karma: int = 0) -> None:
        """
        Add a new user to the karma table with an initial karma value.

        Args:
            user_id (int): The Discord user ID to add.
            karma (int, optional): The initial karma value. Defaults to 0.
        """
        with self._get_conn() as conn:
            conn.execute(
                "INSERT OR IGNORE INTO karma (user_id, karma) VALUES (?, ?)",
                (user_id, karma),
            )

    def get_karma(self, user_id: int) -> int | None:
        """
        Retrieve the karma value for a specific user.

        Args:
            user_id (int): The Discord user ID to look up.

        Returns:
            int or None: The user's karma value, or None if the user does not exist.
        """
        with self._get_conn() as conn:
            cur = conn.execute("SELECT karma FROM karma WHERE user_id = ?", (user_id,))
            row = cur.fetchone()
            return row[0] if row else None

    def update(self, user_id: int, delta: int) -> None:
        """
        Update the karma value for a specific user by a given delta,
        and update the last_karma timestamp.

        Args:
            user_id (int): The Discord user ID to update.
            delta (int): The amount to add (or subtract) from the user's karma.
        """
        now = int(time.time())
        with self._get_conn() as conn:
            conn.execute(
                "UPDATE karma SET karma = karma + ?, last_karma = ? WHERE user_id = ?",
                (delta, now, user_id),
            )

    def delete(self, user_id: int) -> None:
        """
        Remove a user from the karma table.

        Args:
            user_id (int): The Discord user ID to delete.
        """
        with self._get_conn() as conn:
            conn.execute("DELETE FROM karma WHERE user_id = ?", (user_id,))

    def can_update_karma(self, user_id: int) -> bool:
        """
        Determine whether enough time has passed since the user's last karma update.

        This method checks the 'last_karma' timestamp for the specified user in the database.
        If the time elapsed since the last update is greater than or equal to the specified delay,
        the user is eligible for another karma change.

        Args:
            user_id (int): The Discord user ID to check.

        Returns:
            bool: True if the user can receive a karma update, False otherwise.
        """
        with self._get_conn() as conn:
            cur = conn.execute(
                "SELECT last_karma FROM karma WHERE user_id = ?", (user_id,)
            )
            row = cur.fetchone()
            if row and time.time() - row[0] < KARMA_SPAM_DELAY:
                return False
            return True

    def all_user_ids_and_karma(self) -> list[tuple[int, int]]:
        """
        Retrieve all users and their karma values from the database.

        Returns:
            list[tuple[int, int]]: A list of tuples containing user IDs and their karma values.
        """
        with self._get_conn() as conn:
            cur = conn.execute("SELECT user_id, karma FROM karma")
            return cur.fetchall()

    def all_user_ids(self) -> list[int]:
        """
        Retrieve a list of all user IDs in the karma table.

        Returns:
            list[int]: A list of Discord user IDs.
        """
        with self._get_conn() as conn:
            cur = conn.execute("SELECT user_id FROM karma")
            return [row[0] for row in cur.fetchall()]

    def karma_user_count(self) -> int:
        """Return the number of karma-tracked users."""
        with self._get_conn() as conn:
            cur = conn.execute("SELECT COUNT(*) FROM karma")
            return cur.fetchone()[0]

    def upsert_guild(self, guild_id: int, guild_name: str) -> None:
        """Insert or update a guild in the local registry."""
        with self._get_conn() as conn:
            conn.execute(
                """
                INSERT INTO guilds (guild_id, guild_name)
                VALUES (?, ?)
                ON CONFLICT(guild_id) DO UPDATE SET guild_name = excluded.guild_name
            """,
                (guild_id, guild_name),
            )

    def upsert_user(self, user_id: int, user_name: str) -> None:
        """Insert or update a user in the local registry."""
        with self._get_conn() as conn:
            conn.execute(
                """
                INSERT INTO users (user_id, user_name)
                VALUES (?, ?)
                ON CONFLICT(user_id) DO UPDATE SET user_name = excluded.user_name
            """,
                (user_id, user_name),
            )

    def upsert_user_nickname(
        self,
        user_id: int,
        guild_id: int,
        nickname: str | None,
        is_member: int | None,
    ) -> None:
        """Insert or update a user's guild-specific name and membership state."""
        with self._get_conn() as conn:
            conn.execute(
                """
                INSERT INTO user_nicknames (user_id, guild_id, nickname, is_member)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(user_id, guild_id) DO UPDATE SET
                    nickname = excluded.nickname,
                    is_member = excluded.is_member
            """,
                (user_id, guild_id, nickname, is_member),
            )

    def record_guild(self, guild) -> None:
        """Store a guild from Discord in the local registry."""
        self.upsert_guild(guild.id, guild.name)

    def record_member(self, member, guild=None) -> None:
        """Store a member or user plus any guild-specific nickname."""
        target_guild = guild or getattr(member, "guild", None)
        self.upsert_user(member.id, member.name)
        if target_guild is not None:
            self.upsert_guild(target_guild.id, target_guild.name)
            self.upsert_user_nickname(
                member.id,
                target_guild.id,
                getattr(member, "nick", None),
                1,
            )

    def record_departed_member(self, member, guild=None) -> None:
        """Mark a user as not currently belonging to a guild."""
        target_guild = guild or getattr(member, "guild", None)
        if target_guild is None:
            return

        self.upsert_user(member.id, member.name)
        self.upsert_guild(target_guild.id, target_guild.name)
        self.upsert_user_nickname(
            member.id,
            target_guild.id,
            None,
            0,
        )

    def record_message(self, message) -> None:
        """Record the message's guild, author, and mentions into the registry."""
        if message.guild is None:
            return

        self.record_guild(message.guild)
        self.record_member(message.author, message.guild)
        for member in message.mentions:
            self.record_member(member, message.guild)

    def get_top_karma_entries(self, guild_id: int, limit: int) -> list[sqlite3.Row]:
        """Return the highest-karma users with locally cached names."""
        return self._get_ranked_karma_entries(guild_id, limit, descending=True)

    def get_bottom_karma_entries(self, guild_id: int, limit: int) -> list[sqlite3.Row]:
        """Return the lowest-karma users with locally cached names."""
        return self._get_ranked_karma_entries(guild_id, limit, descending=False)

    def _get_ranked_karma_entries(
        self, guild_id: int, limit: int, descending: bool
    ) -> list[sqlite3.Row]:
        """Return ranked karma rows, attaching cached names after ranking."""
        order = "DESC" if descending else "ASC"
        with self._get_conn() as conn:
            cur = conn.execute(
                f"""
                SELECT ranked.user_id, ranked.karma, users.user_name, ranked.nickname
                FROM (
                    SELECT karma.user_id, karma.karma, user_nicknames.nickname
                    FROM karma
                    JOIN user_nicknames
                        ON user_nicknames.user_id = karma.user_id
                        AND user_nicknames.guild_id = ?
                        AND user_nicknames.is_member = 1
                    ORDER BY karma.karma {order}, karma.user_id ASC
                    LIMIT ?
                ) AS ranked
                LEFT JOIN users ON users.user_id = ranked.user_id
                ORDER BY ranked.karma {order}, ranked.user_id ASC
            """,
                (guild_id, limit),
            )
            return cur.fetchall()

    def all_guild_ids(self) -> list[int]:
        """Return all guild IDs in the local registry."""
        with self._get_conn() as conn:
            cur = conn.execute("SELECT guild_id FROM guilds ORDER BY guild_id")
            return [row[0] for row in cur.fetchall()]

    def needs_registry_backfill(self, user_id: int, guild_id: int) -> bool:
        """Return True when we are missing user or guild-specific name data."""
        with self._get_conn() as conn:
            user_row = conn.execute(
                "SELECT 1 FROM users WHERE user_id = ?",
                (user_id,),
            ).fetchone()
            nickname_row = conn.execute(
                """
                SELECT is_member
                FROM user_nicknames
                WHERE user_id = ? AND guild_id = ?
            """,
                (user_id, guild_id),
            ).fetchone()
        return (
            user_row is None
            or nickname_row is None
            or nickname_row["is_member"] is None
        )

    def has_user_registry_entry(self, user_id: int) -> bool:
        """Return True if the user exists in the local registry."""
        with self._get_conn() as conn:
            row = conn.execute(
                "SELECT 1 FROM users WHERE user_id = ?",
                (user_id,),
            ).fetchone()
        return row is not None
