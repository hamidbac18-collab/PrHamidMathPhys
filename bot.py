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
            "❌ بيانات الطلب غير صحيحة."
        )

        return


    # =====================================================
    # معلومات طلب التلميذ
    # =====================================================

    request_info = pending_requests.get(user_id)

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


            # إرسال رسالة للتلميذ
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
                            "@PrfBelkhiriAbdelhamid"
                        ),
                        parse_mode="HTML"
                    )

                except Exception as e:

                    print(
                        f"تعذر إرسال رسالة القبول "
                        f"للتلميذ {user_id}: {repr(e)}"
                    )


            # تغيير رسالة الأستاذ
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


            # إرسال رسالة للتلميذ
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

                            "🔷 <b>Messenger:</b>\n"
                            "https://www.facebook.com/share/16DxuqTuvhn/"
                        ),
                        parse_mode="HTML"
                    )

                except Exception as e:

                    print(
                        f"تعذر إرسال رسالة الرفض "
                        f"للتلميذ {user_id}: {repr(e)}"
                    )


            # تغيير رسالة الأستاذ
            await query.edit_message_text(
                "❌ تم رفض طلب الانضمام.\n"
                "📨 وتم إرسال رسالة للتلميذ."
            )


        except Exception as e:

            await query.edit_message_text(
                f"❌ تعذر رفض الطلب.\n\n{e}"
            )
