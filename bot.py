import datetime
import pytz
from tinydb import TinyDB, Query
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
from apscheduler.schedulers.background import BackgroundScheduler

TOKEN = "8087039975:AAHilkGMZAIwQtglfaeApBHDpcNREqlpCNE"
db = TinyDB("db.json")
User = Query()

waiting_for_name = set()
waiting_for_gender = set()

keyboard = [
    ["Обійми", "Скажи щось миле"],
    ["Скільки зараз часу", "Котик 🐱"],
    ["Запиши моє ім'я"]
]
reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

# ---------- КОРИСТУВАЧ ----------
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

# ---------- КОМАНДА /start ----------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Прив ку! Обери щось ⤵️", reply_markup=reply_markup)

# ---------- КОМАНДА /help ----------
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "\U0001F496 *Прив ку!* Я Хіна-Ботик — твоя мʼяка цифрова помічниця \U0001F338\n\n"
        "Я вмію:\n"
        "• Вести список справ: `/todo купити чай`\n"
        "• Видалити справу: `/todo del 1`\n"
        "• Відмітити як виконане: `/done 1`\n"
        "• Показати час: напиши “Скільки зараз часу”\n"
        "• Обіймати, муркати і котика давати \U0001F431\n\n"
        "\U0001F4CB *Команди:*\n"
        "/start — показати кнопки\n"
        "/todo — список справ\n"
        "/done — відмітити справу виконаною\n"
        "/profile — профіль\n"
        "/help — ця довідка\n\n"
        "\U0001F9E0 Я запамʼятовую твоє імʼя і стать, щоб спілкуватись з тобою з любовʼю \U0001F4AA"
    )
    await update.message.reply_text(text, parse_mode="Markdown")

# ---------- TODO ----------
async def todo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    user = get_user(user_id)
    if not user:
        await update.message.reply_text("Я тебе ще не знаю 😿 Напиши мені щось, щоб ми познайомились!")
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

# ---------- DONE ----------
async def done(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    user = get_user(user_id)

    if not user:
        await update.message.reply_text("Я тебе ще не знаю 😿 Напиши мені щось!")
        return

    args = context.args
    if not args or not args[0].isdigit():
        await update.message.reply_text(
            "Вкажи номер справи, яку завершено, наприклад: `/done 1` ✅",
            parse_mode="Markdown"
        )
        return

    index = int(args[0]) - 1
    tasks = user.get("todo", [])
    if 0 <= index < len(tasks):
        completed = tasks.pop(index)
        db.update({"todo": tasks}, User.id == user_id)
        await update.message.reply_text(f"Справу «{completed['text']}» виконано! ✅")
    else:
        await update.message.reply_text("Номер справи недійсний 😿")

# ---------- ПОВІДОМЛЕННЯ ----------
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

# ---------- ЩОДЕННЕ ОЧИЩЕННЯ ----------
def clear_all_todos():
    users = db.all()
    for user in users:
        if "todo" in user:
            db.update({"todo": []}, User.id == user["id"])
    print("Щоденне очищення TODO виконано")

# ---------- ЗАПУСК ----------
app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("help", help_command))
app.add_handler(CommandHandler("todo", todo))
app.add_handler(CommandHandler("done", done))
app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))

scheduler = BackgroundScheduler(timezone="Europe/Kyiv")
scheduler.add_job(clear_all_todos, "cron", hour=0, minute=0)
scheduler.start()

print("✨ Хіна-Ботик з розумним TODO і /help запущено 🐾")
app.run_polling()
