import os
import telebot
import requests
from bs4 import BeautifulSoup
from flask import Flask, request

# ==== ПЕРЕМЕННЫЕ ОКРУЖЕНИЯ ====
TOKEN = os.environ.get("TOKEN")
WEBHOOK_URL = os.environ.get("WEBHOOK_URL")  # https://vak-avito-bot.onrender.com
bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

# ==== Функция поиска свежих объявлений iPhone ====
def get_new_iphones():
    url = "https://www.avito.ru/ufa/telefony/iphone?cd=1&q=iphone+xs+iphone+xr+iphone+11+iphone+12+iphone+13+iphone+14+iphone+15+pro+max"
    headers = {
        "User-Agent": "Mozilla/5.0"
    }
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, "html.parser")
    ads = []

    # Находим блоки с объявлениями
    for item in soup.find_all("div", {"data-marker": "item"}):
        try:
            title_tag = item.find("h3")
            price_tag = item.find("span", {"data-marker": "item-price"})
            link_tag = item.find("a", {"class": "iva-item-titleLink"})

            if title_tag and price_tag and link_tag:
                title = title_tag.text.strip()
                price = price_tag.text.strip()
                link = "https://www.avito.ru" + link_tag.get("href")
                ads.append(f"{title}\nЦена: {price}\nСсылка: {link}")
        except:
            continue

    return ads[:5]  # берем 5 последних объявлений

# ==== Хендлер команды /start ====
@bot.message_handler(commands=["start"])
def start(message):
    chat_id = message.chat.id
    bot.send_message(chat_id, "Ты подписан на новые объявления iPhone в Уфе!")
    new_ads = get_new_iphones()
    for ad in new_ads:
        bot.send_message(chat_id, ad)

# ==== Webhook endpoint ====
@app.route(f"/{TOKEN}", methods=["POST"])
def webhook():
    json_string = request.get_data().decode("utf-8")
    update = telebot.types.Update.de_json(json_string)
    bot.process_new_updates([update])
    return "OK", 200

# ==== Главная страница для проверки ====
@app.route("/", methods=["GET"])
def index():
    return "Bot is running!", 200

# ==== Настройка webhook при запуске ====
if __name__ == "__main__":
    bot.remove_webhook()
    bot.set_webhook(url=f"{WEBHOOK_URL}/{TOKEN}")
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
