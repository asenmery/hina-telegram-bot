# Хіна-Ботик з повним TODO-функціоналом, нагадуваннями і профілем
import datetime
import pytz
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
        if name: update_data["name"] = name
        if gender: update_data["gender"] = gender
        db.update(update_data, User.id == user_id)
    else:
        db.insert({"id": user_id, "name": name, "gender": gender, "todo": []})

def gendered(name, gender):
    if gender == "ж": return name or "зайчичко"
    elif gender == "ч": return name or "зайчику"
    else: return name or "зайчик"

def gendered_phrase(gender, feminine, masculine, neutral="чудова(ий)"):
    if gender == "ж": return feminine
    elif gender == "ч": return masculine
    else: return neutral

def parse_date(text):
    today = datetime.date.today()
    weekdays = {"понеділок": 0, "вівторок": 1, "середа": 2, "четвер": 3, "пʼятниця": 4, "субота": 5, "неділя": 6}
    text = text.strip().lower()
    if text == "сьогодні": return today.strftime("%Y-%m-%d")
    elif text == "завтра": return (today + datetime.timedelta(days=1)).strftime("%Y-%m-%d")
    elif text in weekdays:
        current = today.weekday()
        target = weekdays[text]
        days_ahead = (target - current + 7) % 7 or 7
        return (today + datetime.timedelta(days=days_ahead)).strftime("%Y-%m-%d")
    try:
        return datetime.datetime.strptime(text, "%Y-%m-%d").strftime("%Y-%m-%d")
    except:
        return None

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Прив ку! Обери щось ⤵️", reply_markup=reply_markup)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "💖 *Прив ку!* Я Хіна-Ботик — твоя мʼяка цифрова помічниця 🌸\n\n"
        "Я вмію:\n"
        "• Вести список справ: `/todo купити чай | завтра`\n"
        "• Показати справи: `/todo`, `/todo завтра`, `/todo 2025-04-03`\n"
        "• Видалити: `/todo del 1`\n"
        "• Відмітити: `/done 1`\n"
        "• Пити воду: `/hydrate`\n",
        parse_mode="Markdown")

async def profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = get_user(update.message.from_user.id)
    if user:
        name = user.get("name", "(не вказано)")
        gender = user.get("gender", "(не вказано)")
        await update.message.reply_text(f"👤 Профіль:\nІм'я: {name}\nСтать: {gender}")
    else:
        await update.message.reply_text("Я тебе ще не знаю 😿 Напиши 'Запиши моє ім'я'")

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("✅ Я живий і мурчу стабільно! 🐾")

async def hydrate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("💧 Не забудь попити водички, моє серденько!")

async def done(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = get_user(update.message.from_user.id)
    if not user: return await update.message.reply_text("Я тебе ще не знаю 😿")
    try:
        i = int(context.args[0]) - 1
        user["todo"][i]["done"] = True
        db.update({"todo": user["todo"]}, User.id == user["id"])
        await update.message.reply_text("✅ Завдання виконано!")
    except:
        await update.message.reply_text("Невірний номер або помилка 😿")

async def todo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = get_user(update.message.from_user.id)
    if not user:
        save_user(update.message.from_user.id)
        user = get_user(update.message.from_user.id)

    if context.args and context.args[0] == "del":
        try:
            i = int(context.args[1]) - 1
            removed = user["todo"].pop(i)
            db.update({"todo": user["todo"]}, User.id == user["id"])
            return await update.message.reply_text(f"❌ Видалено: {removed['text']}")
        except:
            return await update.message.reply_text("Помилка видалення 😿")

    if context.args:
        joined = " ".join(context.args)
        if "|" in joined:
            text, date_text = map(str.strip, joined.split("|", 1))
            due = parse_date(date_text)
            if not due:
                return await update.message.reply_text("Невідома дата. Приклад: /todo купити чай | завтра")
        else:
            text = joined
            due = datetime.date.today().strftime("%Y-%m-%d")
        user["todo"].append({"text": text, "due": due, "done": False})
        db.update({"todo": user["todo"]}, User.id == user["id"])
        return await update.message.reply_text(f"➕ Додано на {due}: {text}")

    today = datetime.date.today().strftime("%Y-%m-%d")
    tasks = [t for t in user["todo"] if t["due"] == today]
    if not tasks:
        return await update.message.reply_text("Сьогодні справ немає ✨")
    msg = "📋 Сьогоднішні справи:\n"
    for i, t in enumerate(tasks):
        checkbox = "[x]" if t["done"] else "[ ]"
        msg += f"{i+1}. {checkbox} {t['text']}\n"
    await update.message.reply_text(msg)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.message.from_user.id
    text = update.message.text.strip()
    lower = text.lower()
    user = get_user(uid)

    if uid in waiting_for_name:
        save_user(uid, name=text)
        waiting_for_name.remove(uid)
        waiting_for_gender.add(uid)
        return await update.message.reply_text("А ти хлопець чи дівчина? 💙💖")

    if uid in waiting_for_gender:
        if "ж" in lower: save_user(uid, gender="ж")
        elif "ч" in lower: save_user(uid, gender="ч")
        else: return await update.message.reply_text("Напиши 'жінка' або 'чоловік' 🌼")
        waiting_for_gender.remove(uid)
        return await update.message.reply_text("Тепер я тебе памʼятаю!")

    name = user.get("name") if user else None
    gender = user.get("gender") if user else None
    short = gendered(name, gender)

    if "обійми" in lower:
        return await update.message.reply_text(f"Добре, {short}, ловиии обійми! 🤗")
    elif "скажи" in lower:
        return await update.message.reply_text(f"Ти {gendered_phrase(gender, 'чудова', 'чудовий')}, {short} 💗")
    elif "час" in lower:
        time = datetime.datetime.now(pytz.timezone("Europe/Kyiv")).strftime("%H:%M")
        return await update.message.reply_text(f"{short}, зараз в Україні: {time} 🕐")
    elif "котик" in lower:
        return await update.message.reply_animation("https://media.giphy.com/media/JIX9t2j0ZTN9S/giphy.gif")
    elif "ім'я" in lower:
        waiting_for_name.add(uid)
        return await update.message.reply_text("Як тебе називати? 💬")
    else:
        return await update.message.reply_text(f"Мур? Я ще не знаю ці слова, {short} 🥺")

def morning_reminder():
    today = datetime.date.today().strftime("%Y-%m-%d")
    for user in db.all():
        tasks = [t for t in user.get("todo", []) if t["due"] == today and not t["done"]]
        if tasks:
            app.bot.send_message(chat_id=user["id"], text="🌞 Добрий ранок! Ось твої справи:")
            for i, task in enumerate(tasks):
                app.bot.send_message(chat_id=user["id"], text=f"{i+1}. {task['text']}")

app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("help", help_command))
app.add_handler(CommandHandler("profile", profile))
app.add_handler(CommandHandler("status", status))
app.add_handler(CommandHandler("hydrate", hydrate))
app.add_handler(CommandHandler("done", done))
app.add_handler(CommandHandler("todo", todo))
app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))

scheduler = BackgroundScheduler(timezone="Europe/Kyiv")
scheduler.add_job(morning_reminder, "cron", hour=9, minute=0)
scheduler.start()

print("✨ Хіна-Ботик запущено з повним плануванням 🗓")
app.run_polling()
