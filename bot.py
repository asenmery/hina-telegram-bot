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
        "/todo — список справ\n"
        "/done — відмітити справу виконаною\n"
        "/hydrate — випити води 💧\n"
        "/profile — профіль\n"
        "/help — ця довідка\n"
    )
    await update.message.reply_text(text, parse_mode="Markdown")

async def todo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    user = get_user(user_id)
    if not user:
        await update.message.reply_text("Я тебе ще не знаю 😿 Напиши мені щось!")
        return
    args = context.args
    if not args:
        tasks = user.get("todo", [])
        if not tasks:
            await update.message.reply_text("У тебе ще нема справ. Додай щось: `/todo купити каву` ☕", parse_mode="Markdown")
        else:
            task_list = "\n".join([f"{i+1}. ⬜ {task['text']} (додано: {task['date']})" for i, task in enumerate(tasks)])
            await update.message.reply_text(
                f"*📝 Список справ, {gendered(user['name'], user['gender'])}:*\n\n{task_list}",
                parse_mode="Markdown"
            )
    elif args[0] == "del" and len(args) > 1 and args[1].isdigit():
        index = int(args[1]) - 1
        tasks = user.get("todo", [])
        if 0 <= index < len(tasks):
            removed = tasks.pop(index)
            db.update({"todo": tasks}, User.id == user_id)
            await update.message.reply_text(f"Видалила завдання: «{removed['text']}» ❌")
        else:
            await update.message.reply_text("Номер завдання недійсний 😿")
    else:
        task_text = " ".join(args)
        today = datetime.datetime.now(pytz.timezone("Europe/Kyiv")).strftime("%d.%m.%Y")
        user["todo"].append({"text": task_text, "date": today})
        db.update({"todo": user["todo"]}, User.id == user_id)
        await update.message.reply_text(f"Додала до списку: «{task_text}» ✍️")

async def done(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    user = get_user(user_id)
    if not user:
        await update.message.reply_text("Я тебе ще не знаю 😿 Напиши мені щось!")
        return
    args = context.args
    if not args or not args[0].isdigit():
        await update.message.reply_text("Вкажи номер справи, наприклад: `/done 1` ✅", parse_mode="Markdown")
        return
    index = int(args[0]) - 1
    tasks = user.get("todo", [])
    if 0 <= index < len(tasks):
        completed = tasks.pop(index)
        db.update({"todo": tasks}, User.id == user_id)
        await update.message.reply_text(f"Справу «{completed['text']}» виконано ✅")
    else:
        await update.message.reply_text("Номер справи недійсний 😿")

async def profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    user = get_user(user_id)
    if not user:
        await update.message.reply_text("Я тебе ще не знаю 😿 Напиши мені щось!")
        return
    name = user.get("name", "(невідоме)")
    gender = user.get("gender", "(не вказано)")
    await update.message.reply_text(f"👤 Профіль:\nІм’я: {name}\nСтать: {gender}")

async def hydrate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = get_user(update.message.from_user.id)
    name = user.get("name") if user else None
    gender = user.get("gender") if user else None
    short = gendered(name, gender)
    await update.message.reply_text(f"{short}, нагадую випити склянку водички 💧\nТвоє тіло — твій храм, навіть у лапках 🐾")

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

async def send_hydrate_reminder(app):
    for user in db.all():
        user_id = user["id"]
        name = user.get("name")
        gender = user.get("gender")
        short = gendered(name, gender)
        try:
            await app.bot.send_message(
                chat_id=user_id,
                text=f"{short}, не забудь пити воду 💧 Твій мурчальний організм цього потребує!"
            )
        except Exception as e:
            print(f"Не вдалося надіслати повідомлення користувачу {user_id}: {e}")

def clear_all_todos():
    users = db.all()
    for user in users:
        if "todo" in user:
            db.update({"todo": []}, User.id == user["id"])
    print("Щоденне очищення TODO виконано")

app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("help", help_command))
app.add_handler(CommandHandler("todo", todo))
app.add_handler(CommandHandler("done", done))
app.add_handler(CommandHandler("hydrate", hydrate))
app.add_handler(CommandHandler("profile", profile))
app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))

scheduler = BackgroundScheduler(timezone="Europe/Kyiv")
scheduler.add_job(clear_all_todos, "cron", hour=0, minute=0)
scheduler.add_job(lambda: asyncio.create_task(send_hydrate_reminder(app)), "cron", hour="10,14,18")
scheduler.start()

print("✨ Хіна-Ботик запущено з усіма функціями та нагадуванням пити воду 🐾")
app.run_polling()
