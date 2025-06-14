"""A leaderboard for finding out who has the best and worst karma in a server."""

import asyncio

from discord import Guild

from db import KarmaDatabase
from user import User
from settings import LEADERBOARD_SIZE


async def get_leaderboard_by_guild(guild: Guild) -> list[User]:
    """Returns a list of users with the most and least karma."""
    db = KarmaDatabase()
    user_ids = db.all_user_ids()
    if not user_ids:
        return []

    # Convert user ids to User objects
    users = await asyncio.gather(
        *[User.from_id(user_id, guild) for user_id in user_ids]
    )
    users = [user for user in users if user is not None]

    size = max(1, min(LEADERBOARD_SIZE, 100, len(users)))

    top_users = sorted(users, key=lambda user: user.get_karma() or 0, reverse=True)[
        :size
    ]
    bottom_users = sorted(users, key=lambda user: user.get_karma() or 0)[:size]

    return top_users, bottom_users
