"""Settings for Karmabot"""

###  Files used by the bot ###

# Path to the SQLite database file.  Defaults to "db.sqlite3".
# Note that this file will be created if it does not exist.
# Additionally, the filename "db.sqlite3" is in the .gitignore file;
# if you change it, be careful not to check it into version control.
SQLITE_DB = "db.sqlite3"

# Path to the file containing the Discord API key. Defaults to "discordapikey.txt".
# This file should contain only the API key, with no extra whitespace or newlines.
# Additionally, the filename "discordapikey.txt" is in the .gitignore file;
# if you change it, be careful not to check it into version control.
DISCORD_API_KEY_FILE = "discordapikey.txt"


### Buzzkill settings ###

# Buzzkill settings are designed to curtail the more excessive enthusiasm
# of users who might otherwise spam karma adjustments.

# Maximum positive karma adjustment allowed in a single message.
# Defaults to 5
BUZZKILL_POSITIVE_MAX = 5

# Maximum negative karma adjustment allowed in a single message.
# NOTE: Discord has a known issue where more than two consecutive
# minuses will be interpreted as a Markdown horizontal rule.
# Highly recommend keeping negative buzzkill at 2 to avoid this.
# Defaults to 2.
BUZZKILL_NEGATIVE_MAX = 2


### Anti-spam settings ###

# Toggles whether to enforce a delay between karma adjustments.
# This applies to simultaneous users; i.e. if multiple users send @user +++
# within this delay, the user's karma will not be updated.
# This does not apply to one user adjusting multiple users' karma.
# Defaults to True.
ENFORCE_KARMA_SPAM_DELAY = True
# Delay in seconds before a user can adjust karma again.
# Defaults to 15 seconds.
KARMA_SPAM_DELAY = 15  # seconds

# Toggles whether to prevent users from adjusting their own karma.
# Defaults to True.
PREVENT_SELF_KARMA = True

### Leaderboard settings ###

# Toggles whether to enable the leaderboard command.
# Defaults to True.
ENABLE_LEADERBOARD = True

# Number of users to show in the leaderboard.
# Accepted values are integers 1 through 100.
# Will be capped at the number of users for a given server, if that is less than LEADERBOARD_SIZE.
# Defaults to 5.
LEADERBOARD_SIZE = 5


## Utility functions for loading settings, do not adjust ###


def load_api_key(api_key_file_path):
    """Loads your discord API key from a file,
    mainly so it's not checked into version control."""
    try:
        with open(api_key_file_path, "r", encoding="utf-8") as file:
            return file.read().strip()
    except FileNotFoundError as exc:
        raise FileNotFoundError(
            f"API key file '{api_key_file_path}' not found."
        ) from exc
    except Exception as e:
        raise OSError(f"An error occurred while loading the API key: {e}") from e

DISCORD_API_KEY = load_api_key(DISCORD_API_KEY_FILE)
