import os
import time
import threading
import requests
from flask import Flask, request
import telebot
from bs4 import BeautifulSoup

# ===== НАСТРОЙКИ =====
TOKEN = "8457178929:AAG9Nlej0WJgZ5Ry6m_F98FFPMry6LEdNx8"
WEBHOOK_URL = "https://vak-avito-bot.onrender.com/" + TOKEN
SEARCH_URL = "https://www.avito.ru/ufa/telefony?q=iphone"

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

subscribers = set()  # кто нажал /start
last_ads = []        # храним последние найденные объявления


# ===== ФУНКЦИЯ: парсинг Авито =====
def fetch_ads():
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(SEARCH_URL, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, "html.parser")

        ads = []
        for item in soup.select("div[itemtype='http://schema.org/Product']"):
            title = item.select_one("h3")
            price = item.select_one("meta[itemprop='price']")
            link = item.select_one("a[itemprop='url']")
            if not (title and price and link):
                continue

            name = title.text.strip()
            if any(model in name.lower() for model in ["xr", "xs", "11", "12", "13", "14", "15", "pro"]):
                url = "https://www.avito.ru" + link["href"]
                ads.append({
                    "title": name,
                    "price": price["content"] + " ₽",
                    "url": url
                })
        return ads
    except Exception as e:
        print("Ошибка парсинга:", e)
        return []


# ===== ФОНОВАЯ ПРОВЕРКА КАЖДЫЕ 5 МИНУТ =====
def background_task():
    global last_ads
    while True:
        ads = fetch_ads()
        new_ads = [ad for ad in ads if ad not in last_ads]
        if new_ads:
            last_ads = ads
            for ad in new_ads:
                text = f"📱 {ad['title']}\n💰 {ad['price']}\n🔗 {ad['url']}"
                for user in subscribers:
                    try:
                        bot.send_message(user, text)
                    except Exception as e:
                        print("Ошибка отправки:", e)
        time.sleep(300)  # 5 минут


# ===== ТЕЛЕГРАМ-КОМАНДЫ =====
@bot.message_handler(commands=["start"])
def start(message):
    subscribers.add(message.chat.id)
    bot.reply_to(message, "✅ Ты подписан на новые объявления iPhone по Уфе!")


# ===== FLASK WEBHOOK =====
@app.route("/" + TOKEN, methods=["POST"])
def webhook():
    update = telebot.types.Update.de_json(request.stream.read().decode("utf-8"))
    bot.process_new_updates([update])
    return "ok", 200


@app.route("/")
def index():
    return "Bot is running!"


# ===== СТАРТ =====
if __name__ == "__main__":
    # Запуск фонового потока
    threading.Thread(target=background_task, daemon=True).start()

    # Установка webhook
    bot.remove_webhook()
    time.sleep(1)
    bot.set_webhook(url=WEBHOOK_URL)

    # Запуск Flask
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
