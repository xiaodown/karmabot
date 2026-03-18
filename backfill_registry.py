"""Slowly populate the local user/guild registry for existing karma rows."""

import argparse
import asyncio

import discord

from db import KarmaDatabase
from settings import DISCORD_API_KEY


class RegistryBackfillClient(discord.Client):
    """Discord client that fills in local registry data with rate limiting."""

    def __init__(self, request_delay: float, retry_delay: float):
        intents = discord.Intents.default()
        intents.members = True
        super().__init__(intents=intents)
        self.db = KarmaDatabase()
        self.request_delay = request_delay
        self.retry_delay = retry_delay

    async def on_ready(self):
        """Backfill the local registry once the bot is connected."""
        print(f"Logged in as {self.user.name} ({self.user.id})")

        karma_user_ids = self.db.all_user_ids()
        if not karma_user_ids:
            print("No karma-tracked users found. Nothing to backfill.")
            await self.close()
            return

        fetched = 0
        skipped = 0
        missing = 0
        errors = 0

        for guild in self.guilds:
            self.db.record_guild(guild)
            print(f"Scanning guild: {guild.name} ({guild.id})")

            for user_id in karma_user_ids:
                if not self.db.needs_registry_backfill(user_id, guild.id):
                    skipped += 1
                    continue

                member = guild.get_member(user_id)
                fetched_from_api = False

                if member is None:
                    try:
                        member = await guild.fetch_member(user_id)
                        fetched_from_api = True
                    except discord.NotFound:
                        if not self.db.has_user_registry_entry(user_id):
                            self.db.upsert_user(user_id, f"user-{user_id}")
                        self.db.upsert_user_nickname(user_id, guild.id, None, 0)
                        missing += 1
                        if self.request_delay > 0:
                            await asyncio.sleep(self.request_delay)
                        continue
                    except discord.HTTPException as exc:
                        errors += 1
                        print(
                            f"Fetch failed for user {user_id} in guild {guild.id}: "
                            f"{exc.status} {exc}"
                        )
                        await asyncio.sleep(self.retry_delay)
                        continue

                self.db.record_member(member, guild)
                fetched += 1

                if fetched_from_api and self.request_delay > 0:
                    await asyncio.sleep(self.request_delay)

        print(
            "Backfill complete. "
            f"fetched={fetched} skipped={skipped} missing={missing} errors={errors}"
        )
        await self.close()


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments for the backfill job."""
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--request-delay",
        type=float,
        default=1.5,
        help="Seconds to wait after each Discord API member fetch.",
    )
    parser.add_argument(
        "--retry-delay",
        type=float,
        default=30.0,
        help="Seconds to wait after a Discord HTTP error before continuing.",
    )
    return parser.parse_args()


async def main(request_delay: float, retry_delay: float) -> None:
    """Run the backfill client with explicit async lifecycle management."""
    client = RegistryBackfillClient(
        request_delay=request_delay,
        retry_delay=retry_delay,
    )
    async with client:
        await client.start(DISCORD_API_KEY)
    await asyncio.sleep(0)


if __name__ == "__main__":
    args = parse_args()
    asyncio.run(
        main(
            request_delay=args.request_delay,
            retry_delay=args.retry_delay,
        )
    )
