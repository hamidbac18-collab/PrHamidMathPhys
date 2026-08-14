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
# إعدادات البوت
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
    # إرسال طلب الانضمام إلى الأستاذ
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
    # الرسالة التي تصل للتلميذ
    # =====================================================

    try:

        await context.bot.send_message(

            chat_id=join.user_chat_id,

            text=(

                "👋 <b>مرحبًا بك</b>\n\n"

                "لقد استلمنا طلب انضمامك إلى:\n"

                f"📚 <b>{chat.title}</b>\n\n"

                "📝 من فضلك أرسل الآن "
                "<b>اسمك ولقبك كاملًا</b> "
                "كما هو مسجل لدى الأستاذ بلخيري عبد الحميد.\n\n"

                "<b>مثال:</b>\n"
                "علويط محسن\n\n"

                "✅ سيتم قبول طلبك بشرط أن تكون "
                "<b>تلميذًا تدرس مع الأستاذ في القسم</b>."

            ),

            parse_mode="HTML"
        )


    except Exception as e:

        print(

            f"تعذر إرسال رسالة الطلب "
            f"للتلميذ {user.id}: {repr(e)}"

        )


# =========================================================
# استقبال الاسم واللقب
# يعمل في الخاص فقط
# =========================================================

async def receive_name(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    if not update.message:

        return


    # =====================================================
    # مهم جدًا:
    # تجاهل أي رسالة ليست في الخاص
    # =====================================================

    if update.effective_chat.type != "private":

        return


    user = update.effective_user

    text = update.message.text.strip()


    if not text:

        return


    # =====================================================
    # البحث عن طلب الانضمام
    # =====================================================

    request_info = pending_requests.get(
        user.id
    )


    # =====================================================
    # إذا لم نجد الطلب
    # =====================================================

    if not request_info:

        await update.message.reply_text(

            "ℹ️ أرسل طلب انضمام إلى المجموعة أولًا."

        )

        return


    # =====================================================
    # التأكد من كتابة الاسم واللقب
    # =====================================================

    words = text.split()


    if len(words) < 2:

        await update.message.reply_text(

            "❌ يرجى كتابة الاسم واللقب كاملين.\n\n"

            "<b>مثال:</b>\n"
            "علويط محسن",

            parse_mode="HTML"
        )

        return


    # =====================================================
    # معلومات المجموعة
    # =====================================================

    chat_title = request_info.get(

        "chat_title",

        "المجموعة"

    )


    username = (

        f"@{user.username}"

        if user.username

        else "لا يوجد"

    )


    # =====================================================
    # إرسال بيانات التلميذ إلى الأستاذ
    # =====================================================

    admin_text = (

        "📝 <b>تم تسجيل بيانات التلميذ</b>\n\n"

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
    # رسالة التأكيد للتلميذ
    # =====================================================

    await update.message.reply_text(

        "✅ <b>تم تسجيل اسمك ولقبك بنجاح.</b>\n\n"

        "⏳ طلب انضمامك في انتظار مراجعة الأستاذ بلخيري.\n\n"

        "⚠️ <b>إذا طال وقت الانتظار، يمكنك التواصل معه "
        "مباشرة من أجل أن يقبلك بسرعة في الجروب:</b>\n\n"

        "📱 <b>الهاتف أو WhatsApp:</b>\n"
        "0669457344\n\n"

        "🔵 <b>Telegram:</b>\n"
        "@PrfBelkhiriAbdelhamid\n\n"

        "🔷 <b>Facebook / Messenger:</b>\n"
        "https://www.facebook.com/share/16DxuqTuvhn/",

        parse_mode="HTML"
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
    # معلومات طلب التلميذ
    # =====================================================

    request_info = pending_requests.get(
        user_id
    )


    user_chat_id = None

    chat_title = "المجموعة"


    if request_info:

        user_chat_id = request_info.get(
            "user_chat_id"
        )

        chat_title = request_info.get(
            "chat_title",
            "المجموعة"
        )


    # =====================================================
    # قبول
    # =====================================================

    if action == "approve":

        try:

            # قبول طلب الانضمام
            await context.bot.approve_chat_join_request(

                chat_id=chat_id,

                user_id=user_id

            )


            # =================================================
            # إرسال رسالة القبول للتلميذ
            # =================================================

            if user_chat_id:

                try:

                    await context.bot.send_message(

                        chat_id=user_chat_id,

                        text=(

                            "✅ <b>تم قبول طلب انضمامك</b>\n\n"

                            f"📚 المجموعة: "
                            f"<b>{chat_title}</b>\n\n"

                            "مرحبًا بك معنا 🌷\n\n"

                            "📚 نتمنى لك التوفيق والاستفادة.\n\n"

                            "إذا واجهت أي مشكلة في الدخول إلى "
                            "المجموعة، يمكنك التواصل مع الأستاذ:\n\n"

                            "📱 <b>الهاتف / WhatsApp:</b>\n"
                            "0669457344\n\n"

                            "🔵 <b>Telegram:</b>\n"
                            "@PrfBelkhiriAbdelhamid\n\n"

                            "🔷 <b>Facebook / Messenger:</b>\n"
                            "https://www.facebook.com/share/16DxuqTuvhn/"

                        ),

                        parse_mode="HTML"

                    )


                except Exception as e:

                    print(

                        f"تعذر إرسال رسالة القبول "
                        f"للتلميذ {user_id}: {repr(e)}"

                    )


            # =================================================
            # رسالة الأستاذ
            # =================================================

            await query.edit_message_text(

                "✅ تم قبول طلب الانضمام.\n"
                "📨 وتم إرسال رسالة للتلميذ."

            )


        except Exception as e:

            await query.edit_message_text(

                f"❌ تعذر قبول الطلب.\n\n{e}"

            )


    # =====================================================
    # رفض
    # =====================================================

    elif action == "reject":

        try:

            # رفض طلب الانضمام
            await context.bot.decline_chat_join_request(

                chat_id=chat_id,

                user_id=user_id

            )


            # =================================================
            # إرسال رسالة الرفض للتلميذ
            # =================================================

            if user_chat_id:

                try:

                    await context.bot.send_message(

                        chat_id=user_chat_id,

                        text=(

                            "❌ <b>نعتذر منك</b>\n\n"

                            f"تم رفض طلب انضمامك إلى:\n"
                            f"📚 <b>{chat_title}</b>\n\n"

                            "إذا كنت تلميذًا تدرس مع الأستاذ "
                            "وكان هناك خطأ في رفض الطلب، "
                            "يمكنك التواصل معه مباشرة.\n\n"

                            "📱 <b>الهاتف / WhatsApp:</b>\n"
                            "0669457344\n\n"

                            "🔵 <b>Telegram:</b>\n"
                            "@PrfBelkhiriAbdelhamid\n\n"

                            "🔷 <b>Facebook / Messenger:</b>\n"
                            "https://www.facebook.com/share/16DxuqTuvhn/"

                        ),

                        parse_mode="HTML"

                    )


                except Exception as e:

                    print(

                        f"تعذر إرسال رسالة الرفض "
                        f"للتلميذ {user_id}: {repr(e)}"

                    )


            # =================================================
            # رسالة الأستاذ
            # =================================================

            await query.edit_message_text(

                "❌ تم رفض طلب الانضمام.\n"
                "📨 وتم إرسال رسالة للتلميذ."

            )


        except Exception as e:

            await query.edit_message_text(

                f"❌ تعذر رفض الطلب.\n\n{e}"

            )


# =========================================================
# إضافة Handlers
# =========================================================

# طلبات الانضمام
telegram_app.add_handler(

    ChatJoinRequestHandler(
        join_request
    )

)


# أزرار القبول والرفض
telegram_app.add_handler(

    CallbackQueryHandler(
        button_handler
    )

)


# =========================================================
# استقبال رسائل التلميذ
#
# مهم:
# يعمل في الخاص فقط
# ولا يستقبل رسائل الجروبات
# =========================================================

telegram_app.add_handler(

    MessageHandler(

        filters.ChatType.PRIVATE
        & filters.TEXT
        & ~filters.COMMAND,

        receive_name

    )

)


# =========================================================
# تشغيل البوت
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


    print(

        "🤖 Telegram bot started successfully."

    )


# =========================================================
# تهيئة البوت داخل Event Loop
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
