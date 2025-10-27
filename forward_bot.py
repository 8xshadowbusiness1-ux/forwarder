import os
import json
import threading
import time
import requests
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
    ContextTypes,
)

# ====== CONFIG ======
BOT_TOKEN = os.getenv("BOT_TOKEN", "PASTE_YOUR_BOT_TOKEN_HERE")
OWNER_ID = 1602198875
CHANNELS_FILE = "channels.json"

# ====== FLASK SERVER ======
flask_app = Flask(__name__)

@flask_app.route("/")
def home():
    return "✅ Vishal Forwarder Bot is alive and running 24x7!"

def run_flask():
    flask_app.run(host="0.0.0.0", port=10000)

# ====== KEEP-ALIVE PING ======
def keep_alive_ping():
    url = "https://forwarder-c46l.onrender.com"  # 👈 Replace with your Render URL
    while True:
        try:
            r = requests.get(url)
            print(f"🌍 Pinged {url} | Status:", r.status_code)
        except Exception as e:
            print("⚠️ Ping failed:", e)
        time.sleep(300)  # every 5 min

# ====== CHANNEL FILE ======
if os.path.exists(CHANNELS_FILE):
    with open(CHANNELS_FILE, "r") as f:
        channels = json.load(f)
else:
    channels = []
    with open(CHANNELS_FILE, "w") as f:
        json.dump(channels, f)

# ====== BUTTONS ======
def main_buttons():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("➕ Add Channel", callback_data="add_channel")],
        [InlineKeyboardButton("➖ Remove Channel", callback_data="remove_channel")],
        [InlineKeyboardButton("📃 List Channels", callback_data="list_channels")]
    ])

# ====== START ======
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        await update.message.reply_text("❌ You are not authorized.")
        return
    await update.message.reply_text(
        "Welcome! Manage your channels below.",
        reply_markup=main_buttons()
    )

# ====== BUTTON HANDLER ======
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id

    if user_id != OWNER_ID:
        await query.message.reply_text("❌ Unauthorized.")
        return

    if query.data == "add_channel":
        context.user_data["mode"] = "add"
        await query.message.reply_text("Send channel username to add (e.g. @channel)")
    elif query.data == "remove_channel":
        context.user_data["mode"] = "remove"
        await query.message.reply_text("Send channel username to remove (e.g. @channel)")
    elif query.data == "list_channels":
        if channels:
            await query.message.reply_text("📃 Channels:\n" + "\n".join(channels))
        else:
            await query.message.reply_text("No channels yet.")

# ====== MESSAGE HANDLER ======
async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text.strip()

    if user_id != OWNER_ID:
        return

    mode = context.user_data.get("mode")

    if mode == "add":
        if text not in channels:
            channels.append(text)
            with open(CHANNELS_FILE, "w") as f:
                json.dump(channels, f)
            await update.message.reply_text(f"✅ Added {text}")
        else:
            await update.message.reply_text("⚠️ Already exists.")
        context.user_data["mode"] = None

    elif mode == "remove":
        if text in channels:
            channels.remove(text)
            with open(CHANNELS_FILE, "w") as f:
                json.dump(channels, f)
            await update.message.reply_text(f"❌ Removed {text}")
        else:
            await update.message.reply_text("⚠️ Not found.")
        context.user_data["mode"] = None
    else:
        if not channels:
            await update.message.reply_text("⚠️ No channels added yet.")
            return
        for ch in channels:
            try:
                await context.bot.forward_message(
                    chat_id=ch,
                    from_chat_id=update.message.chat_id,
                    message_id=update.message.message_id
                )
            except Exception as e:
                print(f"Error forwarding to {ch}: {e}")

# ====== MAIN RUN ======
async def main():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    print("✅ Vishal Forwarder Bot started successfully.")
    await app.run_polling()

if __name__ == "__main__":
    threading.Thread(target=run_flask).start()
    threading.Thread(target=keep_alive_ping).start()
    import asyncio
    asyncio.run(main())
