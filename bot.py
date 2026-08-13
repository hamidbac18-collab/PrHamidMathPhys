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
    CommandHandler,
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


# =========================================================
# Flask
# =========================================================

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
# حلقة asyncio ثابتة
# =========================================================

loop = asyncio.new_event_loop()


def run_loop():
    asyncio.set_event_loop(loop)
    loop.run_forever()


loop_thread = threading.Thread(
    target=run_loop,
    daemon=True
)

loop_thread.start()


# =========================================================
# بيانات مؤقتة
# =========================================================

# أسماء التلاميذ الذين سجلوا أسماءهم
student_names = {}

# طلبات الانضمام المعلقة
# user_id -> قائمة بالمجموعات
pending_requests = {}


# =========================================================
# /start
# =========================================================

async def start_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    user = update.effective_user

    saved_name = student_names.get(user.id)

    if saved_name:

        await update.message.reply_text(
            f"✅ اسمك مسجل مسبقًا:\n\n"
            f"👤 {saved_name}\n\n"
            f"يمكنك الآن انتظار مراجعة الأستاذ."
        )

        return

    await update.message.reply_text(
        "👋 مرحبًا بك في بوت الأستاذ بلخيري عبد الحميد.\n\n"
        "📝 من فضلك أرسل الآن **اسمك ولقبك كاملًا** "
        "كما هو مسجل لدى الأستاذ.\n\n"
        "مثال:\n"
        "محمد أمين بن عيسى"
    )


# =========================================================
# استقبال الاسم واللقب
# =========================================================

async def receive_name(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    user = update.effective_user

    text = update.message.text.strip()

    # تقسيم الاسم إلى كلمات
    words = text.split()

    # يجب أن يحتوي على كلمتين على الأقل
    if len(words) < 2:

        await update.message.reply_text(
            "❌ يرجى كتابة **الاسم واللقب كاملين**.\n\n"
            "مثال:\n"
            "محمد أمين بن عيسى"
        )

        return

    # حفظ الاسم
    student_names[user.id] = text

    # معرفة طلبات الانضمام الخاصة بهذا المستخدم
    groups = pending_requests.get(user.id, [])

    username = (
        f"@{user.username}"
        if user.username
        else "لا يوجد"
    )

    if groups:

        groups_text = "\n".join(
            f"📚 {group_name}"
            for group_name in groups
        )

    else:

        groups_text = "لا يوجد طلب انضمام حاليًا"

    # إرسال المعلومات للأستاذ
    admin_text = (
        "📝 <b>تم تسجيل بيانات تلميذ</b>\n\n"
        f"👤 الاسم في Telegram: "
        f"<b>{user.full_name}</b>\n"
        f"🔹 Username: {username}\n"
        f"🆔 ID: <code>{user.id}</code>\n\n"
        f"✏️ الاسم واللقب المسجل:\n"
        f"<b>{text}</b>\n\n"
        f"{groups_text}"
    )

    await context.bot.send_message(
        chat_id=ADMIN_ID,
        text=admin_text,
        parse_mode="HTML"
    )

    await update.message.reply_text(
        "✅ تم تسجيل اسمك ولقبك بنجاح.\n\n"
        "⏳ يمكنك الآن انتظار مراجعة الأستاذ.\n"
        "لن يتم قبولك أو رفضك تلقائيًا."
    )


# =========================================================
# طلب انضمام جديد
# =========================================================

async def join_request(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    request_join = update.chat_join_request

    user = request_join.from_user

    chat = request_join.chat

    username = (
        f"@{user.username}"
        if user.username
        else "لا يوجد"
    )

    # حفظ الطلب
    if user.id not in pending_requests:
        pending_requests[user.id] = []

    if chat.title not in pending_requests[user.id]:

        pending_requests[user.id].append(
            chat.title
        )

    # الاسم المسجل مسبقًا إن وجد
    saved_name = student_names.get(user.id)

    if saved_name:

        registered_text = (
            f"📝 الاسم واللقب المسجل:\n"
            f"<b>{saved_name}</b>\n\n"
        )

    else:

        registered_text = (
            "📝 الاسم واللقب المسجل:\n"
            "⚠️ <b>لم يسجل بعد</b>\n\n"
        )

    # رابط البوت
    bot_info = await context.bot.get_me()

    bot_link = (
        f"https://t.me/{bot_info.username}"
    )

    text = (
        "🔔 <b>طلب انضمام جديد</b>\n\n"

        f"👤 الاسم: <b>{user.full_name}</b>\n"
        f"🔹 Username: {username}\n"
        f"🆔 ID: <code>{user.id}</code>\n"
        f"📚 المجموعة: <b>{chat.title}</b>\n\n"

        f"{registered_text}"

        "هل تريد قبول هذا التلميذ؟"
    )

    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "✅ قبول",
                callback_data=(
                    f"approve|{chat.id}|{user.id}"
                )
            ),
            InlineKeyboardButton(
                "❌ رفض",
                callback_data=(
                    f"reject|{chat.id}|{user.id}"
                )
            )
        ],
        [
            InlineKeyboardButton(
                "📝 إرسال الاسم واللقب",
                url=bot_link
            )
        ]
    ])

    await context.bot.send_message(
        chat_id=ADMIN_ID,
        text=text,
        parse_mode="HTML",
        reply_markup=keyboard
    )


# =========================================================
# أزرار قبول / رفض
# =========================================================

async def button_handler(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    query = update.callback_query

    # التأكد أن الزر للأستاذ
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
            "❌ حدث خطأ في بيانات الطلب."
        )

        return

    # =====================================================
    # قبول
    # =====================================================

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
                f"❌ تعذر قبول الطلب.\n\n"
                f"{e}"
            )

    # =====================================================
    # رفض
    # =====================================================

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
                f"❌ تعذر رفض الطلب.\n\n"
                f"{e}"
            )


# =========================================================
# إضافة Handlers
# =========================================================

telegram_app.add_handler(
    ChatJoinRequestHandler(join_request)
)

telegram_app.add_handler(
    CommandHandler("start", start_command)
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
# تهيئة Telegram
# =========================================================

async def initialize_bot():

    await telegram_app.initialize()

    await telegram_app.start()

    if WEBHOOK_URL:

        await telegram_app.bot.set_webhook(
            url=f"{WEBHOOK_URL}/webhook"
        )

        print(
            f"Webhook set to: "
            f"{WEBHOOK_URL}/webhook"
        )

    print("Telegram bot started successfully.")


# تشغيل Telegram على الحلقة الثابتة
future = asyncio.run_coroutine_threadsafe(
    initialize_bot(),
    loop
)

future.result()


# =========================================================
# الصفحة الرئيسية
# =========================================================

@app.route("/")
def home():

    return "🤖 botAdmition is running!"


# =========================================================
# Webhook
# =========================================================

@app.route("/webhook", methods=["POST"])
def webhook():

    try:

        data = request.get_json(force=True)

        update = Update.de_json(
            data,
            telegram_app.bot
        )

        # إرسال المعالجة إلى Event Loop الثابت
        future = asyncio.run_coroutine_threadsafe(
            telegram_app.process_update(update),
            loop
        )

        # ننتظر انتهاء معالجة الطلب
        future.result(timeout=30)

        return "OK", 200

    except Exception as e:

        print(
            f"Webhook error: {e}"
        )

        return "ERROR", 500


# =========================================================
# تشغيل Flask
# =========================================================

if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=PORT
    )
