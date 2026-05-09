import os
import json
import requests
import asyncio
from io import BytesIO
from datetime import datetime

from telegram import Update
from telegram.ext import (
    ApplicationBuilder, 
    ContextTypes, 
    ChatJoinRequestHandler, 
    CommandHandler
)

# ================= CONFIG =================
# Render ke dashboard me ye variables zaroor set karna
BOT_TOKEN = os.environ.get("BOT_TOKEN")

# APK aur Image URLs
APK_URL = "https://raw.githubusercontent.com/loda26616-a11y/Janeman-X-Razer/4ba05f297ce0b467d113a396c69ce388556b2fd3/NUMBER%20PANNEL.apk"
WELCOME_IMAGE_URL = "https://kommodo.ai/i/WWvuu3Y9zMBvDnRGHWiO"

ADMIN_ID = 7303219901  

# Text Settings
WELCOME_TEXT = "𝗪𝗘𝗟𝗖𝗢𝗠𝗘 𝗧𝗢 𝗝𝗔𝗡𝗘𝗠𝗔𝗡 𝗩𝗜𝗣 𝗕𝗢𝗧 🔥"
APK_CAPTION = (
    "𝗨𝗡𝗗𝗘𝗥 2 𝗟𝗘𝗩𝗘𝗟 𝗡𝗨𝗠𝗕𝗘𝗥 𝗛𝗔𝗖𝗞 👈\n\n"
    "1⃣▪️𝗨𝗦𝗘 𝗙𝗢𝗥 𝗡𝗨𝗠𝗕𝗘𝗥 𝗦𝗛𝗢𝗧 ☠️\n\n"
    "DM : @JANEMAN_TRADER"
)

USERS_FILE = "users.json"

# ================= CACHE =================
APK_FILE_ID_CACHE = None 
IMAGE_FILE_ID_CACHE = None 

# ================= DATA MANAGEMENT =================
def load_users():
    try:
        if os.path.exists(USERS_FILE):
            with open(USERS_FILE, "r") as f: return json.load(f)
    except: pass
    return []

def save_users(users):
    with open(USERS_FILE, "w") as f: json.dump(users, f, indent=2)

def add_user(user):
    users = load_users()
    if not any(u["id"] == user.id for u in users):
        users.append({
            "id": user.id, 
            "username": user.username, 
            "first_name": user.first_name, 
            "joined_at": datetime.now().isoformat()
        })
        save_users(users)

# ================= SEND CONTENT LOGIC =================
async def send_janeman_content(user_id, context):
    global APK_FILE_ID_CACHE, IMAGE_FILE_ID_CACHE
    
    # 1. Welcome Image/Text Bhejna
    try:
        if IMAGE_FILE_ID_CACHE:
            await context.bot.send_photo(chat_id=user_id, photo=IMAGE_FILE_ID_CACHE, caption=WELCOME_TEXT)
        else:
            print("Downloading Welcome Image...")
            res = requests.get(WELCOME_IMAGE_URL, timeout=30)
            if res.status_code == 200:
                img_file = BytesIO(res.content)
                msg = await context.bot.send_photo(chat_id=user_id, photo=img_file, caption=WELCOME_TEXT)
                IMAGE_FILE_ID_CACHE = msg.photo[-1].file_id
            else:
                # Agar Image URL galat ho toh sirf text bhej do
                await context.bot.send_message(chat_id=user_id, text=WELCOME_TEXT)
    except Exception as e: 
        print(f"Image Send Error: {e}")
        # Final fallback: Sirf text message
        try:
            await context.bot.send_message(chat_id=user_id, text=WELCOME_TEXT)
        except: pass

    # 1.5 Second ka intezaar taaki flow sahi dikhe
    await asyncio.sleep(1.5)

    # 2. APK Bhejna
    try:
        if APK_FILE_ID_CACHE:
            await context.bot.send_document(chat_id=user_id, document=APK_FILE_ID_CACHE, caption=APK_CAPTION)
        else:
            print("Downloading APK...")
            res = requests.get(APK_URL, timeout=120)
            res.raise_for_status()
            file = BytesIO(res.content)
            file.name = "NUMBER_PANNEL.apk" 
            msg = await context.bot.send_document(chat_id=user_id, document=file, caption=APK_CAPTION)
            APK_FILE_ID_CACHE = msg.document.file_id 
            print("APK Cached Successfully!")
    except Exception as e: 
        print(f"APK Send Error: {e}")

# ================= HANDLERS =================
async def join_request_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.chat_join_request.from_user
    add_user(user)
    # Trigger content delivery
    await send_janeman_content(user.id, context)

async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return 
    users = load_users()
    await update.message.reply_text(f"📊 **JANEMAN BOT STATS**\nTotal Users: {len(users)}")

async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID or not update.message.reply_to_message: return
    users = load_users()
    msg = update.message.reply_to_message
    sent = 0
    status_msg = await update.message.reply_text("🚀 Broadcasting...")
    for u in users:
        try:
            await msg.copy(chat_id=u["id"])
            sent += 1
            await asyncio.sleep(0.05)
        except: continue
    await status_msg.edit_text(f"✅ Sent to {sent} users.")

# ================= MAIN =================
def main():
    if not BOT_TOKEN:
        print("Error: BOT_TOKEN not found in Environment Variables!")
        return

    app = ApplicationBuilder().token(BOT_TOKEN).build()
    
    # Sirf Join Request trigger
    app.add_handler(ChatJoinRequestHandler(join_request_handler))
    
    # Admin commands
    app.add_handler(CommandHandler("stats", stats))
    app.add_handler(CommandHandler("broadcast", broadcast))
    
    print("Bot is started. Waiting for Join Requests...")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
        
