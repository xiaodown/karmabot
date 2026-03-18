"""Create or migrate the SQLite schema used by Karmabot."""

from db import KarmaDatabase


if __name__ == "__main__":
    db = KarmaDatabase()
    print(f"Database schema is ready at {db.db_path}")
