import telebot
from flask import Flask, request
import requests
import time
import threading
from bs4 import BeautifulSoup

# === НАСТРОЙКИ ===
BOT_TOKEN = "8457178929:AAG9Nlej0WJgZ5Ry6m_F98FFPMry6LEdNx8"
WEBHOOK_URL = "https://vak-avito-bot.onrender.com/" + BOT_TOKEN
CHAT_ID = None  # сюда бот добавит id того, кто напишет /start

bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)

# === ПОИСК ОБЪЯВЛЕНИЙ ===
def get_iphones():
    url = "https://www.avito.ru/ufa"
    params = {"q": "iPhone"}
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(url, params=params, headers=headers)
    soup = BeautifulSoup(response.text, "html.parser")

    ads = []
    models = ["xr", "xs", "11", "12", "13", "14", "15", "pro", "pro max"]

    for item in soup.select('div[data-marker="item"]'):
        title_tag = item.select_one('h3[itemprop="name"]')
        price_tag = item.select_one('meta[itemprop="price"]')
        link_tag = item.select_one('a[itemprop="url"]')

        if not (title_tag and price_tag and link_tag):
            continue

        title = title_tag.text.strip().lower()
        price = price_tag.get("content", "Цена не указана")
        link = "https://www.avito.ru" + link_tag.get("href", "")

        if any(model in title for model in models):
            ads.append(f"📱 {title.title()}\n💸 {price} ₽\n🔗 {link}")

    return ads if ads else ["Пока ничего нового нет 😔"]

# === ОТПРАВКА ОБЪЯВЛЕНИЙ ===
def monitor_ads():
    last_ads = set()
    while True:
        iphones = get_iphones()
        new_ads = set(iphones) - last_ads
        if new_ads and CHAT_ID:
            for ad in new_ads:
                bot.send_message(CHAT_ID, ad)
        last_ads = set(iphones)
        time.sleep(300)  # каждые 5 минут

# === ТЕЛЕГРАМ КОМАНДЫ ===
@bot.message_handler(commands=['start'])
def start(message):
    global CHAT_ID
    CHAT_ID = message.chat.id
    bot.send_message(CHAT_ID, "🔔 Подписка активна! Буду слать новые объявления по айфонам в Уфе 💥")
    threading.Thread(target=monitor_ads, daemon=True).start()

# === FLASK (для Webhook) ===
@app.route('/' + BOT_TOKEN, methods=['POST'])
def getMessage():
    json_str = request.stream.read().decode('UTF-8')
    update = telebot.types.Update.de_json(json_str)
    bot.process_new_updates([update])
    return '!', 200

@app.route("/")
def webhook():
    bot.remove_webhook()
    bot.set_webhook(url=WEBHOOK_URL)
    return "Webhook установлен!", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
