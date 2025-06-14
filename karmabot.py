"""A Discord bot that tracks user karma in a sqlite database.
Users can give and receive karma points by using commands."""

import re

import discord

from user import User
from settings import (
    BUZZKILL_NEGATIVE_MAX,
    BUZZKILL_POSITIVE_MAX,
    DISCORD_API_KEY,
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


@bot.event
async def on_message(message):
    """Event handler for incoming messages."""
    if message.author.bot:
        return
    if not message.mentions:
        return

    for mentioned_user in message.mentions:
        user = User(mentioned_user)

        mention_str = f"<@{user.id}>"
        # Discord also supports <@!id> for nicknames
        alt_mention_str = f"<@!{user.id}>"

        # Karma query pattern
        karma_query_pattern = (
            rf"({re.escape(mention_str)}|{re.escape(alt_mention_str)})\s*karma\b"
        )
        # Karma adjustment pattern
        karma_adjustment_pattern = (
            rf"({re.escape(mention_str)}|{re.escape(alt_mention_str)})\s*([+-]+)"
        )

        if re.search(karma_query_pattern, message.content, re.IGNORECASE):
            # The message contains a karma query request
            karma = user.get_karma() if user.get_karma() is not None else 0
            await message.channel.send(f"{user.display_name} has {karma} karma.")

        elif match := re.search(karma_adjustment_pattern, message.content):
            # The message contains a karma adjustment request

            # Prevent self-karma
            if PREVENT_SELF_KARMA:
                if user.id == message.author.id:
                    karma = user.get_karma() if user.get_karma() is not None else 0
                    await message.channel.send(
                        f"{user.display_name} has {karma} karma."
                    )
                    await message.channel.send(
                        "_Buzzkill Mode™ has prevented self-karma._"
                    )
                    continue

            # Prevent karma spam
            if ENFORCE_KARMA_SPAM_DELAY:
                if not user.can_update_karma():
                    await message.channel.send(
                        f"{user.display_name} cannot update karma yet."
                    )
                    await message.channel.send(
                        "_Buzzkill Mode™ has prevented karma spam._"
                    )
                    continue

            symbol_str = match.group(2)
            if all(c == "+" for c in symbol_str):
                delta = len(symbol_str)
            elif all(c == "-" for c in symbol_str):
                delta = -len(symbol_str)
            else:
                continue

            buzzkill = False
            if delta > BUZZKILL_POSITIVE_MAX:
                delta = BUZZKILL_POSITIVE_MAX
                buzzkill = True
            elif delta < -BUZZKILL_NEGATIVE_MAX:
                delta = -BUZZKILL_NEGATIVE_MAX
                buzzkill = True

            user.update_karma(delta)
            await message.channel.send(
                f"{user.display_name} now has {user.get_karma()} karma."
            )
            if buzzkill:
                await message.channel.send(
                    f"_Buzzkill Mode™ has limited karma change to {delta} points._"
                )


if __name__ == "__main__":
    try:
        bot.run(DISCORD_API_KEY)
    except discord.LoginFailure as e:
        print(f"Failed to log in: {e}")
    except discord.DiscordException as e:
        print(f"A Discord-related error occurred: {e}")
