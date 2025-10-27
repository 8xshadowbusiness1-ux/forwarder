import os
import json
from flask import Flask
from threading import Thread
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
    ContextTypes
)

# ====== CONFIG ======
BOT_TOKEN = os.getenv("7366502402:AAEij4_HcMkycR5-KxO2BBSd91026Cv_LbU", "PASTE_YOUR_BOT_TOKEN_HERE")
OWNER_ID = 1602198875  # 👈 Apna Telegram ID daalna
CHANNELS_FILE = "channels.json"

# ====== FLASK KEEP ALIVE ======
app_flask = Flask(__name__)

@app_flask.route("/")
def home():
    return "✅ Vishal Forwarder Bot is alive and running on Render!"

def run_flask():
    app_flask.run(host="0.0.0.0", port=10000)

# ====== LOAD CHANNEL DATA ======
if os.path.exists(CHANNELS_FILE):
    with open(CHANNELS_FILE, "r") as f:
        channels = json.load(f)
else:
    channels = []
    with open(CHANNELS_FILE, "w") as f:
        json.dump(channels, f)

# ====== INLINE BUTTONS ======
def main_buttons():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("➕ Add Channel", callback_data="add_channel")],
        [InlineKeyboardButton("➖ Remove Channel", callback_data="remove_channel")],
        [InlineKeyboardButton("📃 List Channels", callback_data="list_channels")]
    ])

# ====== START COMMAND ======
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        await update.message.reply_text("❌ You are not authorized to use this bot.")
        return
    await update.message.reply_text(
        "Welcome! Use the buttons below to manage your channels.",
        reply_markup=main_buttons()
    )

# ====== CALLBACK HANDLER ======
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    await query.answer()

    if user_id != OWNER_ID:
        await query.message.reply_text("❌ You are not authorized.")
        return

    if query.data == "add_channel":
        context.user_data["mode"] = "add"
        await query.message.reply_text("Send me the channel username to add (e.g. @examplechannel)")

    elif query.data == "remove_channel":
        context.user_data["mode"] = "remove"
        await query.message.reply_text("Send me the channel username to remove (e.g. @examplechannel)")

    elif query.data == "list_channels":
        if channels:
            text = "📃 **Channel List:**\n" + "\n".join(channels)
        else:
            text = "No channels added yet."
        await query.message.reply_text(text)

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
            await update.message.reply_text(f"✅ Channel {text} added.")
        else:
            await update.message.reply_text("⚠️ Channel already exists.")
        context.user_data["mode"] = None

    elif mode == "remove":
        if text in channels:
            channels.remove(text)
            with open(CHANNELS_FILE, "w") as f:
                json.dump(channels, f)
            await update.message.reply_text(f"❌ Channel {text} removed.")
        else:
            await update.message.reply_text("⚠️ Channel not found.")
        context.user_data["mode"] = None

    else:
        # Forward message to all added channels
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
                await update.message.reply_text(f"Error forwarding to {ch}: {e}")

# ====== MAIN FUNCTION ======
def main():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    print("✅ Vishal Forwarder Bot started successfully!")
    app.run_polling()

if __name__ == "__main__":
    Thread(target=run_flask).start()  # keepalive thread
    main()
