import datetime
import pytz
from tinydb import TinyDB, Query
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

TOKEN = "8087039975:AAHilkGMZAIwQtglfaeApBHDpcNREqlpCNE"
db = TinyDB("db.json")
User = Query()
waiting_for_name = set()

# /start — кнопки + вітання
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        ["Обійми", "Скажи щось миле"],
        ["Скільки зараз часу", "Котик 🐱"],
        ["Запиши моє ім'я"]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text("Прив ку! Обери щось ⤵️", reply_markup=reply_markup)

# Отримати ім’я з бази
def get_name(user_id):
    result = db.search(User.id == user_id)
    if result:
        return result[0]["name"]
    return None

# Записати ім’я в базу
def save_name(user_id, name):
    if db.search(User.id == user_id):
        db.update({"name": name}, User.id == user_id)
    else:
        db.insert({"id": user_id, "name": name})

# Обробка повідомлень
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    text = update.message.text.strip()
    lower_text = text.lower()

    if user_id in waiting_for_name:
        save_name(user_id, text)
        waiting_for_name.remove(user_id)
        await update.message.reply_text(f"Зберегла! Тепер я тебе зватиму: {text} 🌸")
        return

    name = get_name(user_id)

    if not name:
        waiting_for_name.add(user_id)
        await update.message.reply_text("Прив ку, я тебе ще не знаю! Як тебе називати? 💬")
        return

    if "обійми" in lower_text:
        await update.message.reply_text(f"Добре, {name}, ловиии обійми! 🤗")

    elif "скажи" in lower_text:
        await update.message.reply_text(f"Ти чудова, {name}. Я завжди поруч 💗")

    elif "час" in lower_text or "година" in lower_text:
        kyiv_time = datetime.datetime.now(pytz.timezone("Europe/Kyiv")).strftime("%H:%M")
        await update.message.reply_text(f"{name}, зараз в Україні: {kyiv_time} 🕰️")

    elif "котик" in lower_text:
        await update.message.reply_animation("https://media.giphy.com/media/JIX9t2j0ZTN9S/giphy.gif")

    elif "запиши" in lower_text or "ім'я" in lower_text:
        waiting_for_name.add(user_id)
        await update.message.reply_text("Напиши, як тебе називати 💬")

    else:
        await update.message.reply_text(f"Мур? Я ще не знаю ці слова, {name} 🥺")

# Запуск бота
app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))

print("Хіна-Ботик з TinyDB 💾 запущено 🐾")
app.run_polling()
