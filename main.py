import os
import time
import threading
import requests
from bs4 import BeautifulSoup
import telebot
from flask import Flask

# ===== Telegram Bot =====
TOKEN = os.getenv("TOKEN")
if not TOKEN:
    raise ValueError("TOKEN не найден!")

bot = telebot.TeleBot(TOKEN)

# ===== Flask Ping Server =====
app = Flask("")

@app.route("/")
def home():
    return "Bot is running!"

def run_flask():
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

threading.Thread(target=run_flask).start()

# ===== Подписчики =====
subscribers = set()

@bot.message_handler(commands=["start"])
def start_message(message):
    subscribers.add(message.chat.id)
    bot.send_message(message.chat.id, "Ты подписан на новые объявления iPhone!")

# ===== Настройки Авито =====
URL = "https://www.avito.ru/ufa/telefony?q=iphone"
CHECK_INTERVAL = 300  # 5 минут
ALREADY_SENT = set()

# Список моделей iPhone для поиска
IPHONES = [
    "iPhone XS", "iPhone XS Max", "iPhone XR",
    "iPhone 11", "iPhone 11 Pro", "iPhone 11 Pro Max",
    "iPhone 12", "iPhone 12 Mini", "iPhone 12 Pro", "iPhone 12 Pro Max",
    "iPhone 13", "iPhone 13 Mini", "iPhone 13 Pro", "iPhone 13 Pro Max",
    "iPhone 14", "iPhone 14 Plus", "iPhone 14 Pro", "iPhone 14 Pro Max",
    "iPhone 15", "iPhone 15 Plus", "iPhone 15 Pro", "iPhone 15 Pro Max"
]

def check_avito():
    while True:
        try:
            headers = {"User-Agent": "Mozilla/5.0"}
            r = requests.get(URL, headers=headers)
            soup = BeautifulSoup(r.text, "html.parser")

            ads = soup.find_all("a", {"class": "iva-item-titleStep-2bjuh"})
            for ad in ads:
                title = ad.text.strip()
                link = "https://www.avito.ru" + ad.get("href")
                if any(model in title for model in IPHONES) and link not in ALREADY_SENT:
                    for user_id in subscribers:
                        bot.send_message(user_id, f"{title}\n{link}")
                    ALREADY_SENT.add(link)
        except Exception as e:
            print("Ошибка при парсинге:", e)
        time.sleep(CHECK_INTERVAL)

# ===== Запуск парсинга =====
threading.Thread(target=check_avito).start()

# ===== Запуск бота =====
bot.infinity_polling()
