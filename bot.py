import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    ChatJoinRequestHandler,
    CallbackQueryHandler,
    ContextTypes,
)

TOKEN = os.getenv("BOT_TOKEN")


async def join_request(update: Update, context: ContextTypes.DEFAULT_TYPE):
    request = update.chat_join_request

    user = request.from_user
    chat = request.chat

    name = user.full_name
    username = f"@{user.username}" if user.username else "لا يوجد"
    user_id = user.id
    group_name = chat.title

    text = (
        "🔔 <b>طلب انضمام جديد</b>\n\n"
        f"👤 الاسم: <b>{name}</b>\n"
        f"🔹 المعرف: {username}\n"
        f"🆔 ID: <code>{user_id}</code>\n"
        f"📚 المجموعة: <b>{group_name}</b>\n\n"
        "هل تريد قبول هذا التلميذ؟"
    )

    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "✅ قبول",
                callback_data=f"approve:{chat.id}:{user_id}"
            ),
            InlineKeyboardButton(
                "❌ رفض",
                callback_data=f"reject:{chat.id}:{user_id}"
            )
        ]
    ])

    # في النسخة الأولى سنرسل الطلب إلى حساب تشغيل البوت
    # لاحقًا نحدد حساب الأستاذ بشكل ثابت.
    await context.bot.send_message(
        chat_id=user_id,
        text=text,
        parse_mode="HTML",
        reply_markup=keyboard
    )


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    data = query.data.split(":")
    action = data[0]
    chat_id = int(data[1])
    user_id = int(data[2])

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


def main():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(
        ChatJoinRequestHandler(join_request)
    )

    app.add_handler(
        CallbackQueryHandler(button_handler)
    )

    print("Bot is running...")
    app.run_polling(
        allowed_updates=["chat_join_request", "callback_query"]
    )


if __name__ == "__main__":
    main()
