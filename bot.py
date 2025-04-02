import datetime
import pytz
import json
import os
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

# 🔐 Твій токен (тільки не публікуй публічно 😿)
TOKEN = "8087039975:AAHilkGMZAIwQtglfaeApBHDpcNREqlpCNE"
USERS_FILE = "users.json"

# Завантаження імен
def load_users():
    if not os.path.exists(USERS_FILE):
        return {}
    with open(USERS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

# Збереження імен
def save_users(users):
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(users, f, ensure_ascii=False, indent=2)

users = load_users()
waiting_for_name = set()

# /start — привітання + кнопочки
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        ["Обійми", "Скажи щось миле"],
        ["Скільки зараз часу", "Котик 🐱"],
        ["Запиши моє ім'я"]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text("Прив ку! Обери щось ⤵️", reply_markup=reply_markup)

# Обробка повідомлень
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.message.from_user.id)
    text = update.message.text.strip()
    lower_text = text.lower()

    # Якщо новий користувач
    if user_id not in users and user_id not in waiting_for_name:
        waiting_for_name.add(user_id)
        await update.message.reply_text("Прив ку, я тебе ще не знаю! Як тебе називати? 💬")
        return

    # Якщо чекаємо імʼя
    if user_id in waiting_for_name:
        users[user_id] = text
        save_users(users)
        waiting_for_name.remove(user_id)
        await update.message.reply_text(f"Зберегла! Тепер я тебе зватиму: {text} 🌸")
        return

    # Імʼя з бази
    name = users.get(user_id, "моя зіронька ✨")

    # Реакції
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

print("🐾 Хіна-Ботик запущено з любовʼю")
app.run_polling()
