import os
import json
import time
import threading
import requests
import asyncio
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters
)

# =============================
# ⚙️ CONFIGURATION
# =============================
BOT_TOKEN = "7366502402:AAEij4_HcMkycR5-KxO2BBSd91026Cv_LbU"  # 👈 apna bot token daalna
OWNER_ID = 1602198875              # 👈 apna Telegram user ID daalna
SERVER_URL = "https://forwarder-c46l.onrender.com"  # 👈 apna render ya hosting URL daalna
CHANNELS_FILE = "channels.json"

# =============================
# 💾 CHANNELS FILE SYSTEM
# =============================
if not os.path.exists(CHANNELS_FILE):
    with open(CHANNELS_FILE, "w") as f:
        json.dump([], f)

with open(CHANNELS_FILE, "r") as f:
    channels = json.load(f)

# =============================
# 🔘 MAIN BUTTONS
# =============================
def main_buttons():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("➕ Add Channel", callback_data="add_channel")],
        [InlineKeyboardButton("➖ Remove Channel", callback_data="remove_channel")],
        [InlineKeyboardButton("📃 List Channels", callback_data="list_channels")],
        [InlineKeyboardButton("📨 Forward Test Message", callback_data="test_forward")],
        [InlineKeyboardButton("📊 Bot Status", callback_data="bot_status")],
        [InlineKeyboardButton("👤 Owner Info", callback_data="owner_info")]
    ])

# =============================
# 🧠 CALLBACK HANDLER (BUTTONS)
# =============================
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    await query.answer()

    if user_id != OWNER_ID:
        await query.message.reply_text("❌ You are not authorized to use this bot.")
        return

    if query.data == "add_channel":
        context.user_data["mode"] = "add"
        await query.message.reply_text("✏️ Send me the channel username to **add** (e.g., @examplechannel)")

    elif query.data == "remove_channel":
        context.user_data["mode"] = "remove"
        await query.message.reply_text("🗑️ Send me the channel username to **remove** (e.g., @examplechannel)")

    elif query.data == "list_channels":
        if channels:
            text = "📃 **Channel List:**\n" + "\n".join(f"🔹 {ch}" for ch in channels)
        else:
            text = "⚠️ No channels added yet."
        await query.message.reply_text(text, reply_markup=main_buttons())

    elif query.data == "test_forward":
        if not channels:
            await query.message.reply_text("⚠️ No channels to forward.")
            return
        for ch in channels:
            try:
                await context.bot.send_message(ch, "✅ Test message from Forwarder Bot!")
            except Exception as e:
                await query.message.reply_text(f"❌ Failed to send to {ch}: {e}")
        await query.message.reply_text("📨 Test message sent to all channels.", reply_markup=main_buttons())

    elif query.data == "bot_status":
        total_channels = len(channels)
        text = (
            "📊 **Bot Status**\n"
            f"🟢 Online and running\n"
            f"📡 Connected channels: {total_channels}\n"
            f"🕒 Active ping every 5 minutes\n"
        )
        await query.message.reply_text(text, reply_markup=main_buttons())

    elif query.data == "owner_info":
        text = (
            "👤 **Owner Info**\n"
            "🧑 Owner: Vishal\n"
            f"🆔 Owner ID: {OWNER_ID}\n"
            "💬 Contact via Telegram for queries."
        )
        await query.message.reply_text(text, reply_markup=main_buttons())

# =============================
# 💬 TEXT MESSAGE HANDLER
# =============================
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
            await update.message.reply_text(f"✅ Channel {text} added.", reply_markup=main_buttons())
        else:
            await update.message.reply_text("⚠️ Channel already exists.", reply_markup=main_buttons())
        context.user_data["mode"] = None

    elif mode == "remove":
        if text in channels:
            channels.remove(text)
            with open(CHANNELS_FILE, "w") as f:
                json.dump(channels, f)
            await update.message.reply_text(f"❌ Channel {text} removed.", reply_markup=main_buttons())
        else:
            await update.message.reply_text("⚠️ Channel not found.", reply_markup=main_buttons())
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
                await update.message.reply_text(f"⚠️ Error forwarding to {ch}: {e}")

# =============================
# 🚀 START BUTTON
# =============================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        await update.message.reply_text("❌ You are not authorized to use this bot.")
        return
    await update.message.reply_text("Welcome, Boss 👑", reply_markup=main_buttons())

# =============================
# 🌐 FLASK KEEP-ALIVE SYSTEM
# =============================
flask_app = Flask(__name__)

@flask_app.route('/')
def home():
    return "✅ Bot is alive and running!"

def run_flask():
    flask_app.run(host="0.0.0.0", port=10000)

def keep_alive_ping():
    while True:
        try:
            res = requests.get(SERVER_URL)
            print(f"🌍 Pinged {SERVER_URL} — {res.status_code}")
        except Exception as e:
            print("⚠️ Ping failed:", e)
        time.sleep(300)  # every 5 minutes

# =============================
# 🏁 MAIN FUNCTION
# =============================
async def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app.add_handler(MessageHandler(filters.COMMAND, handle_text))
    app.add_handler(MessageHandler(filters.ALL, handle_text))

    app.add_handler(MessageHandler(filters.COMMAND, handle_text))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app.add_handler(MessageHandler(filters.ALL, handle_text))
    app.add_handler(MessageHandler(filters.TEXT, handle_text))
    app.add_handler(MessageHandler(filters.ALL, handle_text))
    app.add_handler(MessageHandler(filters.ALL, handle_text))
    app.add_handler(MessageHandler(filters.ALL, handle_text))
    app.add_handler(MessageHandler(filters.ALL, handle_text))
    app.add_handler(MessageHandler(filters.ALL, handle_text))
    app.add_handler(MessageHandler(filters.ALL, handle_text))
    app.add_handler(MessageHandler(filters.ALL, handle_text))
    app.add_handler(MessageHandler(filters.ALL, handle_text))
    app.add_handler(MessageHandler(filters.ALL, handle_text))
    app.add_handler(MessageHandler(filters.ALL, handle_text))
    app.add_handler(MessageHandler(filters.ALL, handle_text))
    app.add_handler(MessageHandler(filters.ALL, handle_text))
    app.add_handler(MessageHandler(filters.ALL, handle_text))
    app.add_handler(MessageHandler(filters.ALL, handle_text))
    app.add_handler(MessageHandler(filters.ALL, handle_text))
    app.add_handler(MessageHandler(filters.ALL, handle_text))
    app.add_handler(MessageHandler(filters.ALL, handle_text))

    app.add_handler(MessageHandler(filters.ALL, handle_text))
    app.add_handler(MessageHandler(filters.ALL, handle_text))
    app.add_handler(MessageHandler(filters.ALL, handle_text))
    app.add_handler(MessageHandler(filters.ALL, handle_text))
    app.add_handler(MessageHandler(filters.ALL, handle_text))
    app.add_handler(MessageHandler(filters.ALL, handle_text))
    app.add_handler(MessageHandler(filters.ALL, handle_text))
    app.add_handler(MessageHandler(filters.ALL, handle_text))
    app.add_handler(MessageHandler(filters.ALL, handle_text))

    print("✅ Bot started successfully and running 24×7...")
    await app.run_polling()

# =============================
# ⚙️ START EVERYTHING
# =============================
if __name__ == "__main__":
    threading.Thread(target=run_flask).start()
    threading.Thread(target=keep_alive_ping).start()
    asyncio.run(main())
