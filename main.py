import os
from dotenv import load_dotenv
from telegram.ext import Application, CommandHandler, \
    MessageHandler, filters, ConversationHandler, JobQueue

from database import setup_database
from handlers import start, get_notifications,\
    request_add_notification, add_notification, \
    request_delete_notification, delete_notification, \
    cancel, \
    get_all_notifications, \
    send_notifications
from consts import WAITING_FOR_MESSAGE



load_dotenv()
TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')

if not TOKEN:
    raise ValueError("No TELEGRAM_BOT_TOKEN found in environment variables")


def main() -> None:
    setup_database()

    application = (
        Application
        .builder()
        .token(TOKEN)
        .concurrent_updates(True)
        .job_queue(JobQueue())
        .build()
    )
    
    show_handler = MessageHandler(filters.Regex("^Вывести список заметок$"), get_notifications)
    conv_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^Добавить заметку$"), request_add_notification)],
        states={
            WAITING_FOR_MESSAGE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, add_notification)
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )
    delete_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^Удалить заметку$"), request_delete_notification)],
        states={
            WAITING_FOR_MESSAGE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, delete_notification)
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    application.add_handler(CommandHandler("start", start))
    application.add_handler(conv_handler)
    application.add_handler(show_handler)
    application.add_handler(delete_handler)
    application.add_handler(CommandHandler("all", get_all_notifications))
    application.job_queue.run_repeating(send_notifications, interval=60.0, first=0)

    
    application.run_polling()
if __name__ == "__main__":
    main()
