import os
import threading
import subprocess
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from telegram import Bot, Update
from telegram.ext import Updater, CommandHandler, CallbackContext

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")

BOT_TOKEN = os.getenv("BOT_TOKEN")
bot = Bot(token=BOT_TOKEN)
blocked_users = set()

@app.get("/")
def read_root():
    with open("static/index.html") as f:
        return f.read()

@app.post("/download")
async def download_video(request: Request):
    data = await request.json()
    url = data.get("url")
    user_id = data.get("user_id")
    if not url or not user_id:
        return JSONResponse({"status": "error", "message": "Missing URL or user_id"})
    filename = "video.mp4"
    try:
        subprocess.run(["yt-dlp", "-o", filename, url], check=True)
        with open(filename, "rb") as f:
            bot.send_video(chat_id=int(user_id), video=f)
        os.remove(filename)
        return JSONResponse({"status": "success", "message": "Video sent to Telegram"})
    except Exception as e:
        return JSONResponse({"status": "error", "message": str(e)})

def telegram_bot():
    updater = Updater(BOT_TOKEN, use_context=True)
    dp = updater.dispatcher

    def start(update: Update, context: CallbackContext):
        user_id = update.effective_user.id
        if user_id in blocked_users:
            context.bot.send_message(chat_id=user_id, text="❌ আপনি ব্লকড ইউজার।")
        else:
            context.bot.send_message(chat_id=user_id, text="✅ বট চালু আছে, ভিডিও লিংক দিন।")

    def block(update: Update, context: CallbackContext):
        if context.args:
            user_id = int(context.args[0])
            blocked_users.add(user_id)
            update.message.reply_text(f"🔒 ইউজার {user_id} ব্লক করা হয়েছে।")

    def unblock(update: Update, context: CallbackContext):
        if context.args:
            user_id = int(context.args[0])
            blocked_users.discard(user_id)
            update.message.reply_text(f"🔓 ইউজার {user_id} আনব্লক করা হয়েছে।")

    def blocked(update: Update, context: CallbackContext):
        update.message.reply_text(f"🔒 Blocked users: {list(blocked_users)}")

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("block", block))
    dp.add_handler(CommandHandler("unblock", unblock))
    dp.add_handler(CommandHandler("blocked", blocked))

    updater.start_polling()

# Run Telegram bot in a background thread
threading.Thread(target=telegram_bot, daemon=True).start()