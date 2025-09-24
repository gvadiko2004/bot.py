from telethon import TelegramClient, events
import threading
import os
import re
import time
import subprocess
import sys

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options

# ==== Настройки Telegram ====
api_id = 21882740
api_hash = "c80a68894509d01a93f5acfeabfdd922"

KEYWORDS = [
    "#html_и_css_верстка",
    "#веб_программирование",
    "#cms",
    "#интернет_магазины_и_электронная_коммерция",
    "#создание_сайта_под_ключ",
    "#дизайн_сайтов"
]
KEYWORDS = [kw.lower() for kw in KEYWORDS]

COMMENT_TEXT = """Доброго дня! 

Я ознайомився із завданням і готовий приступити до якісного виконання завдання

Стек: Figma (Дизайн) / html (bem), scss, js / WordPress ACF PRO

Щоб ви були впевнені, що під час роботи не виникне проблем, можете ознайомитися з моєю останньою роботою:

https://telya.ch/

Також наводжу посилання на інші проекти:

https://gvadiko2004.github.io/grill/
https://gvadiko2004.github.io/Anon-shop/
https://iliarchie.github.io/cates/

Якщо вас зацікавив мій відгук, зв'яжіться зі мною в особистих повідомленнях.

Заздалегідь дякую"""

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
chromedriver_path = "/usr/bin/chromedriver"

# ---------------- Функции ----------------

def notify_linux(title, message):
    """Безопасное уведомление на Linux через notify-send"""
    try:
        subprocess.run(["notify-send", title, message])
    except FileNotFoundError:
        print(f"[NOTIFY] {title}: {message}")

def play_sound_thread():
    """Заглушка для звука (можно добавить воспроизведение через plyer)"""
    pass

def extract_links(text):
    """Извлечение ссылок из текста"""
    cleaned_text = text.replace("**", "")
    return re.findall(r"https?://[^\s]+", cleaned_text)

def type_text_slowly(element, text, delay=0.02):
    """Печать текста в поле по символу"""
    for ch in text:
        element.send_keys(ch)
        time.sleep(delay)

def open_link_and_click(url):
    """Открытие ссылки и заполнение формы через Selenium"""
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    service = Service(chromedriver_path)
    driver = webdriver.Chrome(service=service, options=options)

    try:
        driver.get(url)
        time.sleep(5)  # дождаться полной загрузки
        wait = WebDriverWait(driver, 20)

        # Кнопка "Сделать ставку"
        try:
            button = wait.until(EC.element_to_be_clickable((By.ID, "add-bid")))
            button.click()
            print("✅ Кнопка 'Сделать ставку' нажата!")
        except Exception:
            print("⚠️ Кнопка 'Сделать ставку' не найдена на странице")
            with open("debug_page.html", "w", encoding="utf-8") as f:
                f.write(driver.page_source)
            return

        # Сумма заказа
        try:
            price_span = wait.until(EC.presence_of_element_located((
                By.CSS_SELECTOR,
                "span.text-green.bold.pull-right.price.with-tooltip.hidden-xs"
            )))
            raw_price = price_span.text
            price_digits = re.sub(r"[^\d]", "", raw_price) or "1111"
        except Exception:
            price_digits = "1111"

        # Ввод суммы
        try:
            amount_input = wait.until(EC.element_to_be_clickable((By.ID, "amount-0")))
            amount_input.clear()
            type_text_slowly(amount_input, price_digits)
        except Exception:
            print("⚠️ Поле для суммы не найдено")

        # Ввод дней
        try:
            days_input = wait.until(EC.element_to_be_clickable((By.ID, "days_to_deliver-0")))
            days_input.clear()
            type_text_slowly(days_input, "3")
        except Exception:
            print("⚠️ Поле для дней не найдено")

        # Ввод комментария
        try:
            textarea = wait.until(EC.element_to_be_clickable((By.ID, "comment-0")))
            type_text_slowly(textarea, COMMENT_TEXT)
        except Exception:
            print("⚠️ Поле для комментария не найдено")

        # Кнопка "Добавить"
        try:
            submit_btn = wait.until(EC.element_to_be_clickable((
                By.CSS_SELECTOR,
                "button#add-0.btn.btn-primary.btn-lg.ladda-button"
            )))
            submit_btn.click()
            print("✅ Кнопка 'Добавить' нажата! Задача выполнена.")
        except Exception:
            print("⚠️ Кнопка 'Добавить' не найдена")

        time.sleep(3)

    except Exception as e:
        print(f"❌ Ошибка в open_link_and_click: {e}")
        with open("debug_page.html", "w", encoding="utf-8") as f:
            f.write(driver.page_source)
    finally:
        driver.quit()

# ---------------- Телеграм ----------------

client = TelegramClient("session", api_id, api_hash)

@client.on(events.NewMessage)
async def handler(event):
    message_text = (event.message.text or "").lower()
    if any(keyword in message_text for keyword in KEYWORDS):
        print(f"🔔 Нашёл проект: {message_text[:100]}")

        play_sound_thread()
        notify_linux("Новый проект на Freelancehunt!", message_text[:150])

        links = extract_links(message_text)
        if links:
            print(f"🌐 Открываю и кликаю по ссылке: {links[0]}")
            threading.Thread(target=open_link_and_click, args=(links[0],), daemon=True).start()

# ---------------- Запуск ----------------

if __name__ == "__main__":
    print("✅ Бот запущен, ждёт сообщения...")
    client.start()
    client.run_until_disconnected()
