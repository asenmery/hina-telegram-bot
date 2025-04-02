import datetime
import pytz
import asyncio
from tinydb import TinyDB, Query
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
from apscheduler.schedulers.background import BackgroundScheduler

TOKEN = "8087039975:AAHilkGMZAIwQtglfaeApBHDpcNREqlpCNE"
db = TinyDB("/data/db.json")
User = Query()

waiting_for_name = set()
waiting_for_gender = set()

keyboard = [
    ["Обійми", "Скажи щось миле"],
    ["Скільки зараз часу", "Котик 🐱"],
    ["Запиши моє ім'я"]
]
reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def get_user(user_id):
    result = db.search(User.id == user_id)
    return result[0] if result else None

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
        db.insert({"id": user_id, "name": name, "gender": gender, "todo": []})

def gendered(name, gender):
    if gender == "ж":
        return name or "зайчичко"
    elif gender == "ч":
        return name or "зайчику"
    else:
        return name or "зайчик"

def gendered_phrase(gender, feminine: str, masculine: str, neutral: str = "чудова(ий)"):
    if gender == "ж":
        return feminine
    elif gender == "ч":
        return masculine
    else:
        return neutral

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Прив ку! Обери щось ⤵️", reply_markup=reply_markup)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "💖 *Прив ку!* Я Хіна-Ботик — твоя мʼяка цифрова помічниця 🌸\n\n"
        "Я вмію:\n"
        "• Вести список справ: `/todo купити чай`\n"
        "• Видалити справу: `/todo del 1`\n"
        "• Відмітити як виконане: `/done 1`\n"
        "• Показати час: напиши “Скільки зараз часу”\n"
        "• Нагадати випити водички: `/hydrate` або автоматично 💧\n\n"
        "📋 *Команди:*\n"
        "/start — показати кнопки\n"
        "/status — перевірити, чи бот живий\n"
        "/profile — профіль\n"
        "/hydrate — випити води 💧\n"
        "/done — відмітити справу виконаною\n"
        "/help — ця довідка\n"
    )
    await update.message.reply_text(text, parse_mode="Markdown")

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("✅ Я живий і мурчу стабільно! 🐾")

async def profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    user = get_user(user_id)
    if user:
        name = user.get("name", "(не вказано)")
        gender = user.get("gender", "(не вказано)")
        await update.message.reply_text(f"👤 Профіль:\nІм'я: {name}\nСтать: {gender}")
    else:
        await update.message.reply_text("Я тебе ще не знаю 😿 Напиши 'Запиши моє ім'я'")

async def hydrate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("💧 Не забудь попити водички, моє серденько!")

async def done(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("✅ Уявімо, що справа виконана! (тимчасово)")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    text = update.message.text.strip()
    lower_text = text.lower()

    if user_id in waiting_for_name:
        save_user(user_id, name=text)
        waiting_for_name.remove(user_id)
        waiting_for_gender.add(user_id)
        await update.message.reply_text("А ти хлопець чи дівчина? 💙💖 (напиши 'чоловік' або 'жінка')")
        return

    if user_id in waiting_for_gender:
        if "ж" in lower_text:
            save_user(user_id, gender="ж")
            waiting_for_gender.remove(user_id)
            await update.message.reply_text("Зрозуміла 🌸 Тепер я тебе памʼятаю!")
        elif "ч" in lower_text:
            save_user(user_id, gender="ч")
            waiting_for_gender.remove(user_id)
            await update.message.reply_text("Зрозуміла 💙 Тепер я тебе памʼятаю!")
        else:
            await update.message.reply_text("Напиши, будь ласка, 'жінка' або 'чоловік' 🌼")
        return

    user = get_user(user_id)
    name = user["name"] if user else None
    gender = user["gender"] if user else None
    short = gendered(name, gender)

    if not name:
        waiting_for_name.add(user_id)
        await update.message.reply_text("Прив ку, я тебе ще не знаю! Як тебе називати? 💬")
        return

    if "обійми" in lower_text:
        await update.message.reply_text(f"Добре, {short}, ловиии обійми! 🤗")
    elif "скажи" in lower_text:
        await update.message.reply_text(f"Ти {gendered_phrase(gender, 'чудова', 'чудовий')}, {short}. Я завжди поруч 💗")
    elif "час" in lower_text or "година" in lower_text:
        kyiv_time = datetime.datetime.now(pytz.timezone("Europe/Kyiv")).strftime("%H:%M")
        await update.message.reply_text(f"{short}, зараз в Україні: {kyiv_time} 🕐")
    elif "котик" in lower_text:
        await update.message.reply_animation("https://media.giphy.com/media/JIX9t2j0ZTN9S/giphy.gif")
    elif "запиши" in lower_text or "ім'я" in lower_text:
        waiting_for_name.add(user_id)
        await update.message.reply_text("Напиши, як тебе називати 💬")
    else:
        await update.message.reply_text(f"Мур? Я ще не знаю ці слова, {short} 🥺")

app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("help", help_command))
app.add_handler(CommandHandler("status", status))
app.add_handler(CommandHandler("profile", profile))
app.add_handler(CommandHandler("hydrate", hydrate))
app.add_handler(CommandHandler("done", done))
app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))

scheduler = BackgroundScheduler(timezone="Europe/Kyiv")
scheduler.add_job(lambda: None, "cron", hour=0, minute=0)  # заглушка, бо немає todo
scheduler.start()

print("✨ Хіна-Ботик запущено з усіма функціями та муркотінням 🐾")
app.run_polling()