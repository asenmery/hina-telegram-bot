import datetime
import pytz
from tinydb import TinyDB, Query
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
from apscheduler.schedulers.background import BackgroundScheduler
import asyncio

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
        "• Обіймати, муркати і котика давати \U0001F431\n"
        "• Нагадати випити водички: `/hydrate` або автоматично 💧\n\n"
        "\U0001F4CB *Команди:*\n"
        "/start — показати кнопки\n"
        "/todo — список справ\n"
        "/done — відмітити справу виконаною\n"
        "/hydrate — випити води 💧\n"
        "/profile — профіль\n"
        "/help — ця довідка\n\n"
        "\U0001F9E0 Я запамʼятовую твоє імʼя і стать, щоб спілкуватись з тобою з любовʼю \U0001F4AA"
    )
    await update.message.reply_text(text, parse_mode="Markdown")

# ---------- КОМАНДА /hydrate ----------
async def hydrate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    user = get_user(user_id)
    name = user.get("name") if user else None
    gender = user.get("gender") if user else None
    short = gendered(name, gender)

    await update.message.reply_text(
        f"{short}, нагадую випити склянку водички 💧\n"
        "Твоє тіло — твій храм, навіть у лапках 🐾"
    )

# ---------- ЩОДЕННЕ ОЧИЩЕННЯ ----------
def clear_all_todos():
    users = db.all()
    for user in users:
        if "todo" in user:
            db.update({"todo": []}, User.id == user["id"])
    print("Щоденне очищення TODO виконано")

# ---------- НАГАДУВАННЯ ПРО ВОДУ ----------
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

# ---------- ЗАПУСК ----------
app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("help", help_command))
app.add_handler(CommandHandler("todo", todo))
app.add_handler(CommandHandler("done", done))
app.add_handler(CommandHandler("hydrate", hydrate))
app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))

scheduler = BackgroundScheduler(timezone="Europe/Kyiv")
scheduler.add_job(clear_all_todos, "cron", hour=0, minute=0)
scheduler.add_job(lambda: asyncio.create_task(send_hydrate_reminder(app)), "cron", hour="10,14,18")
scheduler.start()

print("✨ Хіна-Ботик запущено з TODO, /help, /hydrate та нагадуванням пити воду 🐾")
app.run_polling()