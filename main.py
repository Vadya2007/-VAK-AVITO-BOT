import telebot
from flask import Flask, request
import requests
import time
import threading

# === НАСТРОЙКИ ===
BOT_TOKEN = "8457178929:AAG9Nlej0WJgZ5Ry6m_F98FFPMry6LEdNx8"
WEBHOOK_URL = "https://vak-avito-bot.onrender.com/" + BOT_TOKEN
CHAT_ID = None  # сюда бот сам добавит id того, кто напишет /start

bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)

# === ПОИСК ОБЪЯВЛЕНИЙ ===
def get_iphones():
    url = "https://www.avito.ru/ufa"
    params = {
        "q": "iPhone",
    }
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(url, params=params, headers=headers)
    text = response.text.lower()
    iphones = []
    models = ["xr", "xs", "11", "12", "13", "14", "15", "pro", "pro max"]
    for model in models:
        if model in text:
            iphones.append(f"Найдено объявление с моделью iPhone {model.upper()}")
    return iphones if iphones else ["Пока ничего нового нет 😔"]

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
    bot.send_message(CHAT_ID, "🔔 Ты подписан на новые объявления iPhone в Уфе!")
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
