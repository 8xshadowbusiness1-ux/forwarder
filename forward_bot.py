import os
import json
import threading
import time
import requests
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters
)

# ==============================
# CONFIG
# ==============================
BOT_TOKEN = "7366502402:AAEij4_HcMkycR5-KxO2BBSd91026Cv_LbU"
OWNER_ID = 1602198875
SERVER_URL = "https://forwarder-c46l.onrender.com"
CHANNELS_FILE = "channels.json"

if not os.path.exists(CHANNELS_FILE):
    with open(CHANNELS_FILE, "w") as f:
        json.dump([], f)

with open(CHANNELS_FILE, "r") as f:
    channels = json.load(f)

# ==============================
# BUTTONS
# ==============================
def main_buttons():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("➕ Add Channel", callback_data="add_channel")],
        [InlineKeyboardButton("➖ Remove Channel", callback_data="remove_channel")],
        [InlineKeyboardButton("📃 List Channels", callback_data="list_channels")],
        [InlineKeyboardButton("📨 Test Forward", callback_data="test_forward")],
        [InlineKeyboardButton("📊 Bot Status", callback_data="bot_status")],
        [InlineKeyboardButton("👤 Owner Info", callback_data="owner_info")]
    ])

# ==============================
# START COMMAND
# ==============================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        await update.message.reply_text("❌ You are not authorized to use this bot.")
        return
    await update.message.reply_text("👋 Welcome Boss! Bot is ready.", reply_markup=main_buttons())

# ==============================
# BUTTON HANDLER
# ==============================
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    await query.answer()

    if user_id != OWNER_ID:
        await query.message.reply_text("❌ You are not authorized.")
        return

    if query.data == "add_channel":
        context.user_data["mode"] = "add"
        await query.message.reply_text("Send channel username to add (e.g. @example)")
    elif query.data == "remove_channel":
        context.user_data["mode"] = "remove"
        await query.message.reply_text("Send channel username to remove.")
    elif query.data == "list_channels":
        if channels:
            msg = "\n".join(f"🔹 {c}" for c in channels)
            await query.message.reply_text(f"📃 Channel List:\n{msg}", reply_markup=main_buttons())
        else:
            await query.message.reply_text("⚠️ No channels added yet.", reply_markup=main_buttons())
    elif query.data == "test_forward":
        for ch in channels:
            try:
                await context.bot.send_message(ch, "✅ Test message from Forwarder Bot!")
            except Exception as e:
                await query.message.reply_text(f"❌ Failed for {ch}: {e}")
        await query.message.reply_text("📨 Test sent!", reply_markup=main_buttons())
    elif query.data == "bot_status":
        await query.message.reply_text(
            f"📊 Bot is running\nChannels: {len(channels)}\nPing every 5 min.",
            reply_markup=main_buttons()
        )
    elif query.data == "owner_info":
        await query.message.reply_text(
            f"👤 Owner ID: {OWNER_ID}\n💬 Contact: Vishal",
            reply_markup=main_buttons()
        )

# ==============================
# MESSAGE HANDLER
# ==============================
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
            await update.message.reply_text(f"✅ Added {text}", reply_markup=main_buttons())
        else:
            await update.message.reply_text("⚠️ Already exists.", reply_markup=main_buttons())
        context.user_data["mode"] = None

    elif mode == "remove":
        if text in channels:
            channels.remove(text)
            with open(CHANNELS_FILE, "w") as f:
                json.dump(channels, f)
            await update.message.reply_text(f"❌ Removed {text}", reply_markup=main_buttons())
        else:
            await update.message.reply_text("⚠️ Not found.", reply_markup=main_buttons())
        context.user_data["mode"] = None

    else:
        for ch in channels:
            try:
                await context.bot.forward_message(
                    chat_id=ch,
                    from_chat_id=update.message.chat_id,
                    message_id=update.message.message_id
                )
            except Exception as e:
                await update.message.reply_text(f"⚠️ Error forwarding to {ch}: {e}")

# ==============================
# FLASK KEEP-ALIVE
# ==============================
flask_app = Flask(__name__)

@flask_app.route('/')
def home():
    return "✅ Bot Alive"

def run_flask():
    flask_app.run(host="0.0.0.0", port=10000)

def keep_alive():
    while True:
        try:
            res = requests.get(SERVER_URL)
            print(f"🌍 Ping {SERVER_URL} — {res.status_code}")
        except:
            pass
        time.sleep(300)

# ==============================
# MAIN FUNCTION
# ==============================
def start_bot():
    application = ApplicationBuilder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button_handler))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("✅ Bot running 24×7...")

    application.run_polling(stop_signals=None)

# ==============================
# EXECUTION
# ==============================
if __name__ == "__main__":
    threading.Thread(target=run_flask).start()
    threading.Thread(target=keep_alive).start()
    start_bot()
