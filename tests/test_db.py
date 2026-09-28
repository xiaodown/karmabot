"""Tests for the KarmaDatabase layer."""

import os
import tempfile
import time
import unittest

from db import KarmaDatabase
from settings import KARMA_SPAM_DELAY


class KarmaDatabaseTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.db = KarmaDatabase(os.path.join(self._tmp.name, "test.sqlite3"))

    def tearDown(self):
        self._tmp.cleanup()

    def test_create_and_get_karma(self):
        self.assertIsNone(self.db.get_karma(1))
        self.db.create(1)
        self.assertEqual(self.db.get_karma(1), 0)

    def test_create_ignores_duplicate(self):
        self.db.create(1, karma=7)
        self.db.create(1, karma=99)
        self.assertEqual(self.db.get_karma(1), 7)

    def test_update_adds_delta(self):
        self.db.create(1)
        self.db.update(1, 5)
        self.db.update(1, -2)
        self.assertEqual(self.db.get_karma(1), 3)

    def test_update_sets_last_karma_timestamp(self):
        self.db.create(1)
        before = int(time.time())
        self.db.update(1, 1)
        after = int(time.time())
        row = self.db._conn.execute(
            "SELECT last_karma FROM karma WHERE user_id = 1"
        ).fetchone()
        self.assertGreaterEqual(row[0], before)
        self.assertLessEqual(row[0], after)

    def test_spam_delay_blocks_then_allows(self):
        self.db.create(1)
        self.db.update(1, 1)
        self.assertFalse(self.db.can_update_karma(1))
        self.db._conn.execute(
            "UPDATE karma SET last_karma = ? WHERE user_id = 1",
            (int(time.time()) - KARMA_SPAM_DELAY - 1,),
        )
        self.db._conn.commit()
        self.assertTrue(self.db.can_update_karma(1))

    def test_unknown_user_can_update_karma(self):
        self.assertTrue(self.db.can_update_karma(999))

    def test_delete_removes_user(self):
        self.db.create(1)
        self.db.delete(1)
        self.assertIsNone(self.db.get_karma(1))

    def test_wal_mode_enabled(self):
        row = self.db._conn.execute("PRAGMA journal_mode").fetchone()
        self.assertEqual(row[0], "wal")

    def test_persistent_connection_reused(self):
        self.assertIs(self.db._conn, self.db._conn)
        self.db.create(1)
        self.db.update(1, 3)
        self.assertEqual(self.db.get_karma(1), 3)

    def test_multiple_instances_share_file(self):
        other = KarmaDatabase(self.db.db_path)
        self.db.create(42, karma=9)
        self.assertEqual(other.get_karma(42), 9)
        other._conn.close()

    def test_registry_roundtrip(self):
        self.db.upsert_guild(100, "Test Guild")
        self.db.upsert_user(1, "alice")
        self.db.upsert_user_nickname(1, 100, "Al", 1)

        self.assertTrue(self.db.has_user_registry_entry(1))
        self.assertFalse(self.db.needs_registry_backfill(1, 100))
        self.assertTrue(self.db.needs_registry_backfill(2, 100))

        self.db.upsert_guild(100, "Renamed Guild")
        row = self.db._conn.execute(
            "SELECT guild_name FROM guilds WHERE guild_id = 100"
        ).fetchone()
        self.assertEqual(row[0], "Renamed Guild")

    def test_ranked_entries_require_membership(self):
        self.db.upsert_guild(100, "Test Guild")
        self.db.create(1)
        self.db.update(1, 5)
        self.db.create(2)
        self.db.update(2, 9)
        self.db.upsert_user(1, "member")
        self.db.upsert_user(2, "ex-member")
        self.db.upsert_user_nickname(1, 100, None, 1)
        self.db.upsert_user_nickname(2, 100, None, 0)

        top = self.db.get_top_karma_entries(100, 10)
        self.assertEqual([row["user_id"] for row in top], [1])
        self.assertEqual(top[0]["user_name"], "member")

    def test_all_guild_ids_sorted(self):
        self.db.upsert_guild(3, "c")
        self.db.upsert_guild(1, "a")
        self.db.upsert_guild(2, "b")
        self.assertEqual(self.db.all_guild_ids(), [1, 2, 3])


if __name__ == "__main__":
    unittest.main()
