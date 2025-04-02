import datetime
import pytz
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

# 🔐 Твій токен — працює напряму
TOKEN = "8087039975:AAHilkGMZAIwQtglfaeApBHDpcNREqlpCNE"

# /start з кнопочками
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        ["Обійми", "Скажи щось миле"],
        ["Скільки зараз часу", "Котик 🐱"]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text("Прив ку! Обери кнопку ⤵️", reply_markup=reply_markup)

# реакції на повідомлення
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.lower()

    if "обійми" in text:
        await update.message.reply_text("🤗 *мʼякі обійми для тебе, мур!*")

    elif "скажи щось миле" in text:
        await update.message.reply_text("Ти найпрекрасніше створіння цього дня 🥹💗")

    elif "час" in text or "година" in text:
        kyiv_time = datetime.datetime.now(pytz.timezone("Europe/Kyiv")).strftime("%H:%M")
        await update.message.reply_text(f"Зараз в Україні: {kyiv_time} 🕰️")

    elif "котик" in text:
        await update.message.reply_animation("https://media.giphy.com/media/JIX9t2j0ZTN9S/giphy.gif")

    else:
        await update.message.reply_text("Мур? Я ще не знаю ці слова 🥺")

# запуск бота
app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))

print("Бот запущено з кнопочками, авою й гіфкою 🐾")
app.run_polling()
