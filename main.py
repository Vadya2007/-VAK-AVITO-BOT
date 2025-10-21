import os
import threading
import telebot
from flask import Flask

# ===== Telegram Bot =====
TOKEN = os.getenv("TOKEN")
if not TOKEN:
    raise ValueError("Telegram TOKEN не найден!")

bot = telebot.TeleBot(TOKEN)

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.send_message(message.chat.id, "Привет! Бот работает ✅")

# ===== Flask Ping Server =====
app = Flask("")

@app.route("/")
def home():
    return "Bot is running!"

def run_flask():
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

threading.Thread(target=run_flask).start()

# ===== Запуск бота =====
bot.infinity_polling()
