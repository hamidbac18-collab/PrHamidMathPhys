import os
import asyncio
import threading

from flask import Flask, request

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)

from telegram.ext import (
    Application,
    ChatJoinRequestHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters,
)


# =========================================================
# الإعدادات
# =========================================================

TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = 5175833485

PORT = int(os.getenv("PORT", "10000"))
WEBHOOK_URL = os.getenv("WEBHOOK_URL")

app = Flask(__name__)


# =========================================================
# Telegram Application
# =========================================================

telegram_app = (
    Application.builder()
    .token(TOKEN)
    .build()
)


# =========================================================
# Event Loop ثابت
# =========================================================

bot_loop = asyncio.new_event_loop()


def run_bot_loop():
    asyncio.set_event_loop(bot_loop)
    bot_loop.run_forever()


loop_thread = threading.Thread(
    target=run_bot_loop,
    daemon=True
)

loop_thread.start()


# =========================================================
# بيانات طلبات الانضمام
# =========================================================

pending_requests = {}


# =========================================================
# طلب انضمام جديد
# =========================================================

async def join_request(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    join = update.chat_join_request

    user = join.from_user
    chat = join.chat

    username = (
        f"@{user.username}"
        if user.username
        else "لا يوجد"
    )

    # حفظ معلومات الطلب
    pending_requests[user.id] = {
        "chat_id": chat.id,
        "chat_title": chat.title,
        "user_chat_id": join.user_chat_id,
    }

    # -----------------------------------------------------
    # إرسال الطلب للأستاذ
    # -----------------------------------------------------

    text = (
        "🔔 <b>طلب انضمام جديد</b>\n\n"

        f"👤 الاسم: <b>{user.full_name}</b>\n"
        f"🔹 Username: {username}\n"
        f"🆔 ID: <code>{user.id}</code>\n"
        f"📚 المجموعة: <b>{chat.title}</b>\n\n"

        "📝 الاسم واللقب: "
        "<i>في انتظار التسجيل...</i>\n\n"

        "هل تريد قبول هذا التلميذ؟"
    )

    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "✅ اقبل",
                callback_data=(
                    f"approve|{chat.id}|{user.id}"
                )
            ),

            InlineKeyboardButton(
                "❌ ارفض",
                callback_data=(
                    f"reject|{chat.id}|{user.id}"
                )
            )
        ]
    ])

    await context.bot.send_message(
        chat_id=ADMIN_ID,
        text=text,
        parse_mode="HTML",
        reply_markup=keyboard
    )

    # -----------------------------------------------------
    # إرسال رسالة تلقائية للتلميذ
    # -----------------------------------------------------

    try:

        await context.bot.send_message(
            chat_id=join.user_chat_id,

            text=(
                "👋 <b>مرحبًا بك</b>\n\n"

                f"لقد استلمنا طلب انضمامك إلى:\n"
                f"📚 <b>{chat.title}</b>\n\n"

                "📝 من فضلك أرسل الآن "
                "<b>اسمك ولقبك كاملًا</b> "
                "كما هو مسجل لدى الأستاذ.\n\n"

                "مثال:\n"
                "<b>محمد أمين بن عيسى</b>"
            ),

            parse_mode="HTML"
        )

    except Exception as e:

        print(
            f"خطأ عند إرسال رسالة للتلميذ "
            f"{user.id}: {repr(e)}"
        )


# =========================================================
# استقبال الاسم واللقب
# =========================================================

async def receive_name(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    user = update.effective_user

    if not update.message:
        return

    text = update.message.text.strip()

    # هل لديه طلب انضمام؟
    if user.id not in pending_requests:

        await update.message.reply_text(
            "ℹ️ أرسل طلب انضمام إلى المجموعة أولًا."
        )

        return

    # التأكد من وجود اسم ولقب
    words = text.split()

    if len(words) < 2:

        await update.message.reply_text(
            "❌ يرجى كتابة الاسم واللقب كاملين.\n\n"
            "مثال:\n"
            "محمد أمين بن عيسى"
        )

        return

    request_info = pending_requests[user.id]

    chat_title = request_info["chat_title"]

    username = (
        f"@{user.username}"
        if user.username
        else "لا يوجد"
    )

    # -----------------------------------------------------
    # إرسال المعلومات للأستاذ
    # -----------------------------------------------------

    admin_text = (
        "📝 <b>تم تسجيل بيانات تلميذ</b>\n\n"

        f"👤 حساب Telegram: "
        f"<b>{user.full_name}</b>\n"

        f"🔹 Username: {username}\n"

        f"🆔 ID: <code>{user.id}</code>\n\n"

        f"📝 الاسم واللقب:\n"
        f"<b>{text}</b>\n\n"

        f"📚 المجموعة:\n"
        f"<b>{chat_title}</b>"
    )

    await context.bot.send_message(
        chat_id=ADMIN_ID,
        text=admin_text,
        parse_mode="HTML"
    )

    await update.message.reply_text(
        "✅ تم تسجيل اسمك ولقبك بنجاح.\n\n"
        "⏳ طلب انضمامك في انتظار مراجعة الأستاذ."
    )


# =========================================================
# قبول / رفض
# =========================================================

async def button_handler(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    query = update.callback_query

    if query.from_user.id != ADMIN_ID:

        await query.answer(
            "❌ هذا الزر خاص بالأستاذ.",
            show_alert=True
        )

        return

    await query.answer()

    try:

        action, chat_id, user_id = (
            query.data.split("|")
        )

        chat_id = int(chat_id)
        user_id = int(user_id)

    except Exception:

        await query.edit_message_text(
            "❌ بيانات الطلب غير صحيحة."
        )

        return

    # -----------------------------------------------------
    # قبول
    # -----------------------------------------------------

    if action == "approve":

        try:

            await context.bot.approve_chat_join_request(
                chat_id=chat_id,
                user_id=user_id
            )

            await query.edit_message_text(
                "✅ تم قبول طلب الانضمام."
            )

        except Exception as e:

            await query.edit_message_text(
                f"❌ تعذر قبول الطلب.\n\n{e}"
            )

    # -----------------------------------------------------
    # رفض
    # -----------------------------------------------------

    elif action == "reject":

        try:

            await context.bot.decline_chat_join_request(
                chat_id=chat_id,
                user_id=user_id
            )

            await query.edit_message_text(
                "❌ تم رفض طلب الانضمام."
            )

        except Exception as e:

            await query.edit_message_text(
                f"❌ تعذر رفض الطلب.\n\n{e}"
            )


# =========================================================
# Handlers
# =========================================================

telegram_app.add_handler(
    ChatJoinRequestHandler(join_request)
)

telegram_app.add_handler(
    CallbackQueryHandler(button_handler)
)

telegram_app.add_handler(
    MessageHandler(
        filters.TEXT & ~filters.COMMAND,
        receive_name
    )
)


# =========================================================
# تهيئة البوت
# =========================================================

async def initialize_bot():

    await telegram_app.initialize()

    await telegram_app.start()

    if WEBHOOK_URL:

        webhook_url = (
            f"{WEBHOOK_URL.rstrip('/')}/webhook"
        )

        await telegram_app.bot.set_webhook(
            url=webhook_url
        )

        print(
            f"Webhook set to: {webhook_url}"
        )

    print("🤖 Telegram bot started successfully.")


# إرسال التهيئة إلى الحلقة الثابتة
init_future = asyncio.run_coroutine_threadsafe(
    initialize_bot(),
    bot_loop
)

init_future.result()


# =========================================================
# الصفحة الرئيسية
# =========================================================

@app.route("/")
def home():

    return "🤖 botAdmition is running!"


# =========================================================
# Webhook
# =========================================================

@app.route(
    "/webhook",
    methods=["POST"]
)
def webhook():

    try:

        data = request.get_json(force=True)

        update = Update.de_json(
            data,
            telegram_app.bot
        )

        # إرسال التحديث إلى الحلقة الثابتة
        future = asyncio.run_coroutine_threadsafe(
            telegram_app.process_update(update),
            bot_loop
        )

        # انتظار انتهاء المعالجة
        future.result(timeout=30)

        return "OK", 200

    except Exception as e:

        print(
            f"Webhook error: {repr(e)}"
        )

        return "ERROR", 500


# =========================================================
# تشغيل Flask
# =========================================================

if __name__ == "__main__":

    print(
        "🌐 Starting Flask server..."
    )

    app.run(
        host="0.0.0.0",
        port=PORT,
        threaded=True
    )
