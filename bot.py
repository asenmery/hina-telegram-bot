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

def parse_date(text):
    today = datetime.date.today()
    weekdays = {
        "понеділок": 0, "вівторок": 1, "середа": 2,
        "четвер": 3, "пʼятниця": 4, "субота": 5, "неділя": 6
    }
    text = text.strip().lower()
    if text == "сьогодні":
        return today.strftime("%Y-%m-%d")
    elif text == "завтра":
        return (today + datetime.timedelta(days=1)).strftime("%Y-%m-%d")
    elif text in weekdays:
        current = today.weekday()
        target = weekdays[text]
        days_ahead = (target - current + 7) % 7 or 7
        return (today + datetime.timedelta(days=days_ahead)).strftime("%Y-%m-%d")
    else:
        try:
            return datetime.datetime.strptime(text, "%Y-%m-%d").strftime("%Y-%m-%d")
        except:
            return None

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Прив ку! Обери щось ⤵️", reply_markup=reply_markup)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "💖 *Прив ку!* Я Хіна-Ботик — твоя мʼяка цифрова помічниця 🌸\n\n"
        "Я вмію:\n"
        "• Вести список справ: `/todo купити чай | завтра`\n"
        "• Показати справи: `/todo`, `/todo завтра`, `/todo 2025-04-03`\n"
        "• Видалити справу: `/todo del 1`\n"
        "• Відмітити як виконане: `/done 1`\n"
        "• Нагадати попити води: `/hydrate`\n\n"
        "📋 *Команди:*\n"
        "/start — кнопки\n"
        "/status — чи живий я\n"
        "/profile — профіль\n"
        "/todo — список справ\n"
        "/done — виконано\n"
        "/hydrate — пити воду\n"
        "/help — довідка\n"
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
    user_id = update.message.from_user.id
    user = get_user(user_id)
    if not user:
        await update.message.reply_text("Я тебе ще не знаю 😿")
        return

    if len(context.args) < 1 or not context.args[0].isdigit():
        await update.message.reply_text("Вкажи номер завдання: /done 1")
        return

    index = int(context.args[0]) - 1
    todos = user.get("todo", [])

    if 0 <= index < len(todos):
        todos[index]["done"] = True
        db.update({"todo": todos}, User.id == user_id)
        await update.message.reply_text("✅ Завдання виконано!")
    else:
        await update.message.reply_text("Невірний номер завдання 😿")

async def todo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    user = get_user(user_id)
    if not user:
        save_user(user_id)
        user = get_user(user_id)

    if context.args and context.args[0] == "del" and len(context.args) > 1:
        index = int(context.args[1]) - 1
        if 0 <= index < len(user["todo"]):
            removed = user["todo"].pop(index)
            db.update({"todo": user["todo"]}, User.id == user_id)
            await update.message.reply_text(f"❌ Видалено: {removed['text']}")
        else:
            await update.message.reply_text("Невірний номер завдання 😿")
        return

    if context.args and not "|" in " ".join(context.args):
        date = parse_date(" ".join(context.args))
        if not date:
            await update.message.reply_text("Невідома дата. Приклад: /todo завтра або /todo 2025-04-04")
            return
        tasks = [t for t in user["todo"] if t["due"] == date]
        if not tasks:
            await update.message.reply_text(f"На {date} у тебе нічого немає ✨")
            return
        text = f"📅 Завдання на {date}:\n"
        for i, task in enumerate(tasks):
            checkbox = "[x]" if task["done"] else "[ ]"
            text += f"{i+1}. {checkbox} {task['text']}\n"
        await update.message.reply_text(text)
        return

    if context.args:
        full = " ".join(context.args)
        if "|" in full:
            parts = full.split("|", 1)
            task_text = parts[0].strip()
            due_date = parse_date(parts[1])
            if not due_date:
                await update.message.reply_text("Невірна дата. Приклад: /todo купити хліб | завтра")
                return
        else:
            task_text = full
            due_date = datetime.date.today().strftime("%Y-%m-%d")

        user["todo"].append({
            "text": task_text,
            "due": due_date,
            "done": False
        })
        db.update({"todo": user["todo"]}, User.id == user_id)
        await update.message.reply_text(f"➕ Додано на {due_date}: {task_text}")
    else:
        today = datetime.date.today().strftime("%Y-%m-%d")
        tasks = [t for t in user["todo"] if t["due"] == today]
        if not tasks:
            await update.message.reply_text("Сьогодні в тебе немає справ ✨")
            return
        text = f"📋 Сьогоднішні справи:\n"
        for i, task in enumerate(tasks):
            checkbox = "[x]" if task["done"] else "[ ]"
            text += f"{i+1}. {checkbox} {task['text']}\n"
        await update.message.reply_text(text)

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
            await update.message.reply_text("Зрозумів 💙 Тепер я тебе памʼятаю!")
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

def morning_reminder():
    users = db.all()
    today = datetime.date.today().strftime("%Y-%m-%d")
    for user in users:
        tasks = [t for t in user.get("todo", []) if t["due"] == today and not t["done"]]
        if tasks:
            app.bot.send_message(chat_id=user["id"], text="🌞 Добрий ранок! Ось твої справи на сьогодні:")
            for i, task in enumerate(tasks):
                app.bot.send_message(chat_id=user["id"], text=f"{i+1}. {task['text']}")

app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("help", help_command))
app.add_handler(CommandHandler("status", status))
app.add_handler(CommandHandler("profile", profile))
app.add_handler(CommandHandler("hydrate", hydrate))
app.add_handler(CommandHandler("done", done))
app.add_handler(CommandHandler("todo", todo))
app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))

scheduler = BackgroundScheduler(timezone="Europe/Kyiv")
scheduler.add_job(morning_reminder, "cron", hour=9, minute=0)
scheduler.start()

print("✨ Хіна-Ботик запущено з функціоналом дедлайнів, нагадувань і дат 🗓")
app.run_polling()