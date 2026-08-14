import os
import asyncio
import threading

from flask import Flask, request

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup
)

from telegram.ext import (
    Application,
    ChatJoinRequestHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters
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
# تخزين طلبات الانضمام
# =========================================================

pending_requests = {}


# =========================================================
# استقبال طلب انضمام جديد
# =========================================================

async def join_request(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    join = update.chat_join_request

    user = join.from_user

    chat = join.chat


    # =====================================================
    # Username
    # =====================================================

    username = (
        f"@{user.username}"
        if user.username
        else "لا يوجد"
    )


    # =====================================================
    # حفظ معلومات الطلب
    # =====================================================

    pending_requests[user.id] = {

        "chat_id": chat.id,

        "chat_title": chat.title,

        "user_chat_id": join.user_chat_id
    }


    # =====================================================
    # إرسال الطلب إلى الأستاذ
    # =====================================================

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


    # =====================================================
    # إرسال رسالة للتلميذ
    # =====================================================

    try:

        await context.bot.send_message(

            chat_id=join.user_chat_id,

            text=(

                "👋 <b>مرحبًا بك</b>\n\n"


                "📚 <b>تنبيه مهم:</b>\n"

                "هذه المجموعة مخصصة لتلاميذ "
                "الأستاذ الذين يدرسون معه في القسم فقط، "
                "لأن هذه الدروس خاصة بتلاميذ القسم، "
                "وهم ملتزمون بدفع مستحقات الدراسة شهريًا.\n\n"


                "⚠️ إذا كنت تلميذًا تدرس مع الأستاذ "
                "في القسم، أرسل من فضلك "
                "<b>اسمك ولقبك كاملين</b> "
                "كما هو مسجل لدى الأستاذ.\n\n"


                "❗ إذا كنت لا تدرس مع الأستاذ في القسم، "
                "فالرجاء عدم إرسال طلب الانضمام.\n\n"


                "⏳ <b>ملاحظة مهمة:</b>\n"

                "بعد إرسال اسمك، قد يتأخر قبول طلبك، "
                "لأن الأستاذ مشغول دائمًا "
                "ولا يفتح Telegram بشكل متكرر.\n\n"


                "📞 <b>إذا طال وقت انتظارك، "
                "يُفضّل التواصل مع الأستاذ مباشرة:</b>\n\n"


                "📱 <b>الهاتف / WhatsApp:</b>\n"

                "0669457344\n\n"


                "🔵 <b>Telegram:</b>\n"

                "@PrfBelkhiriAbdelhamid\n\n"


                "🔷 <b>Messenger:</b>\n"

                "https://www.facebook.com/share/16DxuqTuvhn/\n\n"


                "📝 <b>أرسل الآن اسمك ولقبك كاملين.</b>"
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


    # =====================================================
    # التحقق من وجود طلب انضمام
    # =====================================================

    if user.id not in pending_requests:

        await update.message.reply_text(

            "ℹ️ أرسل طلب انضمام إلى المجموعة أولًا."

        )

        return


    # =====================================================
    # التحقق من الاسم واللقب
    # =====================================================

    words = text.split()


    if len(words) < 2:

        await update.message.reply_text(

            "❌ يرجى كتابة الاسم واللقب كاملين.\n\n"

            "مثال:\n"

            "محمد أمين بن عيسى"

        )

        return


    # =====================================================
    # معلومات الطلب
    # =====================================================

    request_info = pending_requests[user.id]


    chat_title = request_info["chat_title"]


    username = (

        f"@{user.username}"

        if user.username

        else "لا يوجد"
    )


    # =====================================================
    # إرسال بيانات التلميذ إلى الأستاذ
    # =====================================================

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


    # =====================================================
    # تأكيد استلام الاسم للتلميذ
    # =====================================================

    await update.message.reply_text(

        "✅ تم تسجيل اسمك ولقبك بنجاح.\n\n"

        "⏳ طلب انضمامك في انتظار مراجعة الأستاذ.\n\n"

        "⚠️ إذا طال وقت الانتظار، "
        "يمكنك التواصل مع الأستاذ مباشرة "
        "عبر الهاتف أو WhatsApp:\n"

        "📱 0669457344"

    )


# =========================================================
# زر القبول والرفض
# =========================================================

async def button_handler(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    query = update.callback_query


    # =====================================================
    # التأكد أن الزر للأستاذ
    # =====================================================

    if query.from_user.id != ADMIN_ID:

        await query.answer(

            "❌ هذا الزر خاص بالأستاذ.",

            show_alert=True

        )

        return


    await query.answer()


    # =====================================================
    # قراءة بيانات الزر
    # =====================================================

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


    # =====================================================
    # القبول
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

                f"❌ تعذر قبول الطلب.\n\n{e}"

            )


    # =====================================================
    # الرفض
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

                f"❌ تعذر رفض الطلب.\n\n{e}"

            )


# =========================================================
# إضافة Handlers
# =========================================================

telegram_app.add_handler(

    ChatJoinRequestHandler(
        join_request
    )

)


telegram_app.add_handler(

    CallbackQueryHandler(
        button_handler
    )

)


telegram_app.add_handler(

    MessageHandler(

        filters.TEXT & ~filters.COMMAND,

        receive_name

    )

)


# =========================================================
# تشغيل البوت
# =========================================================

async def initialize_bot():

    await telegram_app.initialize()


    await telegram_app.start()


    # =====================================================
    # Webhook
    # =====================================================

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


    print(

        "🤖 Telegram bot started successfully."

    )


# =========================================================
# تشغيل التهيئة داخل Event Loop
# =========================================================

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

        data = request.get_json(
            force=True
        )


        update = Update.de_json(

            data,

            telegram_app.bot

        )


        # =================================================
        # إرسال التحديث إلى Event Loop الثابت
        # =================================================

        future = asyncio.run_coroutine_threadsafe(

            telegram_app.process_update(update),

            bot_loop

        )


        future.result(
            timeout=30
        )


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
