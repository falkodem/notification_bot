
import time
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
import asyncio

from consts import greeting, DEFAULT_BUTTONS, ADD_NOTIFICATION_MARKUP,\
      DEL_NOTIFICATION_MARKUP, WAITING_FOR_MESSAGE
from database import db_write_notification, db_read_user_notifications, \
    db_delete_user_notification, db_read_all_notifications, db_update_notification
from utils import format_notifications_for_response, format_notification_oneline, \
    format_user_input, check_if_time_is_now, update_notification_datetime


# Start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(greeting, reply_markup=DEFAULT_BUTTONS)

# Conversation part: canceling the operation
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("Действие отменено.", reply_markup=DEFAULT_BUTTONS)
    return ConversationHandler.END

# Conversation part: requesting notification details
async def request_add_notification(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text('📝 Ваша заметка...', reply_markup=ADD_NOTIFICATION_MARKUP)
    return WAITING_FOR_MESSAGE

# Conversation part: adding a notification
async def add_notification(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.message.chat_id
    user_input = update.message.text

    if user_input.lower() == "отмена":
        await update.message.reply_text("Добавление отменено", reply_markup=DEFAULT_BUTTONS)
        return ConversationHandler.END
    
    val_res = format_user_input(user_input)
    if not val_res.is_valid:
        error_msg = f"❌ Ошибка формата:\n{val_res.error_message}"
        await update.message.reply_text(error_msg, parse_mode='HTML', reply_markup=ADD_NOTIFICATION_MARKUP)
        return WAITING_FOR_MESSAGE

    
    name, notification_datetime, periodicity = val_res.result
    db_write_notification(chat_id, name, notification_datetime, periodicity)
    await update.message.reply_text("✅ Заметка добавлена!", reply_markup=DEFAULT_BUTTONS)

    return ConversationHandler.END

# List user notifications
async def get_notifications(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    notifications = db_read_user_notifications(update.message.chat_id)
    if not notifications:
        await update.message.reply_text("📭 У вас пока нет заметок", reply_markup=DEFAULT_BUTTONS)
        return
    
    response = format_notifications_for_response(notifications)
    await update.message.reply_text(response, parse_mode='HTML', reply_markup=DEFAULT_BUTTONS)

# Conversation part: requesting ID of notification to delete
async def request_delete_notification(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("Введите ID уведомления для удаления:", reply_markup=DEL_NOTIFICATION_MARKUP)
    return WAITING_FOR_MESSAGE

# Conversation part: deleting a notification
async def delete_notification(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.message.chat_id
    user_input = update.message.text

    if user_input.lower() == "отмена":
        await update.message.reply_text('Удаление отменено', reply_markup=DEFAULT_BUTTONS)
        return ConversationHandler.END

    try:
        deleted_notification = db_delete_user_notification(chat_id, user_input)
        await update.message.reply_text(
            f"Заметка с ID {user_input} удалена:\n{format_notification_oneline(deleted_notification)}",
            parse_mode='HTML',
            reply_markup=DEFAULT_BUTTONS)
    except Exception as e:
        await update.message.reply_text("Ошибка: Убедитесь, что ID заметки указан правильно.", reply_markup=DEFAULT_BUTTONS)

    return ConversationHandler.END

# List user notifications
async def get_all_notifications(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    notifications = db_read_all_notifications()
    if not notifications:
        await update.message.reply_text("📭 У вас пока нет заметок", reply_markup=DEFAULT_BUTTONS)
        return
    
    response = format_notifications_for_response(notifications)
    await update.message.reply_text(response, parse_mode='HTML', reply_markup=DEFAULT_BUTTONS)

# Send notification
async def send_notifications(context: ContextTypes.DEFAULT_TYPE) -> None:
    notifications = db_read_all_notifications()

    for notification in notifications:
        chat_id, notification_id, name, notification_datetime, periodicity = notification[1:]
        do_notify = check_if_time_is_now(notification_datetime)
        if do_notify:
            # Send notification
            await context.bot.send_message(chat_id=chat_id, text=f"🔔Напоминание:\n{name}")
            # update notification status in the database
            periodicity = int(periodicity)
            if periodicity == 0:  # If periodicity is 0, delete the notification
                db_delete_user_notification(chat_id, notification_id)
            else:
                # Update periodicity
                new_notification_datetime = update_notification_datetime(notification_datetime, periodicity)
                db_update_notification(chat_id, notification_id, new_notification_datetime)

# async def send_notifications(context: ContextTypes.DEFAULT_TYPE) -> None:
#     try:
#         await context.bot.send_message(chat_id=197133507, text="❕Напоминание: Тестовое уведомление")
#     except Exception as e:
#         print(f"Ошибка в send_notifications: {e}")


