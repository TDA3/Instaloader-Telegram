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
- 🇲🇲 Bot messages in Myanmar/Burmese language
- ⚡ Async design — non-blocking Instaloader calls via `asyncio.to_thread`

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

## 📖 Usage

### Commands

| Command | Description |
|---------|-------------|
| `/start` | Welcome message with usage instructions |
| `/help` | Detailed help text |
| `/pfp username` | Download HD profile picture |
| `/story username` | Download all active stories |
| `/posts username [N]` | Download latest N posts (default 5, max 20) |

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
.gitignore          # Ignored files
.env.example        # Example environment variables
README.md           # This file
```

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

---

---

# 🇲🇲 မြန်မာဘာသာ — ထည့်သွင်းနည်း

## 📋 လိုအပ်သောအရာများ

- Python **3.10+**
- [Telegram API ID နှင့် API Hash](https://my.telegram.org)
- [@BotFather](https://t.me/BotFather) မှ Bot Token
- Instagram Account (private account များအတွက်)

## 🚀 ထည့်သွင်းနည်း

### 1. Repository clone လုပ်ရန်

```bash
git clone https://github.com/TDA3/Instaloader-Telegram.git
cd Instaloader-Telegram
```

### 2. Dependencies ထည့်ရန်

```bash
pip install -r requirements.txt
```

### 3. Environment Variables ပြင်ဆင်ရန်

```bash
cp .env.example .env
```

`.env` ဖိုင်ကို ဖွင့်ပြီး credentials ထည့်ပေးပါ:

```env
API_ID=သင်၏_api_id
API_HASH=သင်၏_api_hash
BOT_TOKEN=သင်၏_bot_token
IG_USERNAME=သင်၏_ig_username
IG_SESSION_FILE=cookies/session
DOWNLOAD_DIR=downloads
```

### 4. Instagram Session ဖန်တီးရန် (optional)

```bash
python create_session.py
```

### 5. Bot စတင်ရန်

```bash
python bot.py
```

## 📖 Commands

| Command | ရှင်းလင်းချက် |
|---------|--------------|
| `/start` | ကြိုဆိုသည့် message |
| `/help` | အသေးစိတ် အကူအညီ |
| `/pfp username` | Profile picture download |
| `/story username` | Stories download |
| `/posts username [N]` | Latest posts download |

## ⚠️ မှတ်ချက်များ

- **Rate Limiting**: Instagram က request များကို ကန့်သတ်ပါသည်။ Bulk download များအတွက် ခဏစောင့်ပေးပါ။
- **Private Accounts**: Account follow လုပ်ထားပြီး session file ရှိရမည်။
- **Session Expired**: Session ကုန်သွားပါက `create_session.py` ကို ပြန် run ပေးပါ။
