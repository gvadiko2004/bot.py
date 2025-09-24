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
from selenium.common.exceptions import TimeoutException, ElementClickInterceptedException
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

Стек: Figma / html (bem), scss, js / WordPress ACF PRO

Мої роботи:
https://telya.ch/
https://gvadiko2004.github.io/grill/
https://gvadiko2004.github.io/Anon-shop/
https://iliarchie.github.io/cates/

Зв'яжіться зі мною в особистих повідомленнях.
Заздалегідь дякую"""

chromedriver_path = "/usr/bin/chromedriver"  # путь к ChromeDriver
remote_debug_port = 9222  # порт remote debugging

# ---------------- Функции ----------------
def notify_linux(title, message):
    try:
        subprocess.run(["notify-send", title, message])
        print(f"[NOTIFY] {title}: {message}")
    except FileNotFoundError:
        print(f"[NOTIFY] {title}: {message} (notify-send не найден)")

def type_text_slowly(element, text, delay=0.02):
    for ch in text:
        element.send_keys(ch)
        time.sleep(delay)

def extract_links(text):
    cleaned_text = text.replace("**", "")
    return re.findall(r"https?://[^\s]+", cleaned_text)

def open_link_and_click(url):
    options = Options()
    options.debugger_address = f"127.0.0.1:{remote_debug_port}"  # подключение к уже запущенному Chrome
    driver = webdriver.Chrome(service=Service(chromedriver_path), options=options)
    wait = WebDriverWait(driver, 20)

    try:
        driver.get(url)
        print(f"🌐 Открыта страница: {url}")

        # --- Находим кнопку "Сделать ставку" ---
        button = None
        try:
            button = wait.until(EC.element_to_be_clickable((By.ID, "add-bid")))
        except TimeoutException:
            try:
                button = wait.until(EC.element_to_be_clickable(
                    (By.XPATH, '//a[contains(text(),"Сделать ставку")]')
                ))
            except TimeoutException:
                print("❌ Кнопка 'Сделать ставку' не найдена")
                return

        try:
            button.click()
            print("✅ Кнопка 'Сделать ставку' нажата!")
        except ElementClickInterceptedException:
            driver.execute_script("arguments[0].click();", button)
            print("✅ Кнопка 'Сделать ставку' нажата через JS!")

        time.sleep(2)

        # --- Ввод суммы ---
        try:
            price_span = wait.until(EC.presence_of_element_located((
                By.CSS_SELECTOR,
                "span.text-green.bold.pull-right.price.with-tooltip.hidden-xs"
            )))
            raw_price = price_span.text
            price_digits = re.sub(r"[^\d]", "", raw_price) or "1111"
        except Exception:
            price_digits = "1111"

        amount_input = wait.until(EC.element_to_be_clickable((By.ID, "amount-0")))
        amount_input.clear()
        type_text_slowly(amount_input, price_digits)

        # --- Ввод дней ---
        days_input = wait.until(EC.element_to_be_clickable((By.ID, "days_to_deliver-0")))
        days_input.clear()
        type_text_slowly(days_input, "3")

        # --- Ввод комментария ---
        textarea = wait.until(EC.element_to_be_clickable((By.ID, "comment-0")))
        type_text_slowly(textarea, COMMENT_TEXT)

        # --- Нажатие кнопки "Добавить" ---
        try:
            submit_btn = wait.until(EC.element_to_be_clickable(
                (By.XPATH, '//button[contains(text(),"Добавить")]')
            ))
            submit_btn.click()
            print("✅ Кнопка 'Добавить' нажата! Задача выполнена.")
        except TimeoutException:
            print("⚠️ Кнопка 'Добавить' не найдена")

        time.sleep(2)

    except Exception as e:
        print(f"❌ Ошибка в open_link_and_click: {e}")

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
