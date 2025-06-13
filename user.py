"""User class for Karmabot."""

from db import KarmaDatabase

class User:
    """Represents a user and provides methods to interact with the karma database."""

    def __init__(self, discord_user, db=None):
        """
        Initialize a User object.

        Args:
            discord_user: A discord.Member or discord.User object.
            db: Optional KarmaDatabase instance. If None, a new one is created.
        """
        self.discord_id = discord_user.id
        self.discord_name = discord_user.name
        self.db = db if db is not None else KarmaDatabase()

    def exists(self) -> bool:
        """
        Check if the user exists in the database.

        Returns:
            bool: True if user exists, False otherwise.
        """
        return self.db.read(self.discord_id) is not None

    def update_karma(self, delta: int) -> None:
        """
        Update the user's karma by a given delta.

        Args:
            delta (int): The amount to change the user's karma by.
        """
        if not self.exists():
            self.db.create(self.discord_id)
        self.db.update(self.discord_id, delta)

    def get_karma(self) -> int | None:
        """
        Retrieve the user's current karma.

        Returns:
            int or None: The user's karma, or None if not found.
        """
        return self.db.read(self.discord_id)

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
