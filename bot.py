import os
import asyncio
import threading

from flask import Flask, request

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
)


# =========================================================
# الإعدادات
# =========================================================

TOKEN = os.getenv("BOT_TOKEN")

PORT = int(os.getenv("PORT", "10000"))

WEBHOOK_URL = os.getenv("WEBHOOK_URL")


# =========================================================
# Flask
# =========================================================

app = Flask(__name__)


# =========================================================
# Telegram
# =========================================================

telegram_app = (
    Application
    .builder()
    .token(TOKEN)
    .build()
)


# =========================================================
# أمر /id
# =========================================================

async def get_id(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    try:

        chat = update.effective_chat
        user = update.effective_user

        if not chat:
            print("❌ لا يوجد Chat")
            return

        print("================================")
        print("📩 تم استلام أمر /id")
        print(f"👤 المستخدم: {user.full_name}")
        print(f"👤 User ID: {user.id}")
        print(f"💬 Chat ID: {chat.id}")
        print(f"💬 Chat Type: {chat.type}")
        print(f"💬 Chat Title: {chat.title}")
        print("================================")


        await update.message.reply_text(
            "🆔 <b>Chat ID:</b>\n\n"
            f"<code>{chat.id}</code>\n\n"
            "📚 <b>اسم المجموعة:</b>\n"
            f"{chat.title or 'بدون اسم'}",
            parse_mode="HTML"
        )


    except Exception as e:

        print(
            f"❌ خطأ في /id: {repr(e)}"
        )


# =========================================================
# إضافة الأمر
# =========================================================

telegram_app.add_handler(
    CommandHandler(
        "id",
        get_id
    )
)


# =========================================================
# الصفحة الرئيسية
# =========================================================

@app.route("/")
def home():

    return "🤖 ID Bot is running!"


# =========================================================
# Event Loop
# =========================================================

BOT_LOOP = asyncio.new_event_loop()


# =========================================================
# Webhook
# =========================================================

@app.route(
    "/webhook",
    methods=["POST"]
)
def webhook():

    try:

        data = request.get_json(
            force=True
        )

        update = Update.de_json(
            data,
            telegram_app.bot
        )

        asyncio.run_coroutine_threadsafe(
            telegram_app.process_update(update),
            BOT_LOOP
        )

        return "OK"

    except Exception as e:

        print(
            f"❌ Webhook error: {repr(e)}"
        )

        return "ERROR", 500


# =========================================================
# تشغيل Telegram
# =========================================================

def run_bot():

    asyncio.set_event_loop(
        BOT_LOOP
    )


    BOT_LOOP.run_until_complete(
        telegram_app.initialize()
    )


    BOT_LOOP.run_until_complete(
        telegram_app.start()
    )


    # -----------------------------------------------------
    # Webhook
    # -----------------------------------------------------

    if WEBHOOK_URL:

        webhook_url = (
            f"{WEBHOOK_URL}/webhook"
        )

        BOT_LOOP.run_until_complete(
            telegram_app.bot.set_webhook(
                url=webhook_url
            )
        )

        print(
            f"🌐 Webhook set to: {webhook_url}"
        )


    print(
        "🤖 ID Bot started successfully!"
    )


    BOT_LOOP.run_forever()


# =========================================================
# تشغيل البرنامج
# =========================================================

if __name__ == "__main__":

    thread = threading.Thread(
        target=run_bot,
        daemon=True
    )

    thread.start()


    print(
        "🌐 Starting Flask server..."
    )


    app.run(
        host="0.0.0.0",
        port=PORT,
        use_reloader=False
    )
