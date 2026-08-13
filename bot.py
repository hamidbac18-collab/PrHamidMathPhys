import os
from flask import Flask, request
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    ChatJoinRequestHandler,
    CallbackQueryHandler,
)

TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = 5175833485

PORT = int(os.getenv("PORT", "10000"))
WEBHOOK_URL = os.getenv("WEBHOOK_URL")

app = Flask(__name__)

telegram_app = Application.builder().token(TOKEN).build()


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


async def button_handler(update: Update, context):
    query = update.callback_query

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

    if action == "approve":

        await context.bot.approve_chat_join_request(
            chat_id=chat_id,
            user_id=user_id
        )

        await query.edit_message_text(
            "✅ تم قبول طلب الانضمام."
        )

    elif action == "reject":

        await context.bot.decline_chat_join_request(
            chat_id=chat_id,
            user_id=user_id
        )

        await query.edit_message_text(
            "❌ تم رفض طلب الانضمام."
        )


telegram_app.add_handler(
    ChatJoinRequestHandler(join_request)
)

telegram_app.add_handler(
    CallbackQueryHandler(button_handler)
)


@app.route("/")
def home():
    return "🤖 botAdmition is running!"


@app.route("/webhook", methods=["POST"])
async def webhook():
    data = request.get_json(force=True)

    update = Update.de_json(
        data,
        telegram_app.bot
    )

    await telegram_app.process_update(update)

    return "OK"


if __name__ == "__main__":
    import asyncio

    async def start_bot():
        await telegram_app.initialize()
        await telegram_app.start()

        if WEBHOOK_URL:
            await telegram_app.bot.set_webhook(
                url=f"{WEBHOOK_URL}/webhook"
            )

    asyncio.run(start_bot())

    app.run(
        host="0.0.0.0",
        port=PORT
    )
