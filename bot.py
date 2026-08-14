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
    ContextTypes,
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
    Application
    .builder()
    .token(TOKEN)
    .build()
)


# =========================================================
# معلومات طلبات الانضمام
# =========================================================

pending_requests = {}


# =========================================================
# أمر /id
# =========================================================
# أرسل /id داخل المجموعة
# وسيعطيك Chat ID الخاص بالمجموعة.
# =========================================================

async def get_id(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    chat = update.effective_chat

    if not chat:
        return

    # فقط الأستاذ يستطيع استعمال الأمر
    if update.effective_user.id != ADMIN_ID:
        return

    chat_id = chat.id

    chat_title = chat.title or "بدون اسم"

    await update.message.reply_text(
        "🆔 <b>Chat ID:</b>\n"
        f"<code>{chat_id}</code>\n\n"
        "📚 <b>اسم المجموعة:</b>\n"
        f"{chat_title}",
        parse_mode="HTML"
    )


# =========================================================
# استقبال طلبات الانضمام
# =========================================================

async def join_request(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    request_join = update.chat_join_request

    user = request_join.from_user

    chat = request_join.chat


    # =====================================================
    # حفظ معلومات الطلب
    # =====================================================

    pending_requests[user.id] = {
        "user_chat_id": user.id,
        "chat_id": chat.id,
        "chat_title": chat.title or "المجموعة",
        "user_name": user.full_name,
        "username": user.username,
    }


    # =====================================================
    # معلومات المستخدم
    # =====================================================

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
        ]
    ])


    try:

        await context.bot.send_message(
            chat_id=ADMIN_ID,
            text=text,
            parse_mode="HTML",
            reply_markup=keyboard
        )

    except Exception as e:

        print(
            "خطأ في إرسال طلب الانضمام للأستاذ:",
            repr(e)
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
    # استخراج البيانات
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
    # معلومات الطلب
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

            await context.bot.approve_chat_join_request(
                chat_id=chat_id,
                user_id=user_id
            )


            # -------------------------------------------------
            # رسالة للتلميذ
            # -------------------------------------------------

            if user_chat_id:

                try:

                    await context.bot.send_message(
                        chat_id=user_chat_id,
                        text=(
                            "✅ <b>تم قبول طلب انضمامك</b>\n\n"
                            f"📚 المجموعة: "
                            f"<b>{chat_title}</b>\n\n"
                            "مرحبًا بك معنا 🌷"
                        ),
                        parse_mode="HTML"
                    )

                except Exception as e:

                    print(
                        "تعذر إرسال رسالة القبول "
                        f"للتلميذ {user_id}: {repr(e)}"
                    )


            # -------------------------------------------------
            # تغيير رسالة الأستاذ
            # -------------------------------------------------

            await query.edit_message_text(
                "✅ تم قبول طلب الانضمام.\n"
                "📨 وتم إرسال رسالة للتلميذ."
            )


            # -------------------------------------------------
            # حذف الطلب من الذاكرة
            # -------------------------------------------------

            pending_requests.pop(
                user_id,
                None
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

            await context.bot.decline_chat_join_request(
                chat_id=chat_id,
                user_id=user_id
            )


            # -------------------------------------------------
            # رسالة للتلميذ
            # -------------------------------------------------

            if user_chat_id:

                try:

                    await context.bot.send_message(
                        chat_id=user_chat_id,
                        text=(
                            "❌ <b>نعتذر منك</b>\n\n"
                            f"تم رفض طلب انضمامك إلى:\n"
                            f"📚 <b>{chat_title}</b>\n\n"
                            "إذا كان هناك خطأ، "
                            "يمكنك التواصل مع الأستاذ."
                        ),
                        parse_mode="HTML"
                    )

                except Exception as e:

                    print(
                        "تعذر إرسال رسالة الرفض "
                        f"للتلميذ {user_id}: {repr(e)}"
                    )


            # -------------------------------------------------
            # تغيير رسالة الأستاذ
            # -------------------------------------------------

            await query.edit_message_text(
                "❌ تم رفض طلب الانضمام.\n"
                "📨 وتم إرسال رسالة للتلميذ."
            )


            # -------------------------------------------------
            # حذف الطلب من الذاكرة
            # -------------------------------------------------

            pending_requests.pop(
                user_id,
                None
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
        button_handler,
        pattern=r"^(approve|reject)\|"
    )
)


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

    return "🤖 botAdmition is running!"


# =========================================================
# Webhook
# =========================================================

BOT_LOOP = asyncio.new_event_loop()


@app.route(
    "/webhook",
    methods=["POST"]
)
def webhook():

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


# =========================================================
# تشغيل البوت
# =========================================================

def run_bot_loop():

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
    # إعداد Webhook
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
            f"Webhook set to: {webhook_url}"
        )


    print(
        "🤖 Telegram bot started successfully."
    )


    BOT_LOOP.run_forever()


# =========================================================
# تشغيل Flask
# =========================================================

if __name__ == "__main__":

    bot_thread = threading.Thread(
        target=run_bot_loop,
        daemon=True
    )


    bot_thread.start()


    print(
        "🌐 Starting Flask server..."
    )


    app.run(
        host="0.0.0.0",
        port=PORT,
        use_reloader=False
    )
