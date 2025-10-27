from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
import json
import os

# ====== CONFIG ======
bot_token = "7366502402:AAEij4_HcMkycR5-KxO2BBSd91026Cv_LbU"      # BotFather se mila token
owner_id = 1602198875                    # Apna Telegram user ID daalo yahan
channels_file = "channels.json"

# ====== LOAD OR CREATE CHANNELS FILE ======
if os.path.exists(channels_file):
    with open(channels_file, "r") as f:
        channels = json.load(f)
else:
    channels = []
    with open(channels_file, "w") as f:
        json.dump(channels, f)

# ====== INITIALIZE BOT ======
app = Client("forward_bot", bot_token=bot_token)

# ====== MAIN BUTTONS ======
def main_buttons():
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("➕ Add Channel", callback_data="add_channel")],
            [InlineKeyboardButton("➖ Remove Channel", callback_data="remove_channel")],
            [InlineKeyboardButton("📃 List Channels", callback_data="list_channels")],
        ]
    )

# ====== OWNER CHECK DECORATOR ======
def owner_only(func):
    async def wrapper(client, message):
        if message.from_user.id != owner_id:
            await message.reply("❌ You are not allowed to use this bot.")
            return
        await func(client, message)
    return wrapper

def owner_only_callback(func):
    async def wrapper(client, query: CallbackQuery):
        if query.from_user.id != owner_id:
            await query.answer("❌ You are not allowed.", show_alert=True)
            return
        await func(client, query)
    return wrapper

# ====== /start COMMAND ======
@app.on_message(filters.private & filters.command("start"))
@owner_only
async def start(client, message):
    await message.reply_text(
        "Welcome! Use the buttons below to manage channels and forward messages.",
        reply_markup=main_buttons()
    )

# ====== CALLBACK HANDLER ======
@app.on_callback_query()
@owner_only_callback
async def callbacks(client: Client, query: CallbackQuery):
    if query.data == "add_channel":
        await query.message.reply("Send me the channel username to add (e.g., @examplechannel).")
        app.add_handler(filters.private & filters.text, add_channel_handler, group=1)

    elif query.data == "remove_channel":
        await query.message.reply("Send me the channel username to remove (e.g., @examplechannel).")
        app.add_handler(filters.private & filters.text, remove_channel_handler, group=2)

    elif query.data == "list_channels":
        if channels:
            await query.message.reply("📃 Channels:\n" + "\n".join(channels))
        else:
            await query.message.reply("No channels added yet.")

# ====== ADD CHANNEL HANDLER ======
async def add_channel_handler(client, message):
    if message.from_user.id != owner_id:
        await message.reply("❌ You are not allowed.")
        return
    channel = message.text.strip()
    if channel not in channels:
        channels.append(channel)
        with open(channels_file, "w") as f:
            json.dump(channels, f)
        await message.reply(f"✅ Channel {channel} added.")
    else:
        await message.reply("⚠️ Channel already exists.")
    app.remove_handler(add_channel_handler, group=1)

# ====== REMOVE CHANNEL HANDLER ======
async def remove_channel_handler(client, message):
    if message.from_user.id != owner_id:
        await message.reply("❌ You are not allowed.")
        return
    channel = message.text.strip()
    if channel in channels:
        channels.remove(channel)
        with open(channels_file, "w") as f:
            json.dump(channels, f)
        await message.reply(f"❌ Channel {channel} removed.")
    else:
        await message.reply("⚠️ Channel not found.")
    app.remove_handler(remove_channel_handler, group=2)

# ====== FORWARD PRIVATE MESSAGES ======
@app.on_message(filters.private & ~filters.command(["start"]))
async def forward_messages(client, message):
    if message.from_user.id != owner_id:
        return  # ignore messages from non-owner
    if not channels:
        await message.reply("No channels added to forward messages. Use /start to add channels.")
        return
    for channel in channels:
        try:
            await client.forward_messages(chat_id=channel, from_chat_id=message.chat.id, message_ids=message.message_id)
        except Exception as e:
            await message.reply(f"Error forwarding to {channel}: {e}")

# ====== RUN BOT ======
app.run()


