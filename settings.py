""" Settings for Karmabot """

SQLITE_DB = 'db.sqlite3'
DISCORD_API_KEY_FILE = 'discord_api_key.txt'


def load_api_key(api_key_file_path):
    """Loads your discord API key from a file, 
       mainly so it's not checked into version control."""
    try:
        with open(api_key_file_path, 'r', encoding='utf-8') as file:
            return file.read().strip()
    except FileNotFoundError as exc:
        raise FileNotFoundError(f"API key file '{api_key_file_path}' not found.") from exc
    except Exception as e:
        raise OSError(f"An error occurred while loading the API key: {e}") from e

discord_api_key = load_api_key(DISCORD_API_KEY_FILE)
