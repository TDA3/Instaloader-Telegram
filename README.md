# 🤖 Instagram Downloader Telegram Bot

A Telegram bot that downloads Instagram content (Photos, Videos, Reels, Stories, Profile Pictures) using **Pyrogram** and **Instaloader**, with full session/cookie support for private accounts.

---

## ✨ Features

- 📸 Download single photos and carousel/sidecar posts
- 🎬 Download Reels and Videos
- 📖 Download active Stories from any user
- 🖼 Download HD Profile Pictures
- 📋 Download latest N posts from a profile
- 🔘 Inline keyboard buttons for profile links
- 🔐 Instagram session file support (for private accounts)
- 🐳 Docker support for easy deployment
- 🛡 Admin system with broadcast, stats, and user management
- ⏱ Rate limiting / per-user cooldown
- ⚡ Async design — non-blocking Instaloader calls via `asyncio.to_thread`
- 🌐 Works in both private chats and group chats

---

## 📋 Prerequisites

- Python **3.10+**
- A [Telegram API ID and API Hash](https://my.telegram.org)
- A Telegram Bot Token from [@BotFather](https://t.me/BotFather)
- An Instagram account (for session-based access to private content)

---

## 🚀 Installation

### 1. Clone the repository

```bash
git clone https://github.com/TDA3/Instaloader-Telegram.git
cd Instaloader-Telegram
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure environment variables

```bash
cp .env.example .env
```

Edit `.env` and fill in your credentials:

```env
API_ID=your_api_id_here
API_HASH=your_api_hash_here
BOT_TOKEN=your_bot_token_here
IG_USERNAME=your_ig_username
IG_SESSION_FILE=cookies/session
DOWNLOAD_DIR=downloads

# Admin / access control
ADMIN_ID=your_telegram_user_id
ALLOWED_USERS=
LOG_CHANNEL=0

# Logging
LOG_LEVEL=INFO

# Rate limiting
COOLDOWN_SECONDS=5
```

### 4. Create Instagram session (optional but recommended)

Run the session creator script to log in and save a session file:

```bash
python create_session.py
```

This saves a session to `cookies/session` which the bot uses for authenticated requests.

### 5. Start the bot

```bash
python bot.py
```

---

## 🐳 Docker Deployment

### Using Docker

```bash
docker build -t ig-telegram-bot .
docker run --env-file .env ig-telegram-bot
```

### Using Docker Compose

```bash
docker-compose up -d
```

Docker Compose mounts `cookies/`, `data/`, and `downloads/` as volumes so your session, user data, and downloads persist across container restarts.

---

## 📖 Usage

### Commands

| Command | Description |
|---------|-------------|
| `/start` | Welcome message with usage instructions |
| `/help` | Detailed help text |
| `/pfp username` | Download HD profile picture |
| `/story username` | Download all active stories |
| `/posts username [N]` | Download latest N posts (default 5, max 20) |

### Admin Commands

| Command | Description |
|---------|-------------|
| `/stats` | Show total user count and bot uptime |
| `/users` | Show total user count |
| `/broadcast <message>` | Send a message to all users who have started the bot |

### Paste an Instagram Link

Just paste any Instagram link directly in the chat:

| Link Type | Action |
|-----------|--------|
| `instagram.com/p/xxxxx` | Download post / carousel |
| `instagram.com/reel/xxxxx` | Download reel / video |
| `instagram.com/stories/username` | Download stories |
| `instagram.com/username` | Show inline buttons |

---

## 📁 Project Structure

```
bot.py              # Main Telegram bot (Pyrogram handlers)
ig_downloader.py    # Instaloader wrapper class
config.py           # Configuration via environment variables
create_session.py   # Script to create Instagram session file
requirements.txt    # pip dependencies
Dockerfile          # Docker image definition
docker-compose.yml  # Docker Compose configuration
.gitignore          # Ignored files
.dockerignore       # Docker build ignored files
.env.example        # Example environment variables
README.md           # This file
```

---

## 🔑 Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `API_ID` | Telegram API ID from my.telegram.org | — |
| `API_HASH` | Telegram API Hash from my.telegram.org | — |
| `BOT_TOKEN` | Bot token from @BotFather | — |
| `IG_USERNAME` | Instagram username for session login | — |
| `IG_SESSION_FILE` | Path to the Instaloader session file | `cookies/session` |
| `DOWNLOAD_DIR` | Directory for temporary downloads | `downloads` |
| `ADMIN_ID` | Telegram user ID of the bot admin | `0` |
| `ALLOWED_USERS` | Comma-separated list of allowed user IDs (empty = everyone) | `` |
| `LOG_CHANNEL` | Telegram channel/group ID for activity logging (0 = disabled) | `0` |
| `LOG_LEVEL` | Python logging level | `INFO` |
| `COOLDOWN_SECONDS` | Seconds between requests per user | `5` |

---

## 🔑 How to Get Telegram API ID/Hash

1. Go to [https://my.telegram.org](https://my.telegram.org)
2. Log in with your Telegram phone number
3. Click **API development tools**
4. Create an application and copy `api_id` and `api_hash`

## 🤖 How to Get a Bot Token

1. Open [@BotFather](https://t.me/BotFather) on Telegram
2. Send `/newbot` and follow the prompts
3. Copy the token provided

---

## ⚠️ Notes

- **Rate Limiting**: Instagram may throttle requests. Wait a few minutes between bulk downloads.
- **Private Accounts**: You must follow the account and have a valid session file.
- **Session Expiry**: If the session expires, re-run `create_session.py`.
- **File Size**: Files larger than 50 MB are sent as documents.

---

## 📜 License

MIT License
