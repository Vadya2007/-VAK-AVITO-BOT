import os
import requests
from bs4 import BeautifulSoup
from flask import Flask, request
import telebot
import threading
import time

# Токен бота и URL для Webhook из переменных окружения
TOKEN = os.environ.get("TOKEN")
WEBHOOK_URL = os.environ.get("WEBHOOK_URL")  # https://yourapp.onrender.com
bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

# Хранилище подписанных пользователей и отправленных ссылок
CHAT_IDS = set()
sent_links = set()

# Какие модели искать
VALID_MODELS = ["xs", "xr", "11", "12", "13", "14", "15", "pro", "pro max", "promax"]

# Ссылка на поиск iPhone в Уфе
SEARCH_URL = "https://www.avito.ru/ufa/telefony?q=iphone"

# Команда /start
@bot.message_handler(commands=["start"])
def start(message):
    CHAT_IDS.add(message.chat.id)
    bot.send_message(message.chat.id, "Ты подписан на новые объявления iPhone!")

# Webhook для Telegram
@app.route(f"/{TOKEN}", methods=["POST"])
def webhook():
    json_string = request.get_data().decode("utf-8")
    update = telebot.types.Update.de_json(json_string)
    bot.process_new_updates([update])
    return "!", 200

# Цикл проверки новых объявлений
def fetch_loop():
    while True:
        try:
            response = requests.get(SEARCH_URL)
            soup = BeautifulSoup(response.text, "html.parser")
            items = soup.find_all("div", {"data-marker": "item"})

            for item in items:
                title_tag = item.find("h3")
                price_tag = item.find("span", {"data-marker": "item-price"})
                link_tag = item.find("a", {"data-marker": "item-title"})

                if not title_tag or not price_tag or not link_tag:
                    continue

                title_lower = title_tag.get_text(strip=True).lower()
                price = price_tag.get_text(strip=True)
                link = "https://www.avito.ru" + link_tag.get("href")

                if not any(model in title_lower for model in VALID_MODELS):
                    continue

                if link in sent_links:
                    continue

                sent_links.add(link)
                message_text = f"{title_tag.get_text(strip=True)}\nЦена: {price}\nСсылка: {link}"

                for chat_id in CHAT_IDS:
                    bot.send_message(chat_id, message_text)
        except Exception as e:
            print("Ошибка при получении объявлений:", e)

        time.sleep(300)  # каждые 5 минут

if __name__ == "__main__":
    # Устанавливаем webhook
    bot.remove_webhook()
    bot.set_webhook(url=WEBHOOK_URL + "/" + TOKEN)

    # Запускаем fetch_loop в отдельном потоке
    threading.Thread(target=fetch_loop).start()

    # Запускаем Flask
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
