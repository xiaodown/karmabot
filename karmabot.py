""" A Discord bot that tracks user karma in a sqlite database.
Users can give and receive karma points by using commands."""

import re

import discord

from user import User

bot = discord.Client(intents=discord.Intents.default())

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

        pattern = rf'({re.escape(mention_str)}|{re.escape(alt_mention_str)})\s*([+-]+)'
        matches = re.findall(pattern, message.content)
        buzzkill = False

        for match in matches:
            symbol_str = match[1]
            if all(c == '+' for c in symbol_str):
                delta = len(symbol_str)
            elif all(c == '-' for c in symbol_str):
                delta = -len(symbol_str)
            else:
                continue

            # Buzzkill mode: cap delta at +/-5
            if delta > 5:
                delta = 5
                buzzkill = True
            elif delta < -5:
                delta = -5
                buzzkill = True

            user = User(mentioned_user)
            user.update_karma(delta)
            await message.channel.send(
                f"{mentioned_user.mention} now has {user.get_karma()} karma."
            )
            if buzzkill:
                await message.channel.send(
                    f"_Buzzkill Mode™ has limited karma change to {delta} points._"
                )
