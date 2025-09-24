import os
import re
import threading
import time
import random

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import ElementClickInterceptedException, TimeoutException
from selenium.webdriver.chrome.options import Options
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

# ---------------- Глобальные переменные ----------------
driver = None
wait = None

# ---------------- Инициализация браузера с постоянным профилем ----------------
def init_driver():
    global driver, wait
    chrome_options = Options()
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")

    # Путь к постоянному профилю
    profile_path = "/home/user/chrome_profile"  # замени на свой путь
    chrome_options.add_argument(f"--user-data-dir={profile_path}")

    # Если нужно дополнительно подгружать расширение:
    # chrome_options.add_argument("--load-extension=/path/to/anticaptcha_extension")

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    wait = WebDriverWait(driver, 30)
    print("[INFO] Браузер запущен с постоянным профилем")

# ---------------- Функции ----------------
def extract_links(text):
    return re.findall(r"https?://[^\s]+", text)

def click_element_safe(element, retries=5, delay=0.5):
    for _ in range(retries):
        try:
            element.click()
            return True
        except ElementClickInterceptedException:
            driver.execute_script("arguments[0].click();", element)
            return True
        except:
            time.sleep(delay)
    return False

def insert_comment():
    comment_area = wait.until(EC.presence_of_element_located((By.ID, "comment-0")))
    comment_area.clear()
    for ch in COMMENT_TEXT:
        comment_area.send_keys(ch)
        time.sleep(0.08 + 0.1 * random.random())
    entered_text = comment_area.get_attribute("value")
    if entered_text.strip() == COMMENT_TEXT.strip():
        print("[INFO] Комментарий введен корректно")
    else:
        print("[WARN] Комментарий может быть неполным")

def wait_for_add_button():
    while True:
        try:
            add_btn = driver.find_element(By.ID, "btn-submit-0")
            if add_btn.is_enabled() and add_btn.is_displayed():
                return add_btn
        except:
            pass
        time.sleep(0.5)

def make_bid(url):
    try:
        driver.get(url)
        wait.until(lambda d: d.execute_script("return document.readyState") == "complete")
        print(f"[INFO] Обрабатываем проект: {url}")

        # Кнопка "Сделать ставку"
        bid_btn = wait.until(EC.element_to_be_clickable((By.ID, "add-bid")))
        click_element_safe(bid_btn)
        print("[INFO] Кнопка 'Сделать ставку' нажата")

        # Ввод цены
        try:
            price_span = wait.until(EC.presence_of_element_located((
                By.CSS_SELECTOR, "span.text-green.bold.pull-right.price.with-tooltip.hidden-xs"
            )))
            price = re.sub(r"[^\d]", "", price_span.text) or "1111"
        except:
            price = "1111"
        amount_input = wait.until(EC.element_to_be_clickable((By.ID, "amount-0")))
        amount_input.clear()
        amount_input.send_keys(price)

        # Ввод сроков
        days_input = wait.until(EC.element_to_be_clickable((By.ID, "days_to_deliver-0")))
        days_input.clear()
        days_input.send_keys("3")

        # Ввод комментария
        insert_comment()

        # Кнопка "Добавить" после прохождения капчи
        add_btn = wait_for_add_button()
        click_element_safe(add_btn, retries=5, delay=1)
        print("[INFO] Ставка успешно отправлена!")

    except TimeoutException as e:
        print(f"[ERROR] Ошибка при сделке ставки: {e}")

def process_project(url):
    threading.Thread(target=make_bid, args=(url,), daemon=True).start()

# ---------------- Телеграм ----------------
client = TelegramClient("session", api_id, api_hash)

@client.on(events.NewMessage)
async def handler(event):
    text = (event.message.text or "").lower()
    if any(k in text for k in KEYWORDS):
        print(f"[INFO] Новый проект: {text[:100]}")
        links = extract_links(text)
        if links:
            process_project(links[0])

# ---------------- Запуск ----------------
if __name__ == "__main__":
    print("[INFO] Запускаем браузер...")
    init_driver()
    print("[INFO] Бот запущен. Ожидаем новые проекты...")
    client.start()
    client.run_until_disconnected()
