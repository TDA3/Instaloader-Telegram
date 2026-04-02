import asyncio
import os

from pyrogram import Client, filters
from pyrogram.types import (
    Message,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    CallbackQuery,
)

from config import API_ID, API_HASH, BOT_TOKEN
from ig_downloader import IGDownloader

# ---------------------------------------------------------------------------
# Bot client
# ---------------------------------------------------------------------------
app = Client("instagram_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# Shared downloader instance (created once at startup)
ig = IGDownloader()

# ---------------------------------------------------------------------------
# Message templates (Myanmar / Burmese)
# ---------------------------------------------------------------------------
START_TEXT = """
🤖 **Instagram Downloader Bot မှ ကြိုဆိုပါသည်!**

ဒီ Bot က Instagram မှ Photos, Videos, Reels, Stories နဲ့ Profile Pictures များကို Download လုပ်ပေးပါသည်။

**📌 အသုံးပြုနည်း:**
• Instagram link တစ်ခုကို paste လုပ်ပေးရုံပဲ၊ Bot က အလိုအလျောက် Download လုပ်ပေးမည်။

**📋 Commands များ:**
• `/start` — ကြိုဆိုသည့် message
• `/help` — အသုံးပြုနည်း အသေးစိတ်
• `/pfp username` — Profile Picture download
• `/story username` — Active Stories download
• `/posts username [ပမာဏ]` — Latest posts download (default 5, max 20)

**🔗 Support လုပ်သော Links:**
• `instagram.com/p/xxxx` — Photos / Carousels
• `instagram.com/reel/xxxx` — Reels / Videos
• `instagram.com/stories/username` — Stories
• `instagram.com/username` — Profile (buttons ပေါ်လာမည်)

⚠️ Private accounts များအတွက် session file လိုအပ်ပါသည်။
"""

HELP_TEXT = """
ℹ️ **Instagram Downloader Bot — အကူအညီ**

**Commands:**

🖼 `/pfp username`
Profile picture (HD) download လုပ်ရန်
ဥပမာ: `/pfp natalie_portman`

📖 `/story username`
User ၏ active stories အားလုံး download လုပ်ရန်
ဥပမာ: `/story natalie_portman`

📸 `/posts username [ပမာဏ]`
Latest posts download လုပ်ရန် (default 5, max 20)
ဥပမာ: `/posts natalie_portman 10`

🔗 **Link Paste:**
Instagram link တစ်ခုကို chat ထဲ paste လုပ်ပေးရုံနဲ့ Bot က အလိုအလျောက် download လုပ်ပေးမည်။
• Post/Reel link → media file(s) ပေးပို့မည်
• Stories link → stories file(s) ပေးပို့မည်
• Profile link → buttons ပေါ်လာမည် (Profile Pic / Stories / Posts)

⚠️ **မှတ်ချက်များ:**
• Private account များ access လုပ်ရန် session file လိုပါသည်။
• IG rate limiting ကြောင့် တစ်ခါတစ်ရံ ခဏစောင့်ပေးပါ။
• Session expired ဖြစ်ပါက `create_session.py` ကို ပြန်run ပေးပါ။
"""

# ---------------------------------------------------------------------------
# /start
# ---------------------------------------------------------------------------
@app.on_message(filters.command("start") & filters.private)
async def cmd_start(client: Client, message: Message):
    await message.reply_text(START_TEXT)


# ---------------------------------------------------------------------------
# /help
# ---------------------------------------------------------------------------
@app.on_message(filters.command("help") & filters.private)
async def cmd_help(client: Client, message: Message):
    await message.reply_text(HELP_TEXT)


# ---------------------------------------------------------------------------
# /pfp username
# ---------------------------------------------------------------------------
@app.on_message(filters.command("pfp") & filters.private)
async def cmd_pfp(client: Client, message: Message):
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        await message.reply_text("❌ Username ထည့်ပေးပါ။\nဥပမာ: `/pfp username`")
        return

    username = args[1].strip().lstrip("@")
    status = await message.reply_text(f"⏳ @{username} ၏ profile picture download လုပ်နေသည်…")

    result = await asyncio.to_thread(ig.download_profile_pic, username)
    await _send_results(client, message, status, result)


# ---------------------------------------------------------------------------
# /story username
# ---------------------------------------------------------------------------
@app.on_message(filters.command("story") & filters.private)
async def cmd_story(client: Client, message: Message):
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        await message.reply_text("❌ Username ထည့်ပေးပါ။\nဥပမာ: `/story username`")
        return

    username = args[1].strip().lstrip("@")
    status = await message.reply_text(f"⏳ @{username} ၏ stories download လုပ်နေသည်…")

    url = f"https://www.instagram.com/stories/{username}/"
    result = await asyncio.to_thread(ig.download_stories, url)
    await _send_results(client, message, status, result)


# ---------------------------------------------------------------------------
# /posts username [limit]
# ---------------------------------------------------------------------------
@app.on_message(filters.command("posts") & filters.private)
async def cmd_posts(client: Client, message: Message):
    args = message.text.split()
    if len(args) < 2:
        await message.reply_text("❌ Username ထည့်ပေးပါ။\nဥပမာ: `/posts username 10`")
        return

    username = args[1].strip().lstrip("@")
    limit = 5
    if len(args) >= 3:
        try:
            limit = int(args[2])
        except ValueError:
            pass

    limit = max(1, min(limit, 20))
    status = await message.reply_text(f"⏳ @{username} ၏ posts {limit} ခု download လုပ်နေသည်…")

    result = await asyncio.to_thread(ig.download_profile_posts, username, limit)
    await _send_results(client, message, status, result)


# ---------------------------------------------------------------------------
# Auto-detect Instagram links
# ---------------------------------------------------------------------------
@app.on_message(
    filters.regex(r"(https?://)?(www\.)?instagram\.com/") & filters.private
)
async def handle_ig_link(client: Client, message: Message):
    url = message.text.strip()

    # Normalize URL
    if not url.startswith("http"):
        url = "https://" + url

    if "/stories/" in url:
        status = await message.reply_text("⏳ Stories download လုပ်နေသည်…")
        result = await asyncio.to_thread(ig.download_stories, url)
        await _send_results(client, message, status, result)

    elif any(seg in url for seg in ["/p/", "/reel/", "/reels/", "/tv/"]):
        status = await message.reply_text("⏳ Post/Reel download လုပ်နေသည်…")
        result = await asyncio.to_thread(ig.download_post, url)
        await _send_results(client, message, status, result)

    else:
        # Profile link — show inline keyboard
        username = ig._extract_username(url)
        if not username:
            await message.reply_text("❌ Username ရှာမတွေ့ပါ။ Link ကို စစ်ဆေးပြီး ထပ်ကြိုးစားပါ။")
            return

        keyboard = InlineKeyboardMarkup(
            [
                [InlineKeyboardButton("🖼 Profile Picture", callback_data=f"pfp:{username}")],
                [InlineKeyboardButton("📖 Stories", callback_data=f"stories:{username}")],
                [
                    InlineKeyboardButton("📸 Latest 5 Posts", callback_data=f"posts5:{username}"),
                    InlineKeyboardButton("📸 Latest 10 Posts", callback_data=f"posts10:{username}"),
                ],
            ]
        )
        await message.reply_text(
            f"📌 **@{username}** ၏ profile detect လုပ်မိသည်။\nဘာ download လုပ်ချင်သနည်း?",
            reply_markup=keyboard,
        )


# ---------------------------------------------------------------------------
# Callback query handler (inline buttons)
# ---------------------------------------------------------------------------
@app.on_callback_query()
async def handle_callback(client: Client, query: CallbackQuery):
    data = query.data
    await query.answer()

    if ":" not in data:
        return

    action, username = data.split(":", 1)

    if action == "pfp":
        status = await query.message.reply_text(f"⏳ @{username} ၏ profile picture download လုပ်နေသည်…")
        result = await asyncio.to_thread(ig.download_profile_pic, username)
        await _send_results(client, query.message, status, result)

    elif action == "stories":
        status = await query.message.reply_text(f"⏳ @{username} ၏ stories download လုပ်နေသည်…")
        url = f"https://www.instagram.com/stories/{username}/"
        result = await asyncio.to_thread(ig.download_stories, url)
        await _send_results(client, query.message, status, result)

    elif action in ("posts5", "posts10"):
        limit = 5 if action == "posts5" else 10
        status = await query.message.reply_text(f"⏳ @{username} ၏ posts {limit} ခု download လုပ်နေသည်…")
        result = await asyncio.to_thread(ig.download_profile_posts, username, limit)
        await _send_results(client, query.message, status, result)


# ---------------------------------------------------------------------------
# Helper: send downloaded files back to the user
# ---------------------------------------------------------------------------
MAX_TELEGRAM_SIZE = 50 * 1024 * 1024  # 50 MB


async def _send_results(
    client: Client,
    message: Message,
    status: Message,
    result: dict,
):
    if not result.get("success"):
        error = result.get("error", "Unknown error")
        await status.edit_text(f"❌ Download မအောင်မြင်ပါ:\n`{error}`")
        return

    files = result.get("files", [])
    caption = result.get("caption", "")
    target_dir = result.get("target")

    if not files:
        await status.edit_text("❌ Files ရှာမတွေ့ပါ။")
        if target_dir:
            ig._cleanup(target_dir)
        return

    await status.edit_text(f"📤 {len(files)} file(s) ပို့နေသည်…")

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
        except Exception as e:
            await message.reply_text(f"❌ File ပို့ရန် မအောင်မြင်ပါ: `{e}`")

    await status.delete()

    if target_dir:
        ig._cleanup(target_dir)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    print("Bot starting…")
    app.run()
