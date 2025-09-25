import os
import re
import time
import sys
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver import ActionChains
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager
from telethon import TelegramClient, events

# ===== Telegram настройки =====
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

COMMENT_TEXT = """Доброго дня! Готовий виконати роботу якісно.
Портфоліо робіт у моєму профілі.
Заздалегідь дякую!
"""

PROFILE_PATH = "/home/user/chrome_profile"

# ================= Вспомогательные функции =================
def extract_links(text: str):
    return re.findall(r"https?://[^\s]+", text)

def send_tab_and_enter(driver):
    """Имитация 6 TAB + ENTER с логированием каждого шага"""
    try:
        actions = ActionChains(driver)
        for i in range(1, 7):
            actions.send_keys(Keys.TAB)
            actions.perform()
            print(f"[INFO] TAB нажата {i} раз")
            time.sleep(0.3)
        actions.send_keys(Keys.ENTER)
        actions.perform()
        print("[INFO] ENTER нажата после 6 TAB")
    except Exception as e:
        print(f"[ERROR] TAB+ENTER не спрацював: {e}")

# ================= Основная логика =================
def make_bid(url):
    chrome_options = Options()
    chrome_options.add_argument("--start-maximized")
    chrome_options.add_argument(f"--user-data-dir={PROFILE_PATH}")
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    wait = WebDriverWait(driver, 30)

    try:
        driver.get(url)
        print(f"[INFO] Загружена страница проекта: {url}")
        print("[INFO] Если нужно — авторизуйтесь вручную в браузере.")
        time.sleep(15)  # время для ручной авторизации

        # Кнопка "Сделать ставку"
        bid_button = wait.until(EC.element_to_be_clickable((By.ID, "add-bid")))
        bid_button.click()
        print("[INFO] Кнопка 'Сделать ставку' натиснута")
        time.sleep(2)

        # Ввод суммы
        try:
            price_span = wait.until(EC.presence_of_element_located((
                By.CSS_SELECTOR, "span.text-green.bold.pull-right.price.with-tooltip.hidden-xs"
            )))
            price = ''.join(filter(str.isdigit, price_span.text)) or "1111"
        except:
            price = "1111"

        amount_input = wait.until(EC.element_to_be_clickable((By.ID, "amount-0")))
        amount_input.clear()
        amount_input.send_keys(price)
        print(f"[INFO] Сумма введена: {price}")

        # Ввод дней
        days_input = wait.until(EC.element_to_be_clickable((By.ID, "days_to_deliver-0")))
        days_input.clear()
        days_input.send_keys("3")
        print("[INFO] Количество дней введено: 3")

        # Ввод комментария
        comment_area = wait.until(EC.presence_of_element_located((By.ID, "comment-0")))
        driver.execute_script("arguments[0].value = arguments[1];", comment_area, COMMENT_TEXT)
        print("[INFO] Коментар вставлений")

        # Имитируем TAB x6 + ENTER с логированием
        send_tab_and_enter(driver)

        print("[SUCCESS] Ставка отправлена (или попытка выполнена)")
        print("[INFO] Браузер оставляем открытым для проверки/повторной ставки.")

    except Exception as e:
        print(f"[ERROR] Не удалось сделать ставку: {e}")

# ================= Телеграм =================
client = TelegramClient("session", api_id, api_hash)

@client.on(events.NewMessage)
async def handler(event):
    text = (event.message.text or "").lower()
    if any(k in text for k in KEYWORDS):
        print(f"[INFO] Найдено сообщение по ключу: {text[:100]}")
        links = extract_links(text)
        if links:
            print(f"[INFO] Подходит ссылка: {links[0]}")
            make_bid(links[0])

# ================= Запуск =================
if __name__ == "__main__":
    print("[INFO] Бот запущен. Очікуємо нові проекти...")
    client.start()
    client.run_until_disconnected()
