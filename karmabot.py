""" A Discord bot that tracks user karma in a sqlite database.
Users can give and receive karma points by using commands."""

import re

import discord

from user import User
from settings import BUZZKILL_POSITIVE_MAX, BUZZKILL_NEGATIVE_MAX, DISCORD_API_KEY

intents = discord.Intents.default()
intents.members = True
intents.message_content = True
bot = discord.Client(intents=intents)

@bot.event
async def on_ready():
    """Event handler for when the bot is ready."""
    print(f'Logged in as {bot.user.name} ({bot.user.id})')
    print('------')

@bot.event
async def on_message(message):
    """Event handler for incoming messages."""
    if message.author.bot:
        return
    if not message.mentions:
        return

    for mentioned_user in message.mentions:
        mention_str = f'<@{mentioned_user.id}>'
        # Discord also supports <@!id> for nicknames
        alt_mention_str = f'<@!{mentioned_user.id}>'

        # Karma query pattern
        pattern_query = rf'({re.escape(mention_str)}|{re.escape(alt_mention_str)})\s*karma\b'
        # Karma adjustment pattern
        pattern_adjust = rf'({re.escape(mention_str)}|{re.escape(alt_mention_str)})\s*([+-]+)'

        if re.search(pattern_query, message.content, re.IGNORECASE):
            user = User(mentioned_user)
            karma = user.get_karma()
            await message.channel.send(
                f"{mentioned_user.display_name} has {karma if karma is not None else 0} karma."
            )
        elif match := re.search(pattern_adjust, message.content):
            symbol_str = match.group(2)
            if all(c == '+' for c in symbol_str):
                delta = len(symbol_str)
            elif all(c == '-' for c in symbol_str):
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

            user = User(mentioned_user)
            user.update_karma(delta)
            await message.channel.send(
                f"{mentioned_user.display_name} now has {user.get_karma()} karma."
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
