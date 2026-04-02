import asyncio
import json
import logging
import os
import time

from pyrogram import Client, filters
from pyrogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)

from config import (
    ADMIN_ID,
    ALLOWED_USERS,
    API_HASH,
    API_ID,
    BOT_TOKEN,
    COOLDOWN_SECONDS,
    LOG_CHANNEL,
    LOG_LEVEL,
)
from ig_downloader import IGDownloader

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=getattr(logging, LOG_LEVEL.upper(), logging.INFO),
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Bot client
# ---------------------------------------------------------------------------
app = Client("instagram_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# Shared downloader instance (created once at startup)
ig = IGDownloader()

# Per-user cooldown tracking: {user_id: last_request_timestamp}
user_cooldowns: dict[int, float] = {}

# Bot start time for uptime tracking
_start_time = time.time()

# Users data file
USERS_FILE = "data/users.json"
os.makedirs("data", exist_ok=True)

# ---------------------------------------------------------------------------
# Message templates (English)
# ---------------------------------------------------------------------------
START_TEXT = """
🤖 **Instagram Downloader Bot**

I can download Instagram Photos, Videos, Reels, Stories, and Profile Pictures for you!

**📌 How to use:**
• Just paste any Instagram link and I'll download it automatically.

**📋 Commands:**
• `/start` — Welcome message
• `/help` — Detailed usage instructions
• `/pfp username` — Download HD profile picture
• `/story username` — Download active stories
• `/posts username [N]` — Download latest N posts (default 5, max 20)

**🔗 Supported links:**
• `instagram.com/p/xxxx` — Photos / Carousels
• `instagram.com/reel/xxxx` — Reels / Videos
• `instagram.com/stories/username` — Stories
• `instagram.com/username` — Profile (shows option buttons)

⚠️ A session file is required for private accounts.
"""

HELP_TEXT = """
ℹ️ **Instagram Downloader Bot — Help**

**Commands:**

🖼 `/pfp username`
Download the HD profile picture of a user.
Example: `/pfp natalie_portman`

📖 `/story username`
Download all active stories of a user.
Example: `/story natalie_portman`

📸 `/posts username [N]`
Download the latest N posts (default 5, max 20).
Example: `/posts natalie_portman 10`

🔗 **Paste a link:**
Paste any Instagram link directly in the chat and the bot will download it automatically.
• Post/Reel link → sends media file(s)
• Stories link → sends story file(s)
• Profile link → shows option buttons (Profile Pic / Stories / Posts)

⚠️ **Notes:**
• A session file is required to access private accounts.
• Instagram may throttle requests — please wait a moment between bulk downloads.
• If the session expires, re-run `create_session.py`.
"""


# ---------------------------------------------------------------------------
# User tracking helpers
# ---------------------------------------------------------------------------
def _load_users() -> set[int]:
    if os.path.exists(USERS_FILE):
        try:
            with open(USERS_FILE, "r") as f:
                data = json.load(f)
                return set(data.get("users", []))
        except (json.JSONDecodeError, IOError, OSError) as e:
            logger.error("Failed to load users file: %s", e)
    return set()


def _save_users(users: set[int]) -> None:
    try:
        with open(USERS_FILE, "w") as f:
            json.dump({"users": list(users)}, f)
    except Exception as e:
        logger.error("Failed to save users file: %s", e)


def _track_user(user_id: int) -> None:
    users = _load_users()
    if user_id not in users:
        users.add(user_id)
        _save_users(users)


# ---------------------------------------------------------------------------
# Authorization / cooldown helpers
# ---------------------------------------------------------------------------
def is_authorized(user_id: int) -> bool:
    if not ALLOWED_USERS:
        return True
    return user_id in ALLOWED_USERS or user_id == ADMIN_ID


def _check_cooldown(user_id: int) -> float:
    """Return remaining cooldown seconds (0 if none)."""
    if user_id == ADMIN_ID:
        return 0.0
    last = user_cooldowns.get(user_id, 0.0)
    elapsed = time.time() - last
    remaining = COOLDOWN_SECONDS - elapsed
    return max(remaining, 0.0)


def _update_cooldown(user_id: int) -> None:
    user_cooldowns[user_id] = time.time()


# ---------------------------------------------------------------------------
# Log channel helper
# ---------------------------------------------------------------------------
async def _log_to_channel(client: Client, text: str) -> None:
    if LOG_CHANNEL:
        try:
            await client.send_message(LOG_CHANNEL, text)
        except Exception as e:
            logger.warning("Failed to send log to channel: %s", e)


# ---------------------------------------------------------------------------
# /start
# ---------------------------------------------------------------------------
@app.on_message(filters.command("start"))
async def cmd_start(client: Client, message: Message):
    user_id = message.from_user.id
    _track_user(user_id)
    logger.info("User %s sent /start", user_id)

    if not is_authorized(user_id):
        await message.reply_text(
            "⚠️ You are not authorized to use this bot. Contact the admin."
        )
        return

    await message.reply_text(START_TEXT)


# ---------------------------------------------------------------------------
# /help
# ---------------------------------------------------------------------------
@app.on_message(filters.command("help"))
async def cmd_help(client: Client, message: Message):
    user_id = message.from_user.id
    if not is_authorized(user_id):
        await message.reply_text(
            "⚠️ You are not authorized to use this bot. Contact the admin."
        )
        return

    await message.reply_text(HELP_TEXT)


# ---------------------------------------------------------------------------
# /pfp username
# ---------------------------------------------------------------------------
@app.on_message(filters.command("pfp"))
async def cmd_pfp(client: Client, message: Message):
    user_id = message.from_user.id
    if not is_authorized(user_id):
        await message.reply_text(
            "⚠️ You are not authorized to use this bot. Contact the admin."
        )
        return

    remaining = _check_cooldown(user_id)
    if remaining > 0:
        await message.reply_text(
            f"⏳ Please wait {remaining:.0f} second(s) before your next request."
        )
        return

    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        await message.reply_text(
            "❌ Please provide a username.\nExample: `/pfp username`"
        )
        return

    username = args[1].strip().lstrip("@")
    _update_cooldown(user_id)
    status = await message.reply_text(
        f"⏳ Downloading profile picture for @{username}..."
    )
    logger.info("User %s requested pfp for @%s", user_id, username)

    result = await asyncio.to_thread(ig.download_profile_pic, username)
    await _send_results(client, message, status, result)
    await _log_to_channel(
        client,
        f"👤 User `{user_id}` downloaded pfp of @{username} — "
        f"{'✅ success' if result.get('success') else '❌ failed'}",
    )


# ---------------------------------------------------------------------------
# /story username
# ---------------------------------------------------------------------------
@app.on_message(filters.command("story"))
async def cmd_story(client: Client, message: Message):
    user_id = message.from_user.id
    if not is_authorized(user_id):
        await message.reply_text(
            "⚠️ You are not authorized to use this bot. Contact the admin."
        )
        return

    remaining = _check_cooldown(user_id)
    if remaining > 0:
        await message.reply_text(
            f"⏳ Please wait {remaining:.0f} second(s) before your next request."
        )
        return

    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        await message.reply_text(
            "❌ Please provide a username.\nExample: `/story username`"
        )
        return

    username = args[1].strip().lstrip("@")
    _update_cooldown(user_id)
    status = await message.reply_text(f"⏳ Downloading stories for @{username}...")
    logger.info("User %s requested stories for @%s", user_id, username)

    url = f"https://www.instagram.com/stories/{username}/"
    result = await asyncio.to_thread(ig.download_stories, url)
    await _send_results(client, message, status, result)
    await _log_to_channel(
        client,
        f"📖 User `{user_id}` downloaded stories of @{username} — "
        f"{'✅ success' if result.get('success') else '❌ failed'}",
    )


# ---------------------------------------------------------------------------
# /posts username [limit]
# ---------------------------------------------------------------------------
@app.on_message(filters.command("posts"))
async def cmd_posts(client: Client, message: Message):
    user_id = message.from_user.id
    if not is_authorized(user_id):
        await message.reply_text(
            "⚠️ You are not authorized to use this bot. Contact the admin."
        )
        return

    remaining = _check_cooldown(user_id)
    if remaining > 0:
        await message.reply_text(
            f"⏳ Please wait {remaining:.0f} second(s) before your next request."
        )
        return

    args = message.text.split()
    if len(args) < 2:
        await message.reply_text(
            "❌ Please provide a username.\nExample: `/posts username 10`"
        )
        return

    username = args[1].strip().lstrip("@")
    limit = 5
    if len(args) >= 3:
        try:
            limit = int(args[2])
        except ValueError:
            pass

    limit = max(1, min(limit, 20))
    _update_cooldown(user_id)
    status = await message.reply_text(
        f"⏳ Downloading {limit} posts from @{username}..."
    )
    logger.info("User %s requested %d posts for @%s", user_id, limit, username)

    result = await asyncio.to_thread(ig.download_profile_posts, username, limit)
    await _send_results(client, message, status, result)
    await _log_to_channel(
        client,
        f"📸 User `{user_id}` downloaded {limit} posts of @{username} — "
        f"{'✅ success' if result.get('success') else '❌ failed'}",
    )


# ---------------------------------------------------------------------------
# /stats (admin only)
# ---------------------------------------------------------------------------
@app.on_message(filters.command("stats"))
async def cmd_stats(client: Client, message: Message):
    user_id = message.from_user.id
    if user_id != ADMIN_ID:
        await message.reply_text(
            "⚠️ You are not authorized to use this bot. Contact the admin."
        )
        return

    users = _load_users()
    uptime_seconds = int(time.time() - _start_time)
    hours, remainder = divmod(uptime_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)

    await message.reply_text(
        f"📊 **Bot Statistics**\n\n"
        f"👥 Total users: `{len(users)}`\n"
        f"⏱ Uptime: `{hours}h {minutes}m {seconds}s`"
    )


# ---------------------------------------------------------------------------
# /users (admin only)
# ---------------------------------------------------------------------------
@app.on_message(filters.command("users"))
async def cmd_users(client: Client, message: Message):
    user_id = message.from_user.id
    if user_id != ADMIN_ID:
        await message.reply_text(
            "⚠️ You are not authorized to use this bot. Contact the admin."
        )
        return

    users = _load_users()
    await message.reply_text(f"👥 Total users: `{len(users)}`")


# ---------------------------------------------------------------------------
# /broadcast (admin only)
# ---------------------------------------------------------------------------
@app.on_message(filters.command("broadcast"))
async def cmd_broadcast(client: Client, message: Message):
    user_id = message.from_user.id
    if user_id != ADMIN_ID:
        await message.reply_text(
            "⚠️ You are not authorized to use this bot. Contact the admin."
        )
        return

    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        await message.reply_text(
            "❌ Please provide a message to broadcast.\n"
            "Example: `/broadcast Hello everyone!`"
        )
        return

    broadcast_text = args[1].strip()
    users = _load_users()
    sent = 0
    failed = 0

    status = await message.reply_text(
        f"📣 Broadcasting to {len(users)} users..."
    )

    for uid in users:
        try:
            await client.send_message(uid, broadcast_text)
            sent += 1
            await asyncio.sleep(0.05)
        except Exception as e:
            logger.warning("Broadcast failed for user %s: %s", uid, e)
            failed += 1

    await status.edit_text(
        f"📣 Broadcast complete!\n✅ Sent: {sent}\n❌ Failed: {failed}"
    )
    logger.info("Broadcast by admin: sent=%d, failed=%d", sent, failed)


# ---------------------------------------------------------------------------
# Auto-detect Instagram links
# ---------------------------------------------------------------------------
@app.on_message(filters.regex(r"(https?://)?(www\.)?instagram\.com/"))
async def handle_ig_link(client: Client, message: Message):
    user_id = message.from_user.id
    if not is_authorized(user_id):
        await message.reply_text(
            "⚠️ You are not authorized to use this bot. Contact the admin."
        )
        return

    remaining = _check_cooldown(user_id)
    if remaining > 0:
        await message.reply_text(
            f"⏳ Please wait {remaining:.0f} second(s) before your next request."
        )
        return

    url = message.text.strip()

    # Normalize URL
    if not url.startswith("http"):
        url = "https://" + url

    if "/stories/" in url:
        _update_cooldown(user_id)
        status = await message.reply_text("⏳ Downloading stories...")
        logger.info("User %s downloading stories from %s", user_id, url)
        result = await asyncio.to_thread(ig.download_stories, url)
        await _send_results(client, message, status, result)
        await _log_to_channel(
            client,
            f"📖 User `{user_id}` downloaded stories from `{url}` — "
            f"{'✅ success' if result.get('success') else '❌ failed'}",
        )

    elif any(seg in url for seg in ["/p/", "/reel/", "/reels/", "/tv/"]):
        _update_cooldown(user_id)
        status = await message.reply_text("⏳ Downloading post/reel...")
        logger.info("User %s downloading post from %s", user_id, url)
        result = await asyncio.to_thread(ig.download_post, url)
        await _send_results(client, message, status, result)
        await _log_to_channel(
            client,
            f"🎬 User `{user_id}` downloaded post from `{url}` — "
            f"{'✅ success' if result.get('success') else '❌ failed'}",
        )

    else:
        # Profile link — show inline keyboard
        username = ig._extract_username(url)
        if not username:
            await message.reply_text(
                "❌ Could not detect a username. Please check the link and try again."
            )
            return

        keyboard = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        "🖼 Profile Picture", callback_data=f"pfp:{username}"
                    )
                ],
                [
                    InlineKeyboardButton(
                        "📖 Stories", callback_data=f"stories:{username}"
                    )
                ],
                [
                    InlineKeyboardButton(
                        "📸 Latest 5 Posts", callback_data=f"posts5:{username}"
                    ),
                    InlineKeyboardButton(
                        "📸 Latest 10 Posts", callback_data=f"posts10:{username}"
                    ),
                ],
            ]
        )
        await message.reply_text(
            f"📌 Profile detected: **@{username}**\nWhat would you like to download?",
            reply_markup=keyboard,
        )


# ---------------------------------------------------------------------------
# Callback query handler (inline buttons)
# ---------------------------------------------------------------------------
@app.on_callback_query()
async def handle_callback(client: Client, query: CallbackQuery):
    user_id = query.from_user.id
    if not is_authorized(user_id):
        await query.answer(
            "⚠️ You are not authorized to use this bot.", show_alert=True
        )
        return

    remaining = _check_cooldown(user_id)
    if remaining > 0:
        await query.answer(
            f"⏳ Please wait {remaining:.0f} second(s) before your next request.",
            show_alert=True,
        )
        return

    data = query.data
    await query.answer()

    if ":" not in data:
        return

    action, username = data.split(":", 1)
    _update_cooldown(user_id)

    if action == "pfp":
        status = await query.message.reply_text(
            f"⏳ Downloading profile picture for @{username}..."
        )
        logger.info("User %s requested pfp for @%s via button", user_id, username)
        result = await asyncio.to_thread(ig.download_profile_pic, username)
        await _send_results(client, query.message, status, result)
        await _log_to_channel(
            client,
            f"👤 User `{user_id}` downloaded pfp of @{username} — "
            f"{'✅ success' if result.get('success') else '❌ failed'}",
        )

    elif action == "stories":
        status = await query.message.reply_text(
            f"⏳ Downloading stories for @{username}..."
        )
        logger.info("User %s requested stories for @%s via button", user_id, username)
        url = f"https://www.instagram.com/stories/{username}/"
        result = await asyncio.to_thread(ig.download_stories, url)
        await _send_results(client, query.message, status, result)
        await _log_to_channel(
            client,
            f"📖 User `{user_id}` downloaded stories of @{username} — "
            f"{'✅ success' if result.get('success') else '❌ failed'}",
        )

    elif action in ("posts5", "posts10"):
        limit = 5 if action == "posts5" else 10
        status = await query.message.reply_text(
            f"⏳ Downloading {limit} posts from @{username}..."
        )
        logger.info(
            "User %s requested %d posts for @%s via button", user_id, limit, username
        )
        result = await asyncio.to_thread(ig.download_profile_posts, username, limit)
        await _send_results(client, query.message, status, result)
        await _log_to_channel(
            client,
            f"📸 User `{user_id}` downloaded {limit} posts of @{username} — "
            f"{'✅ success' if result.get('success') else '❌ failed'}",
        )


# ---------------------------------------------------------------------------
# Helper: send downloaded files back to the user
# ---------------------------------------------------------------------------
MAX_TELEGRAM_SIZE = 50 * 1024 * 1024  # 50 MB


async def _send_results(
    client: Client,
    message: Message,
    status: Message,
    result: dict,
) -> None:
    if not result.get("success"):
        error = result.get("error", "Unknown error")
        logger.error("Download failed: %s", error)
        await status.edit_text(f"❌ Download failed:\n`{error}`")
        return

    files = result.get("files", [])
    caption = result.get("caption", "")
    target_dir = result.get("target")

    if not files:
        await status.edit_text("❌ Download completed but no files were found.")
        if target_dir:
            ig._cleanup(target_dir)
        return

    await status.edit_text(f"📤 Uploading {len(files)} file(s)...")

    for i, file_path in enumerate(files):
        try:
            file_size = os.path.getsize(file_path)
            file_caption = caption if i == 0 else ""

            # Truncate caption to Telegram's limit (1024 chars for media)
            if len(file_caption) > 1000:
                file_caption = file_caption[:997] + "…"

            ext = os.path.splitext(file_path)[1].lower()

            if file_size > MAX_TELEGRAM_SIZE:
                await client.send_document(
                    chat_id=message.chat.id,
                    document=file_path,
                    caption=file_caption,
                    reply_to_message_id=message.id,
                )
            elif ext in (".mp4",):
                await client.send_video(
                    chat_id=message.chat.id,
                    video=file_path,
                    caption=file_caption,
                    reply_to_message_id=message.id,
                )
            else:
                await client.send_photo(
                    chat_id=message.chat.id,
                    photo=file_path,
                    caption=file_caption,
                    reply_to_message_id=message.id,
                )
            logger.info("Sent file: %s", file_path)
        except Exception as e:
            logger.error("Failed to send file %s: %s", file_path, e)
            await message.reply_text(f"❌ Failed to send file: `{e}`")

    await status.delete()

    if target_dir:
        ig._cleanup(target_dir)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    logger.info("Bot starting...")
    app.run()
