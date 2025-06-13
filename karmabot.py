""" A Discord bot that tracks user karma in a sqlite database.
Users can give and receive karma points by using commands."""

import os
import sqlite3

import discord

from db import initialize_db

initialize_db()

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
    