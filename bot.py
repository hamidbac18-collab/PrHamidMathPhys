import os
import asyncio
import threading

from flask import Flask, request
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    ChatJoinRequestHandler,
    CallbackQueryHandler,
)

# =========================
# الإعدادات
# =========================

TOKEN = os.getenv("BOT_TOKEN")

ADMIN_ID = 5175833485

PORT = int(os.getenv("PORT", "10000"))

WEBHOOK_URL = os.getenv("WEBHOOK_URL")

# =========================
# Flask
# =========================

app = Flask(__name__)

# =========================
# Telegram Application
# =========================

telegram_app = Application.builder().token(TOKEN).build()

# حلقة asyncio الخاصة بالبوت
bot_loop = asyncio.new_event_loop()

# للتأكد أن البوت أصبح جاهزًا
bot_ready = threading.Event()


# =========================
# طلب انضمام جديد
# =========================

async def join_request(update: Update, context):

    request_join = update.chat_join_request

    user = request_join.from_user
    chat = request_join.chat

    username = (
        f"@{user.username}"
        if user.username
        else "لا يوجد"
    )

    text = (
        "🔔 <b>طلب انضمام جديد</b>\n\n"
        f"👤 الاسم: <b>{user.full_name}</b>\n"
        f"🔹 Username: {username}\n"
        f"🆔 ID: <code>{user.id}</code>\n"
        f"📚 المجموعة: <b>{chat.title}</b>\n\n"
        "هل تريد قبول هذا التلميذ؟"
    )

    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "✅ قبول",
                callback_data=f"approve|{chat.id}|{user.id}"
            ),
            InlineKeyboardButton(
                "❌ رفض",
                callback_data=f"reject|{chat.id}|{user.id}"
            )
        ]
    ])

    await context.bot.send_message(
        chat_id=ADMIN_ID,
        text=text,
        parse_mode="HTML",
        reply_markup=keyboard
    )


# =========================
# أزرار قبول / رفض
# =========================

async def button_handler(update: Update, context):

    query = update.callback_query

    # التأكد أن الضاغط هو الأستاذ
    if query.from_user.id != ADMIN_ID:

        await query.answer(
            "❌ هذا الزر خاص بالأستاذ.",
            show_alert=True
        )

        return

    await query.answer()

    action, chat_id, user_id = query.data.split("|")

    chat_id = int(chat_id)
    user_id = int(user_id)

    # قبول
    if action == "approve":

        await context.bot.approve_chat_join_request(
            chat_id=chat_id,
            user_id=user_id
        )

        await query.edit_message_text(
            "✅ تم قبول طلب الانضمام."
        )

    # رفض
    elif action == "reject":

        await context.bot.decline_chat_join_request(
            chat_id=chat_id,
            user_id=user_id
        )

        await query.edit_message_text(
            "❌ تم رفض طلب الانضمام."
        )


# =========================
# إضافة Handlers
# =========================

telegram_app.add_handler(
    ChatJoinRequestHandler(join_request)
)

telegram_app.add_handler(
    CallbackQueryHandler(button_handler)
)


# =========================
# تشغيل Telegram داخل asyncio
# =========================

async def telegram_start():

    await telegram_app.initialize()

    await telegram_app.start()

    # تسجيل Webhook
    if WEBHOOK_URL:

        webhook = f"{WEBHOOK_URL.rstrip('/')}/webhook"

        await telegram_app.bot.set_webhook(
            url=webhook
        )

        print("Webhook set to:", webhook)

    print("Telegram bot started successfully.")

    bot_ready.set()

    # إبقاء حلقة asyncio تعمل
    await asyncio.Event().wait()


def run_telegram_loop():

    asyncio.set_event_loop(bot_loop)

    try:

        bot_loop.run_until_complete(
            telegram_start()
        )

    except Exception as e:

        print("Telegram loop error:", repr(e))


# =========================
# الصفحة الرئيسية
# =========================

@app.route("/")
def home():

    return "🤖 botAdmition is running!"


# =========================
# Webhook
# =========================

@app.route("/webhook", methods=["POST"])
def webhook():

    try:

        # التأكد أن البوت جاهز
        if not bot_ready.is_set():

            return "Bot is starting...", 503

        data = request.get_json(force=True)

        update = Update.de_json(
            data,
            telegram_app.bot
        )

        # إرسال التحديث إلى حلقة asyncio الخاصة بالبوت
        future = asyncio.run_coroutine_threadsafe(
            telegram_app.process_update(update),
            bot_loop
        )

        # انتظار معالجة التحديث
        future.result(timeout=30)

        return "OK", 200

    except Exception as e:

        print("Webhook error:", repr(e))

        return "ERROR", 500


# =========================
# التشغيل
# =========================

if __name__ == "__main__":

    # تشغيل Telegram في Thread مستقل
    telegram_thread = threading.Thread(
        target=run_telegram_loop,
        daemon=True
    )

    telegram_thread.start()

    # انتظار جاهزية البوت
    bot_ready.wait(timeout=30)

    print("Starting Flask server...")

    app.run(
        host="0.0.0.0",
        port=PORT,
        threaded=True
    )
