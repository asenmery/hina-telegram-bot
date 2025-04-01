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
