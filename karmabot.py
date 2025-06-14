"""A Discord bot that tracks user karma in a sqlite database.
Users can give and receive karma points by using commands."""

import re

import discord

from user import User
from leaderboard import get_leaderboard_by_guild
from settings import (
    BUZZKILL_NEGATIVE_MAX,
    BUZZKILL_POSITIVE_MAX,
    DISCORD_API_KEY,
    ENABLE_LEADERBOARD,
    ENFORCE_KARMA_SPAM_DELAY,
    PREVENT_SELF_KARMA,
)

intents = discord.Intents.default()
intents.members = True
intents.message_content = True
bot = discord.Client(intents=intents)


@bot.event
async def on_ready():
    """Event handler for when the bot is ready."""
    print(f"Logged in as {bot.user.name} ({bot.user.id})")


async def bot_commands(message):
    """Handles bot commands.\n\n

    These are command that are invoked by @mentioning the bot.

    Args:
        message (discord.Message): The message that triggered the command.
    """

    # Help requests
    if "help" in message.content.lower() or "?" in message.content.lower():
        bot_member = message.guild.me
        help_message = (
            "Karma Bot Commands:\n"
            "- `@user +` or `@user ++` etc -    Give karma to a user"
            + f" (max of {BUZZKILL_POSITIVE_MAX}).\n"
            "- `@user -` or `@user --` -    Remove karma from a user"
            + f" (max of {BUZZKILL_NEGATIVE_MAX}).\n"
            "- `@user karma` -    Check a user's karma.\n"
            f"- `@{bot_member.display_name} top` -    Show the top users by karma.\n"
            f"- `@{bot_member.display_name} bottom` -    Show the bottom users by karma.\n"
            f"- `@{bot_member.display_name} help` or `?` -    Show this help message.\n"
        )
        await message.channel.send(help_message)

    # Leaderboard requests
    if "top" in message.content.lower() or "bottom" in message.content.lower():
        if ENABLE_LEADERBOARD:
            await message.channel.send("Fetching leaderboard, please wait...")
            top_users, bottom_users = await get_leaderboard_by_guild(message.guild)
            if "top" in message.content.lower():
                msg = "🏆 **Top Users:**\n```"
                i = 1
                for user in top_users:
                    karma = user.get_karma()
                    karma_str = f"{karma:+d}" if karma != 0 else "0"
                    msg += f"{i}) {user.display_name:<20} {karma_str:>5}\n"
                    i += 1
                msg += "```"
                await message.channel.send(msg)
            if "bottom" in message.content.lower():
                msg = "💀 **Bottom Users:**\n```"
                i = 1
                for user in bottom_users:
                    karma = user.get_karma()
                    karma_str = f"{karma:+d}" if karma != 0 else "0"
                    msg += f"{i}) {user.display_name:<20} {karma_str:>5}\n"
                    i += 1
                msg += "```"
                await message.channel.send(msg)


async def karma_commands(user: User, message: discord.Message):
    """Handles user's karma adjustments and queries.\n\n

    This is when a user has been @mentioned in a message.

    Args:
        user (User): The User object representing the mentioned user.
        message (discord.Message): The message that triggered the command.
    """

    # Construct the string version of the mention (e.g. <@123456789012345678>)
    # This is what the bot sees when someone @mentions a user.
    mention_str = f"<@{user.id}>"
    # Discord also supports <@!id> for nicknames
    alt_mention_str = f"<@!{user.id}>"

    # Construct the regexes for queries and adjustments
    # Karma query pattern
    karma_query_pattern = (
        rf"({re.escape(mention_str)}|{re.escape(alt_mention_str)})\s*karma\b"
    )
    # Karma adjustment pattern
    karma_adjustment_pattern = (
        rf"({re.escape(mention_str)}|{re.escape(alt_mention_str)})\s*([+-]+)"
    )

    # Command is a karma query
    if re.search(karma_query_pattern, message.content, re.IGNORECASE):
        karma = user.get_karma() if user.get_karma() is not None else 0
        await message.channel.send(f"{user.display_name} has {karma} karma.")

    # Command is a karma adjustment
    elif match := re.search(karma_adjustment_pattern, message.content):

        # Prevent self-karma
        if PREVENT_SELF_KARMA:
            if user.id == message.author.id:
                karma = user.get_karma() if user.get_karma() is not None else 0
                await message.channel.send(f"{user.display_name} has {karma} karma.")
                await message.channel.send("_Buzzkill Mode™ has prevented self-karma._")
                return

        # Prevent karma spam
        if ENFORCE_KARMA_SPAM_DELAY:
            if not user.can_update_karma():
                await message.channel.send(
                    f"{user.display_name} cannot update karma yet."
                )
                await message.channel.send("_Buzzkill Mode™ has prevented karma spam._")
                return

        # Count the +'s and -'s
        symbol_str = match.group(2)
        if all(c == "+" for c in symbol_str):
            delta = len(symbol_str)
        elif all(c == "-" for c in symbol_str):
            delta = -len(symbol_str)
        else:
            return

        # Cap the karma delta
        buzzkill = False
        if delta > BUZZKILL_POSITIVE_MAX:
            delta = BUZZKILL_POSITIVE_MAX
            buzzkill = True
        elif delta < -BUZZKILL_NEGATIVE_MAX:
            delta = -BUZZKILL_NEGATIVE_MAX
            buzzkill = True

        # Update the user's karma and send a confirmation message
        user.update_karma(delta)
        await message.channel.send(
            f"{user.display_name} now has {user.get_karma()} karma."
        )
        if buzzkill:
            await message.channel.send(
                f"_Buzzkill Mode™ has limited karma change to {delta} points._"
            )


@bot.event
async def on_message(message):
    """Event handler for incoming messages."""
    if message.author.bot:
        return
    if not message.mentions:
        return

    for mentioned_user in message.mentions:

        if mentioned_user == bot.user:
            await bot_commands(message)

        user = User(mentioned_user)
        await karma_commands(user, message)


if __name__ == "__main__":
    try:
        bot.run(DISCORD_API_KEY)
    except discord.LoginFailure as e:
        print(f"Failed to log in: {e}")
    except discord.DiscordException as e:
        print(f"A Discord-related error occurred: {e}")
