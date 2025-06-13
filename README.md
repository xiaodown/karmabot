# KarmaBot

**KarmaBot** is a Discord bot that tracks and manages user karma in your server. Users can give or take karma from each other by mentioning users and using sequences of `+` or `-` symbols (e.g., `@user ++` or `@user --`). The bot stores karma in a local SQLite database.

---

## Features

- Give or take karma by mentioning users and using `+` or `-`
- Query a user's karma with `@user karma`
- "Buzzkill mode" caps karma changes per message to prevent abuse (configurable)
- **Spam protection:** Users can only have their karma changed once every 15 seconds (configurable)
- **Self-karma prevention:** Users cannot give themselves karma
- Persistent storage using SQLite
- Clean, maintainable codebase (better than my average at least)

---

## Installation

1. **Clone the repository:**
    ```bash
    git clone https://github.com/yourusername/karmabot.git
    cd karmabot
    ```

2. **Create a virtual environment using [uv](https://github.com/astral-sh/uv):**
    ```bash
    uv venv
    ```

3. **Install dependencies:**
    ```bash
    uv pip install -r requirements.txt
    ```

4. **Set up your Discord bot:**
    - Go to the [Discord Developer Portal](https://discord.com/developers/applications).
    - Create a new application and add a bot to it.
    - Under the "Bot" settings, enable the following intents:
        - **SERVER MEMBERS INTENT**
        - **MESSAGE CONTENT INTENT**
    - Copy your bot's token and save it in a file named `discordapikey.txt` in the project root (the file should contain only the token).

5. **Invite the bot to your server:**
    - In the Developer Portal, go to the "OAuth2" > "URL Generator".
    - Under "Scopes", select `bot`.
    - Under "Bot Permissions", select the permissions your bot needs (at minimum: `Send Messages` and `Read Message History`).
    - Copy the generated URL, open it in your browser, and invite the bot to your server.  
      **Note:** You must be a server admin to invite bots.

---

## Running the Bot

1. **Activate your virtual environment:**
    ```bash
    source .venv/bin/activate
    ```

2. **Start the bot:**
    ```bash
    python ./karmabot.py
    ```

The bot should now be running and listening for messages in your Discord server.

---

## Usage

- **Give karma:**  
  `@username ++` (adds 2 karma to username)  
  `@username --` (removes 2 karma from username)

- **Check karma:**  
  `@username karma`

## Abuse Prevention

- **Buzzkill mode:**  
  Karma changes are capped at **+5** and **-2** per message (configurable in `settings.py`).

- **Spam protection:**  
  Users can only have their karma changed once every configurable interval (default: 15 seconds, set in `settings.py`).

- **Self-karma prevention:**  
  Users cannot give themselves karma.

---

## Notes

- Make sure your bot has permission to read messages and see members in the channels you want it to operate in.
- Due to Discord's markdown, three or more consecutive dashes (`---`) after a mention may not work as expected (interpreted as a Markdown horizontal line). Recommend keeping BUZZKILL_NEGATIVE_MAX at 2.

---

## License

GPL v3. See [LICENSE](LICENSE)
