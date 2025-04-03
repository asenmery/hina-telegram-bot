# Хіна-Ботик стабільний з покращеним todo і help
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
    ["🆕 Нова справа", "📋 Сьогоднішні справи"],
    ["🧸 Обійми", "😺 Котик"]
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

def parse_date(text):
    today = datetime.date.today()
    weekdays = {
        "понеділок": 0, "вівторок": 1, "середа": 2,
        "четвер": 3, "пʼятниця": 4, "субота": 5, "неділя": 6
    }
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

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "🌸 Я — Хіна-Ботик, твій помічник!\n"
        "Ось що я вмію:\n"
        "/start — запустити бота\n"
        "/status — перевірити чи я живий\n"
        "/profile — твій профіль\n"
        "/todo справа | дата — додати\n"
        "/todo дата — подивитись\n"
        "/todo del номер — видалити\n"
        "/done номер — позначити виконаним\n"
        "/hydrate — нагадування про воду 💧"
    )
    await update.message.reply_text(text)

async def todo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = get_user(update.message.from_user.id)
    if not user:
        save_user(update.message.from_user.id)
        user = get_user(update.message.from_user.id)

    args = context.args
    if args and args[0] == "del" and len(args) > 1:
        try:
            i = int(args[1]) - 1
            removed = user["todo"].pop(i)
            db.update({"todo": user["todo"]}, User.id == user["id"])
            return await update.message.reply_text(f"❌ Видалено: {removed['text']}")
        except:
            return await update.message.reply_text("Помилка видалення 😿 Перевір номер.")

    elif args and args[0] != "del":
        query = " ".join(args)
        if "|" in query:
            text, date_text = map(str.strip, query.split("|", 1))
            due = parse_date(date_text)
            if not due:
                return await update.message.reply_text("Невірна дата. Приклад: /todo Купити чай | завтра")
            user["todo"].append({"text": text, "due": due, "done": False})
            db.update({"todo": user["todo"]}, User.id == user["id"])
            return await update.message.reply_text(f"✅ Додано: {text} на {due}")

        due = parse_date(query)
        if due:
            tasks = [t for t in user["todo"] if t.get("due") == due]
            if not tasks:
                return await update.message.reply_text(f"На {due} у тебе нічого немає ✨")
            msg = f"📅 Завдання на {due}:\n"
            for i, t in enumerate(tasks):
                checkbox = "✅" if t.get("done") else "⬜"
                msg += f"{i+1}. {checkbox} {t['text']}\n"
            return await update.message.reply_text(msg)

    # Показати на сьогодні
    today = datetime.date.today().strftime("%Y-%m-%d")
    tasks = [t for t in user["todo"] if t.get("due") == today]
    if not tasks:
        return await update.message.reply_text("На сьогодні у тебе нічого немає ✨")

    msg = "📋 Сьогоднішні справи:\n"
    for i, t in enumerate(tasks):
        checkbox = "✅" if t.get("done") else "⬜"
        msg += f"{i+1}. {checkbox} {t['text']}\n"
    await update.message.reply_text(msg)

# Додати в app:
# app.add_handler(CommandHandler("todo", todo))
# app.add_handler(CommandHandler("help", help_command))
