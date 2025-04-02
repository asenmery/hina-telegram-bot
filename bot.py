import datetime
import pytz
from tinydb import TinyDB, Query
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

# 🔐 Твій токен (будь обережна з ним)
TOKEN = "8087039975:AAHilkGMZAIwQtglfaeApBHDpcNREqlpCNE"
db = TinyDB("db.json")
User = Query()

# Тимчасові списки
waiting_for_name = set()
waiting_for_gender = set()

# Кнопочки
keyboard = [
    ["Обійми", "Скажи щось миле"],
    ["Скільки зараз часу", "Котик 🐱"],
    ["Запиши моє ім'я"]
]
reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

# /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Прив ку! Обери щось ⤵️", reply_markup=reply_markup)

# Отримати користувача
def get_user(user_id):
    result = db.search(User.id == user_id)
    return result[0] if result else None

# Зберегти користувача
def save_user(user_id, name=None, gender=None):
    user = get_user(user_id)
    if user:
        update_data = {}
        if name:
            update_data["name"] = name
        if gender:
            update_data["gender"] = gender
        db.update(update_data, User.id == user_id)
    else:
        db.insert({"id": user_id, "name": name, "gender": gender})

# Стиль звертання
def gendered(name, gender):
    if gender == "ж":
        return name or "зайчичко"
    elif gender == "ч":
        return name or "зайчику"
    else:
        return name or "зайчик"

# Обробка повідомлень
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    text = update.message.text.strip()
    lower_text = text.lower()

    # Якщо чекаємо імʼя
    if user_id in waiting_for_name:
        save_user(user_id, name=text)
        waiting_for_name.remove(user_id)
        waiting_for_gender.add(user_id)
        await update.message.reply_text("А ти хлопець чи дівчина? 💙💖\n(напиши 'чоловік' або 'жінка')")
        return

    # Якщо чекаємо стать
    if user_id in waiting_for_gender:
        if "ж" in lower_text:
            save_user(user_id, gender="ж")
            waiting_for_gender.remove(user_id)
            await update.message.reply_text("Зрозуміла 🌸 Тепер я тебе памʼятаю!")
        elif "ч" in lower_text:
            save_user(user_id, gender="ч")
            waiting_for_gender.remove(user_id)
            await update.message.reply_text("Зрозумів 💙 Тепер я тебе памʼятаю!")
        else:
            await update.message.reply_text("Напиши, будь ласка, 'жінка' або 'чоловік' 🌼")
        return

    # Дані користувача
    user = get_user(user_id)
    name = user["name"] if user else None
    gender = user["gender"] if user else None
    short = gendered(name, gender)

    # Якщо ще не зареєстрований
    if not name:
        waiting_for_name.add(user_id)
        await update.message.reply_text("Прив ку, я тебе ще не знаю! Як тебе називати? 💬")
        return

    # Реакції
    if "обійми" in lower_text:
        await update.message.reply_text(f"Добре, {short}, ловиии обійми! 🤗")

    elif "скажи" in lower_text:
        await update.message.reply_text(f"Ти чудова, {short}. Я завжди поруч 💗")

    elif "час" in lower_text or "година" in lower_text:
        kyiv_time = datetime.datetime.now(pytz.timezone("Europe/Kyiv")).strftime("%H:%M")
        await update.message.reply_text(f"{short}, зараз в Україні: {kyiv_time} 🕰️")

    elif "котик" in lower_text:
        await update.message.reply_animation("https://media.giphy.com/media/JIX9t2j0ZTN9S/giphy.gif")

    elif "запиши" in lower_text or "ім'я" in lower_text:
        waiting_for_name.add(user_id)
        await update.message.reply_text("Напиши, як тебе називати 💬")

    else:
        await update.message.reply_text(f"Мур? Я ще не знаю ці слова, {short} 🥺")

# Запуск бота
app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))

print("✨ Хіна-Ботик з памʼяттю, ім’ям і гендером запущено 🐾")
app.run_polling()
