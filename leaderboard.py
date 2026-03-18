"""A leaderboard for finding out who has the best and worst karma in a server."""

from discord import Guild

from db import KarmaDatabase
from user import User
from settings import LEADERBOARD_SIZE


async def get_leaderboard_by_guild(guild: Guild) -> tuple[list[User], list[User]]:
    """Returns a list of users with the most and least karma.
    
    Args:
        guild (discord.Guild): The Discord guild to fetch the leaderboard for.
    Returns:
        tuple: A tuple containing two lists:
            - The top users with the most karma.
            - The bottom users with the least karma.
    """
    db = KarmaDatabase()
    user_count = db.karma_user_count()
    if not user_count:
        return [], []

    size = max(1, min(LEADERBOARD_SIZE, 100, user_count))
    top_users = [
        User.from_registry_row(row, db)
        for row in db.get_top_karma_entries(guild.id, size)
    ]
    bottom_users = [
        User.from_registry_row(row, db)
        for row in db.get_bottom_karma_entries(guild.id, size)
    ]

    return top_users, bottom_users
