---
name: run-tests
description: Use when the user asks to run tests, check whether tests pass, run a specific test module, or add/fix tests in the karmabot repo.
user-invocable: true
---

# Karmabot Test Runner

How to run and extend the Karmabot test suite.

## Running tests

The repo ships a single entry point that handles interpreter and runner
selection for you. Always use it instead of invoking pytest/unittest
directly:

```sh
python3 run_tests.py                 # full suite
python3 run_tests.py test_db         # only test modules matching "test_db"
```

The runner (repo root `run_tests.py`):

- Prefers `.venv/bin/python` if the project virtualenv exists, else the
  current interpreter.
- Prefers pytest if the chosen interpreter has it, else falls back to the
  stdlib `unittest` discover runner. `pytest` is a declared dependency in
  `requirements.txt`, so a normal install uses pytest; the unittest
  fallback keeps the suite runnable in a bare interpreter.
- Sets `PYTHONPATH` to the repo root and runs from the repo root, so tests
  import `db`, `karmabot`, etc. without packaging.
- Exits nonzero on failure (CI-friendly).

## Test layout

```
tests/
  test_db.py          KarmaDatabase layer (temp sqlite files, no network)
  test_commands.py    command regexes + leaderboard chunking + bot_commands
                      integration via AsyncMock (no network)
  test_leaderboard.py get_leaderboard_by_guild against a temp database
```

Conventions:

- `unittest` style classes (`unittest.TestCase`), one file per module.
- Every test gets a throwaway database via `tempfile.TemporaryDirectory()`
  in `setUp` and cleanup in `tearDown`. Never touch the real `db.sqlite3`.
- `karmabot.py` is importable in tests (module level only builds a
  `discord.Client`, no network). `bot_commands` is tested by mocking
  `message.channel.send` with `AsyncMock` and patching
  `karmabot.get_leaderboard_by_guild`.
- `tests/` has no `__init__.py`; `unittest discover` and pytest both find
  it from the repo root.

## Adding tests

1. Put the file in `tests/` named `test_<module>.py`.
2. Import project modules at top level (the runner sets `PYTHONPATH`).
3. For DB tests, construct `KarmaDatabase(os.path.join(self._tmp.name, "test.sqlite3"))`.
   Remember the `user_nicknames.guild_id` FK: upsert the guild before
   upserting nicknames.
4. Run `python3 run_tests.py <your_module>` first, then the full suite.

## Do not

- Do not run the actual bot (`python3 karmabot.py`) to "test" it; it
  connects to the live Discord gateway.
- Do not remove the stdlib `unittest` fallback from `run_tests.py`; the
  suite must keep running in an interpreter without pytest.
