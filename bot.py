from telethon import TelegramClient, events
import threading
import os
import re
import time
import subprocess

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

chromedriver_path = "/usr/bin/chromedriver"

# ---------------- Функции ----------------

def notify_linux(title, message):
    """Уведомление на Linux через notify-send"""
    try:
        subprocess.run(["notify-send", title, message])
    except FileNotFoundError:
        print(f"[NOTIFY] {title}: {message}")

def extract_links(text):
    """Извлекаем все ссылки из текста"""
    cleaned_text = text.replace("**", "")
    return re.findall(r"https?://[^\s]+", cleaned_text)

def type_text_slowly(element, text, delay=0.02):
    """Имитируем медленный ввод текста"""
    for ch in text:
        element.send_keys(ch)
        time.sleep(delay)

def find_button_by_text(driver, text_options, timeout=20):
    """Ищем кнопку по тексту (поддержка нескольких вариантов текста)"""
    wait = WebDriverWait(driver, timeout)
    for text in text_options:
        try:
            button = wait.until(
                EC.element_to_be_clickable((By.XPATH, f"//button[contains(text(), '{text}')]"))
            )
            return button
        except:
            continue
    return None

def open_link_and_click(url):
    """Открываем ссылку и автоматически делаем ставку"""
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    service = Service(chromedriver_path)
    driver = webdriver.Chrome(service=service, options=options)

    try:
        driver.get(url)
        time.sleep(2)  # Ждем подгрузки JS

        # 1️⃣ Найти и нажать кнопку "Сделать ставку"
        button1 = find_button_by_text(driver, ["Сделать ставку"])
        if not button1:
            print("⚠️ Кнопка 'Сделать ставку' не найдена на странице")
            return
        button1.click()
        print("✅ Кнопка 'Сделать ставку' нажата!")

        # 2️⃣ Ввод суммы и дней
        try:
            price_span = driver.find_element(By.CSS_SELECTOR, "span.text-green.bold.pull-right.price.with-tooltip.hidden-xs")
            price_digits = re.sub(r"[^\d]", "", price_span.text) or "1111"
        except:
            price_digits = "1111"
        try:
            amount_input = driver.find_element(By.ID, "amount-0")
            amount_input.clear()
            type_text_slowly(amount_input, price_digits)
        except:
            print("⚠️ Поле суммы не найдено, пропускаем")

        try:
            days_input = driver.find_element(By.ID, "days_to_deliver-0")
            days_input.clear()
            type_text_slowly(days_input, "3")
        except:
            print("⚠️ Поле дней не найдено, пропускаем")

        try:
            textarea = driver.find_element(By.ID, "comment-0")
            type_text_slowly(textarea, COMMENT_TEXT)
        except:
            print("⚠️ Поле комментария не найдено, пропускаем")

        # 3️⃣ Нажать кнопку "Добавить" (раньше была "Сделать ставку")
        button2 = find_button_by_text(driver, ["Добавить", "Сделать ставку"])
        if button2:
            button2.click()
            print("✅ Кнопка 'Добавить' нажата! Задача выполнена.")
        else:
            print("⚠️ Кнопка 'Добавить' не найдена")

        time.sleep(2)

    except Exception as e:
        print(f"❌ Ошибка в open_link_and_click: {e}")
    finally:
        driver.quit()

# ---------------- Телеграм ----------------

client = TelegramClient("session", api_id, api_hash)

@client.on(events.NewMessage)
async def handler(event):
    message_text = (event.message.text or "").lower()
    if any(keyword in message_text for keyword in KEYWORDS):
        print(f"🔔 Нашёл проект: {message_text[:100]}")

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
