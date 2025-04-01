import os
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

TOKEN = os.getenv("8087039975:AAHilkGMZAIwQtglfaeApBHDpcNREqlpCNE")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Прив ку! Я бот Хіни 🌸")

app = ApplicationBuilder().token('8087039975:AAHilkGMZAIwQtglfaeApBHDpcNREqlpCNE').build()
app.add_handler(CommandHandler("start", start))

print("Бот запущено 🐾")
app.run_polling()
from telegram.ext import MessageHandler, filters
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.lower()

    if "привіт" in text or "хай" in text:
        await update.message.reply_text("Прив ку, я тебе чекала 🌷")

    elif "як справи" in text:
        await update.message.reply_text("Я мурчу стабільно 🐱 А ти як?")

    elif "ти хто" in text or "хто ти":
        await update.message.reply_text("Я Хіна-ботик. Я трохи божевільна, але мила 🤍")

    else:
        await update.message.reply_text("Я ще не знаю, що сказати на це 🥺")

# підключаємо цей обробник
app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))

