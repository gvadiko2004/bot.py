import os
import pickle
import re
import sys
import time
import random
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager
from telethon import TelegramClient, events

# ===== Настройки Telegram =====
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
COOKIES_FILE = "fh_cookies.pkl"

# ---------------- Функции ----------------
def extract_links(text):
    return re.findall(r"https?://[^\s]+", text)

def load_cookies(driver, url):
    if os.path.exists(COOKIES_FILE):
        with open(COOKIES_FILE, "rb") as f:
            cookies = pickle.load(f)
        driver.get(url)
        for cookie in cookies:
            try:
                driver.add_cookie(cookie)
            except:
                pass
        driver.refresh()
        return True
    return False

def human_type(element, text, delay_range=(0.05, 0.15)):
    """Имитируем набор текста как человек"""
    for char in text:
        element.send_keys(char)
        time.sleep(random.uniform(*delay_range))

def move_to_element_smoothly(driver, element, steps=20):
    """Имитируем движение мышки к элементу"""
    from selenium.webdriver.common.action_chains import ActionChains
    loc = element.location_once_scrolled_into_view
    size = element.size
    x_target = loc['x'] + size['width'] // 2
    y_target = loc['y'] + size['height'] // 2

    action = ActionChains(driver)
    for i in range(steps):
        action.move_by_offset(x_target/steps, y_target/steps)
    action.move_to_element(element)
    action.perform()
    time.sleep(random.uniform(0.2, 0.5))

def make_bid(url):
    chrome_options = Options()
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument(f"--user-data-dir={PROFILE_PATH}")
    chrome_options.add_argument("--start-maximized")
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("--disable-gpu")

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    wait = WebDriverWait(driver, 30)

    try:
        driver.get(url)
        wait.until(lambda d: d.execute_script("return document.readyState") == "complete")
        print(f"[INFO] Страница проекта загружена: {url}")

        load_cookies(driver, url)

        # Нажимаем "Сделать ставку"
        bid_btn = wait.until(EC.element_to_be_clickable((By.ID, "add-bid")))
        move_to_element_smoothly(driver, bid_btn)
        bid_btn.click()
        print("[INFO] Нажата кнопка 'Сделать ставку'")
        time.sleep(random.uniform(0.5, 1.0))

        # Ввод суммы
        try:
            price_span = wait.until(EC.presence_of_element_located((
                By.CSS_SELECTOR, "span.text-green.bold.pull-right.price.with-tooltip.hidden-xs"
            )))
            price = re.sub(r"[^\d]", "", price_span.text) or "1111"
        except:
            price = "1111"

        amount_input = wait.until(EC.element_to_be_clickable((By.ID, "amount-0")))
        move_to_element_smoothly(driver, amount_input)
        amount_input.clear()
        human_type(amount_input, price)

        days_input = wait.until(EC.element_to_be_clickable((By.ID, "days_to_deliver-0")))
        move_to_element_smoothly(driver, days_input)
        days_input.clear()
        human_type(days_input, "3")

        comment_area = wait.until(EC.presence_of_element_located((By.ID, "comment-0")))
        move_to_element_smoothly(driver, comment_area)
        comment_area.clear()
        human_type(comment_area, COMMENT_TEXT)
        print("[INFO] Поля формы заполнены")

        # Имитируем движение мышки и клик на кнопку 'Добавить'
        submit_btn = wait.until(EC.element_to_be_clickable((By.ID, "add-0")))
        move_to_element_smoothly(driver, submit_btn)
        submit_btn.click()
        print("[SUCCESS] Заявка отправлена кнопкой 'Добавить'")

    except (TimeoutException, NoSuchElementException) as e:
        print(f"[ERROR] Не удалось сделать ставку: {e}")

    print("[INFO] Браузер оставлен открытым для проверки.")

# ---------------- Телеграм ----------------
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
            print("[INFO] Готов к следующему проекту")

# ---------------- Запуск ----------------
if __name__ == "__main__":
    print("[INFO] Бот запущен. Ожидаем новые проекты...")
    client.start()
    client.run_until_disconnected()
