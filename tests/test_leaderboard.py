"""Tests for get_leaderboard_by_guild."""

import asyncio
import os
import tempfile
import unittest

from db import KarmaDatabase
from leaderboard import get_leaderboard_by_guild


class FakeGuild:
    def __init__(self, guild_id):
        self.id = guild_id


class GetLeaderboardByGuildTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.db = KarmaDatabase(os.path.join(self._tmp.name, "test.sqlite3"))
        self.db.upsert_guild(100, "Test Guild")
        self.guild = FakeGuild(100)

    def tearDown(self):
        self._tmp.cleanup()

    def add_member(self, user_id, name, nickname, karma):
        self.db.create(user_id)
        self.db.update(user_id, karma)
        self.db.upsert_user(user_id, name)
        self.db.upsert_user_nickname(user_id, 100, nickname, 1)

    def test_returns_ranked_users(self):
        self.add_member(1, "alice", "Al", 5)
        self.add_member(2, "bob", None, -3)
        self.add_member(3, "carol", None, 10)

        top, bottom = asyncio.run(get_leaderboard_by_guild(self.guild, self.db))

        self.assertEqual([u.id for u in top], [3, 1, 2])
        self.assertEqual([u.id for u in bottom], [2, 1, 3])
        self.assertEqual(top[0].get_karma(), 10)
        self.assertEqual(top[0].display_name, "carol")
        self.assertEqual(bottom[0].display_name, "bob")

    def test_excludes_non_members(self):
        self.add_member(1, "alice", "Al", 5)
        self.db.create(2)
        self.db.update(2, 99)
        self.db.upsert_user(2, "gone")
        self.db.upsert_user_nickname(2, 100, None, 0)

        top, bottom = asyncio.run(get_leaderboard_by_guild(self.guild, self.db))

        self.assertEqual([u.id for u in top], [1])
        self.assertEqual([u.id for u in bottom], [1])

    def test_empty_database(self):
        top, bottom = asyncio.run(get_leaderboard_by_guild(self.guild, self.db))
        self.assertEqual(top, [])
        self.assertEqual(bottom, [])

    def test_respects_shared_db(self):
        # The caller's db instance must be used, not a fresh one on the
        # default path.
        self.add_member(1, "alice", None, 4)
        top, _ = asyncio.run(get_leaderboard_by_guild(self.guild, self.db))
        self.assertEqual([u.id for u in top], [1])


if __name__ == "__main__":
    unittest.main()
