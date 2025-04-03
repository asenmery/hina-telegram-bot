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

def gendered_phrase(gender, feminine, masculine, neutral="чудова(ий)"):
    if gender == "ж": return feminine
    elif gender == "ч": return masculine
    else: return neutral

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

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Прив ку! Обери щось ⤵️", reply_markup=reply_markup)

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("✅ Я живий і мурчу стабільно! 🐾")

async def profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = get_user(update.message.from_user.id)
    if user:
        name = user.get("name", "(не вказано)")
        gender = user.get("gender", "(не вказано)")
        await update.message.reply_text(f"👤 Профіль:\nІм'я: {name}\nСтать: {gender}")
    else:
        await update.message.reply_text("Я тебе ще не знаю 😿 Напиши 'Запиши моє імʼя'")

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
        query = " ".join(context.args)
        if "|" in query:
            text, date_text = map(str.strip, query.split("|", 1))
            due = parse_date(date_text)
            if not due:
                return await update.message.reply_text("Невідома дата. Приклад: /todo купити чай | завтра")
            user["todo"].append({"text": text, "due": due, "done": False})
            db.update({"todo": user["todo"]}, User.id == user["id"])
            return await update.message.reply_text(f"➕ Додано на {due}: {text}")

        due = parse_date(query)
        if due:
            tasks = [t for t in user["todo"] if t.get("due") == due]
            if not tasks:
                return await update.message.reply_text(f"На {due} у тебе нічого немає ✨")
            msg = f"📅 Завдання на {due}:\n"
            for i, t in enumerate(tasks):
                checkbox = "[x]" if t.get("done") else "[ ]"
                msg += f"{i+1}. {checkbox} {t['text']}\n"
            return await update.message.reply_text(msg)

    today = datetime.date.today().strftime("%Y-%m-%d")
    tasks = [t for t in user["todo"] if t.get("due") == today]

    if not tasks:
        return await update.message.reply_text("На сьогодні у тебе нічого немає ✨")

    msg = "📋 Справи на сьогодні:\n"
    for i, t in enumerate(tasks):
        checkbox = "✅" if t.get("done") else "⬜"
        msg += f"{i+1}. {checkbox} {t['text']}\n"
    await update.message.reply_text(msg)

async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.lower()
    user_id = update.message.from_user.id
    user = get_user(user_id)

    if user_id in waiting_for_name:
        save_user(user_id, name=text)
        waiting_for_name.discard(user_id)
        await update.message.reply_text(f"Мур, тепер я знаю що тебе звати {text} 🐾")
        return

    if user_id in waiting_for_gender:
        if text in ["ж", "ч"]:
            save_user(user_id, gender=text)
            waiting_for_gender.discard(user_id)
            await update.message.reply_text("Збережено! 🌟")
        else:
            await update.message.reply_text("Введи 'ж' або 'ч'")
        return

    if "обійми" in text or "обіймашки" in text:
        return await update.message.reply_text("🤗 Мурчальні обійми для тебе!")

    if "котик" in text:
        return await update.message.reply_text("мяу~ 🐱 Ти теж котик!")

    if "нов" in text or "справа" in text:
        return await update.message.reply_text("📝 Додай через /todo впиши справу")

    if "сьогоднішн" in text:
        return await todo(update, context)

    if "запиши моє ім" in text:
        waiting_for_name.add(user_id)
        return await update.message.reply_text("Як тебе звати? 🌸")

    if "стать" in text or "хлопець" in text or "дівчинка" in text:
        waiting_for_gender.add(user_id)
        return await update.message.reply_text("Напиши 'ж' чи 'ч' 🧠")

    await update.message.reply_text("Я тебе чую, але ще не розумію 🐣")

app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("status", status))
app.add_handler(CommandHandler("profile", profile))
app.add_handler(CommandHandler("todo", todo))
app.add_handler(CommandHandler("done", done))
app.add_handler(CommandHandler("hydrate", hydrate))
app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), message_handler))

print("✨ Хіна-Ботик запущено з повним плануванням 🗓")
app.run_polling()
