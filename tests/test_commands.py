"""Tests for command parsing and leaderboard message formatting in karmabot."""

import asyncio
import unittest
from unittest.mock import AsyncMock, MagicMock, patch

import karmabot
from karmabot import (
    BOTTOM_PATTERN,
    DISCORD_MESSAGE_LIMIT,
    HELP_PATTERN,
    TOP_PATTERN,
    _chunk_leaderboard,
    _leaderboard_rows,
)


class FakeUser:
    def __init__(self, display_name, karma):
        self.display_name = display_name
        self._karma = karma

    def get_karma(self):
        return self._karma


class CommandPatternTests(unittest.TestCase):
    def test_help_pattern(self):
        self.assertTrue(HELP_PATTERN.search("help"))
        self.assertTrue(HELP_PATTERN.search("@bot help"))
        self.assertFalse(HELP_PATTERN.search("helpful"))
        self.assertFalse(HELP_PATTERN.search("half"))

    def test_top_pattern(self):
        self.assertTrue(TOP_PATTERN.search("top"))
        self.assertTrue(TOP_PATTERN.search("@bot top"))
        self.assertFalse(TOP_PATTERN.search("stop"))
        self.assertFalse(TOP_PATTERN.search("laptop"))
        self.assertFalse(TOP_PATTERN.search("topic"))

    def test_bottom_pattern(self):
        self.assertTrue(BOTTOM_PATTERN.search("bottom"))
        self.assertTrue(TOP_PATTERN.search("bottom") is None)
        self.assertFalse(BOTTOM_PATTERN.search("bottoms"))


def make_bot_message(content):
    message = MagicMock()
    message.content = content
    message.channel.send = AsyncMock()
    message.guild = MagicMock()
    message.guild.me = MagicMock()
    message.guild.me.display_name = "KarmaBot"
    return message


class BotCommandTests(unittest.TestCase):
    def run_bot_commands(self, content):
        message = make_bot_message(content)
        fake_leaderboard = AsyncMock(return_value=([], []))
        with patch.object(karmabot, "ENABLE_LEADERBOARD", True), patch.object(
            karmabot, "get_leaderboard_by_guild", fake_leaderboard
        ):
            asyncio.run(karmabot.bot_commands(message))
        return message, fake_leaderboard

    def test_stop_does_not_trigger_leaderboard_or_help(self):
        message, fake_leaderboard = self.run_bot_commands("@bot why did you stop")
        fake_leaderboard.assert_not_awaited()
        message.channel.send.assert_not_awaited()

    def test_laptop_does_not_trigger_leaderboard(self):
        message, fake_leaderboard = self.run_bot_commands("@bot my laptop")
        fake_leaderboard.assert_not_awaited()
        message.channel.send.assert_not_awaited()

    def test_question_mark_still_triggers_help(self):
        message, _ = self.run_bot_commands("@bot why did you stop?")
        sent = [call.args[0] for call in message.channel.send.await_args_list]
        self.assertEqual(len(sent), 1)
        self.assertIn("Karma Bot Commands", sent[0])

    def test_help_word_triggers_help(self):
        message, _ = self.run_bot_commands("@bot help")
        sent = [call.args[0] for call in message.channel.send.await_args_list]
        self.assertEqual(len(sent), 1)
        self.assertIn("Karma Bot Commands", sent[0])

    def test_top_triggers_leaderboard_once(self):
        top = [FakeUser("alice", 5)]
        bottom = [FakeUser("bob", -1)]
        message = make_bot_message("@bot top")
        fake_leaderboard = AsyncMock(return_value=(top, bottom))
        with patch.object(karmabot, "ENABLE_LEADERBOARD", True), patch.object(
            karmabot, "get_leaderboard_by_guild", fake_leaderboard
        ):
            asyncio.run(karmabot.bot_commands(message))

        fake_leaderboard.assert_awaited_once()
        sent = [call.args[0] for call in message.channel.send.await_args_list]
        self.assertEqual(len(sent), 2)
        self.assertIn("please wait", sent[0])
        self.assertIn("Top Users", sent[1])
        self.assertIn("alice", sent[1])
        self.assertNotIn("bob", sent[1])

    def test_bottom_triggers_leaderboard_once(self):
        top = [FakeUser("alice", 5)]
        bottom = [FakeUser("bob", -1)]
        message = make_bot_message("@bot bottom")
        fake_leaderboard = AsyncMock(return_value=(top, bottom))
        with patch.object(karmabot, "ENABLE_LEADERBOARD", True), patch.object(
            karmabot, "get_leaderboard_by_guild", fake_leaderboard
        ):
            asyncio.run(karmabot.bot_commands(message))

        fake_leaderboard.assert_awaited_once()
        sent = [call.args[0] for call in message.channel.send.await_args_list]
        self.assertEqual(len(sent), 2)
        self.assertIn("Bottom Users", sent[1])
        self.assertIn("bob", sent[1])
        self.assertNotIn("alice", sent[1])

    def test_top_and_bottom_together(self):
        top = [FakeUser("alice", 5)]
        bottom = [FakeUser("bob", -1)]
        message = make_bot_message("@bot top and bottom")
        fake_leaderboard = AsyncMock(return_value=(top, bottom))
        with patch.object(karmabot, "ENABLE_LEADERBOARD", True), patch.object(
            karmabot, "get_leaderboard_by_guild", fake_leaderboard
        ):
            asyncio.run(karmabot.bot_commands(message))

        fake_leaderboard.assert_awaited_once()
        sent = [call.args[0] for call in message.channel.send.await_args_list]
        self.assertEqual(len(sent), 3)
        self.assertIn("Top Users", sent[1])
        self.assertIn("Bottom Users", sent[2])


class LeaderboardRowsTests(unittest.TestCase):
    def test_rows_numbered_and_formatted(self):
        users = [FakeUser("alice", 5), FakeUser("bob", 0), FakeUser("carol", -2)]
        rows = _leaderboard_rows(users)
        self.assertTrue(rows[0].startswith("1) "))
        self.assertIn("alice", rows[0])
        self.assertIn("+5", rows[0])
        self.assertNotIn("+0", rows[1])
        self.assertIn("0", rows[1])
        self.assertIn("-2", rows[2])


class ChunkLeaderboardTests(unittest.TestCase):
    def test_short_list_single_message(self):
        rows = [f"{i}) {'user' + 'x' * 10:<20} {i:>5}" for i in range(1, 6)]
        chunks = _chunk_leaderboard("🏆 **Top Users:**", rows)
        self.assertEqual(len(chunks), 1)
        for i, row in enumerate(rows, start=1):
            self.assertIn(f"{i})", chunks[0])

    def test_all_messages_under_limit(self):
        rows = [f"{i}) {'x' * 19:<20} {i:>5}" for i in range(1, 101)]
        chunks = _chunk_leaderboard("🏆 **Top Users:**", rows)
        self.assertGreater(len(chunks), 1)
        for chunk in chunks:
            self.assertLessEqual(len(chunk), DISCORD_MESSAGE_LIMIT)

    def test_all_rows_preserved_in_order(self):
        rows = [f"row-{i:03d}-" + "x" * (i % 7) for i in range(1, 120)]
        chunks = _chunk_leaderboard("**Bottom Users:**", rows)
        flat = []
        for chunk in chunks:
            body = chunk.split("```\n", 1)[1].rsplit("\n```", 1)[0]
            flat.extend(line for line in body.split("\n") if line)
        self.assertEqual(flat, rows)

    def test_continuation_header(self):
        rows = [f"{i}) {'x' * 19:<20} {i:>5}" for i in range(1, 101)]
        chunks = _chunk_leaderboard("🏆 **Top Users:**", rows)
        self.assertTrue(chunks[0].startswith("🏆 **Top Users:**"))
        self.assertTrue(chunks[1].startswith("🏆 **Top Users:** (continued)"))

    def test_empty_rows(self):
        chunks = _chunk_leaderboard("🏆 **Top Users:**", [])
        self.assertEqual(chunks, ["🏆 **Top Users:**\n_No users found._"])

    def test_single_huge_row_still_sent(self):
        row = "1) " + "x" * 1990
        chunks = _chunk_leaderboard("T:", [row])
        self.assertEqual(len(chunks), 1)
        self.assertIn(row, chunks[0])


if __name__ == "__main__":
    unittest.main()
