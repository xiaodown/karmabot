"""User class for Karmabot."""

import discord

from db import KarmaDatabase


class User:
    """Represents a user and provides methods to interact with the karma database."""

    def __init__(
        self,
        discord_user=None,
        db=None,
        *,
        user_id: int | None = None,
        name: str | None = None,
        display_name: str | None = None,
        karma: int | None = None,
    ):
        """
        Initialize a User object.

        Args:
            discord_user: A discord.Member or discord.User object.
            db: Optional KarmaDatabase instance. If None, a new one is created.
        """
        self.db = db if db is not None else KarmaDatabase()
        self._karma = karma

        if discord_user is not None:
            self.id = discord_user.id
            self.name = discord_user.name
            self.display_name = discord_user.display_name
            return

        if user_id is None or name is None or display_name is None:
            raise ValueError(
                "User requires either a Discord user or explicit user_id/name/display_name."
            )

        self.id = user_id
        self.name = name
        self.display_name = display_name

    def exists(self) -> bool:
        """
        Check if the user exists in the database.

        Returns:
            bool: True if user exists, False otherwise.
        """
        return self.db.get_karma(self.id) is not None

    def update_karma(self, delta: int) -> None:
        """
        Update the user's karma by a given delta.

        Args:
            delta (int): The amount to change the user's karma by.
        """
        if not self.exists():
            self.db.create(self.id)
        self.db.update(self.id, delta)
        if self._karma is not None:
            self._karma += delta

    def get_karma(self) -> int | None:
        """
        Retrieve the user's current karma.

        Returns:
            int or None: The user's karma, or None if not found.
        """
        if self._karma is not None:
            return self._karma
        return self.db.get_karma(self.id)

    @classmethod
    def from_message(cls, message, db=None):
        """
        Create a User object from a Discord message's author.

        Args:
            message: A discord.Message object.
            db: Optional KarmaDatabase instance.

        Returns:
            User: The corresponding User object.
        """
        return cls(message.author, db)

    def can_update_karma(self) -> bool:
        """
        Check if the user can update their karma based on the delay.

        Returns:
            bool: True if the user can update karma, False otherwise.
        """
        return self.db.can_update_karma(self.id)

    @classmethod
    async def from_id(cls, user_id: int, guild: discord.Guild, db=None):
        """
        Create a User object from a Discord user ID and guild.

        Args:
            user_id (int): The Discord user ID.
            guild (discord.Guild): The guild to search for the user.
            db: Optional KarmaDatabase instance.

        Returns:
            User: The corresponding User object, or None if not found.
        """
        member = guild.get_member(user_id)
        if member is None:
            try:
                member = await guild.fetch_member(user_id)
            except discord.NotFound:
                return None
        return cls(member, db)

    @classmethod
    def from_registry_row(cls, row, db=None):
        """
        Create a User object from a local registry/leaderboard query row.

        Args:
            row: A sqlite row containing user_id, karma, user_name, and nickname.
            db: Optional KarmaDatabase instance.

        Returns:
            User: A lightweight user populated from cached local data.
        """
        user_name = row["user_name"] or f"user-{row['user_id']}"
        display_name = row["nickname"] or user_name
        return cls(
            db=db,
            user_id=row["user_id"],
            name=user_name,
            display_name=display_name,
            karma=row["karma"],
        )
