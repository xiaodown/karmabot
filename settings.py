"""Settings for Karmabot"""

SQLITE_DB = "db.sqlite3"
DISCORD_API_KEY_FILE = "discordapikey.txt"
BUZZKILL_POSITIVE_MAX = 5
# NOTE: Discord has a known issuer where more than two consecutive
# minuses will be interpreted as a markdown horizontal rule.
# Highly recommend keeping negative buzzkill at 2 to avoid this.
BUZZKILL_NEGATIVE_MAX = 2


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
