# подключение библиотек
# В google colab добавить: !pip install python-telegram-bot==13.15 APScheduler

import logging
from datetime import datetime, timedelta
from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext, ConversationHandler
from apscheduler.schedulers.background import BackgroundScheduler
import time

# Введите ваш токен API здесь
API_TOKEN = "api_token"

# Настройка журналирования
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Словарь для хранения дедлайнов
deadlines = {}

# Константы для состояний ConversationHandler
DATE, TIME, DESCRIPTION = range(3)

# Команда /start
def start(update: Update, context: CallbackContext):
    update.message.reply_text("Привет! Я бот-напоминалка о дедлайнах. Используйте /set, чтобы добавить новый дедлайн.")
    with open("sticker.webp", "rb") as sti:
        context.bot.send_sticker(chat_id=update.effective_chat.id, sticker=sti)

# Команда /set
def set_deadline(update: Update, context: CallbackContext):
    update.message.reply_text("Ориентируйтесь, пожалуйста, на время сервера! Введите дату дедлайна в формате YYYY-MM-DD:")
    update.message.reply_text(time.tzname)
    update.message.reply_text(str(datetime.now()))
    return DATE

def get_date(update: Update, context: CallbackContext):
    date_str = update.message.text
    context.user_data["date"] = date_str
    update.message.reply_text("Введите время дедлайна в формате HH:mm:")
    return TIME

def get_time(update: Update, context: CallbackContext):
    time_str = update.message.text
    context.user_data["time"] = time_str
    update.message.reply_text("Введите описание дедлайна:")
    return DESCRIPTION

def get_description(update: Update, context: CallbackContext):
    description = update.message.text
    chat_id = update.message.chat_id
    date_str = context.user_data["date"]
    time_str = context.user_data["time"]

    deadline_time = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")
    deadlines[chat_id] = (deadline_time, description)

    update.message.reply_text(f"Дедлайн установлен на {deadline_time} с описанием: {description}")
    set_reminder(context, chat_id, deadline_time, description)

    return ConversationHandler.END

def cancel(update: Update, context: CallbackContext):
    update.message.reply_text("Отменено.")
    return ConversationHandler.END

def set_reminder(context: CallbackContext, chat_id: int, deadline_time: datetime, description: str):
    job_queue = context.job_queue

    # Напоминание за день до
    reminder_time = deadline_time - timedelta(days=1)
    job_queue.run_once(send_reminder, reminder_time, context=(chat_id, f"Завтра дедлайн: {description}"))

    # Напоминание за 10 минут до дедлайна
    reminder_time = deadline_time - timedelta(minutes=10)
    job_queue.run_once(send_reminder, reminder_time, context=(chat_id, f"Осталось 10 минут до дедлайна: {description}"))

def send_reminder(context: CallbackContext):
    chat_id, message = context.job.context
    context.bot.send_message(chat_id, text=message)

def main():
    updater = Updater(API_TOKEN, use_context=True)

    dispatcher = updater.dispatcher

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("set", set_deadline)],
        states={
            DATE: [MessageHandler(Filters.regex("^\d{4}-\d{2}-\d{2}$"), get_date)],
            TIME: [MessageHandler(Filters.regex("^\d{2}:\d{2}$"), get_time)],
            TIMEZONE: [MessageHandler(Filters.text, get_timezone)],
            DESCRIPTION: [MessageHandler(Filters.text, get_description)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(conv_handler)

    updater.start_polling()
    updater.idle()
    
if __name__ == "__main__":
    main()