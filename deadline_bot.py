# подключение библиотек:
# В google colab добавить: !pip install python-telegram-bot==13.15
# В google colab добавить: !pip install APScheduler

import logging
from datetime import datetime, timedelta, date
from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext, ConversationHandler
from apscheduler.schedulers.background import BackgroundScheduler
import time

# Замените YOUR_API_TOKEN на ваш API-токен от BotFather
API_TOKEN = "API_TOKEN"

# Настройка логирования
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

deadlines = {}

DATE, TIME, DESCRIPTION = range(3)

def start(update: Update, context: CallbackContext):
    update.message.reply_text("Привет! Я бот-напоминалка о дедлайнах. \nИспользуйте /set, чтобы добавить новый дедлайн. \n\nЧтобы отменить дедлайн используйте команду /cancel")
    with open("sticker.webp", "rb") as sti:
        context.bot.send_sticker(chat_id=update.effective_chat.id, sticker=sti)

def set_deadline(update: Update, context: CallbackContext):
    update.message.reply_text("Введите дату дедлайна в формате YYYY-MM-DD:")
    return DATE

def get_date(update: Update, context: CallbackContext):
    user_text = update.message.text.strip()
    try:
        input_date = datetime.strptime(user_text, "%Y-%m-%d").date()
    except ValueError:
        update.message.reply_text("Неверный формат даты. Введите дату дедлайна в формате YYYY-MM-DD:")
        return DATE

    today = date.today()
    if input_date < today:
        update.message.reply_text("Дата должна быть в будущем. Введите новую дату дедлайна в формате YYYY-MM-DD:")
        return DATE

    context.user_data["date"] = user_text
    update.message.reply_text("Ориентируйтесь, пожалуйста, на время сервера! \nВведите время дедлайна в формате HH:mm (24-часовой формат):")
    update.message.reply_text(str(datetime.now()))
    return TIME

def get_time(update: Update, context: CallbackContext):
    time_str = update.message.text
    context.user_data["time"] = time_str

    date_str = context.user_data["date"]
    deadline_time = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")

    now = datetime.now()
    if deadline_time <= now:
        update.message.reply_text("Время должно быть в будущем. \nПожалуйста, установите новое время дедлайна в формате HH:mm (24-часовой формат):")
        return TIME

    update.message.reply_text("Введите описание дедлайна:")
    return DESCRIPTION

def get_description(update: Update, context: CallbackContext):
    description = update.message.text
    chat_id = update.message.chat_id
    date_str = context.user_data["date"]
    time_str = context.user_data["time"]

    deadline_time = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")

    now = datetime.now()
    if deadline_time <= now:
        update.message.reply_text("Время должно быть в будущем. Пожалуйста, установите новый дедлайн.")
        return DATE

    deadlines[chat_id] = (deadline_time, description)

    update.message.reply_text(f"Дедлайн установлен на {deadline_time} с описанием: {description}")
    set_reminder(context, chat_id, deadline_time, description)

    return ConversationHandler.END

def cancel(update: Update, context: CallbackContext):
    update.message.reply_text("Отменено.")
    return ConversationHandler.END

def set_reminder(context: CallbackContext, chat_id: int, deadline_time: datetime, description: str):
    job_queue = context.job_queue

    reminder_time = deadline_time - timedelta(days=1)
    job_queue.run_once(send_reminder, reminder_time, context=(chat_id, f"Завтра дедлайн: {description}"))

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

