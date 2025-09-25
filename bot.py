import os
import pickle
import re
import threading
import time

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

from webdriver_manager.chrome import ChromeDriverManager
from telethon import TelegramClient, events

# ========== Telegram API ==========
api_id = 21882740
api_hash = "c80a68894509d01a93f5acfeabfdd922"

# ========== Настройки ==========
KEYWORDS = [
    "#html_и_css_верстка",
    "#веб_программирование",
    "#cms",
    "#интернет_магазины_и_электронная_коммерция",
    "#создание_сайта_под_ключ",
    "#дизайн_сайтов"
]

COMMENT_TEXT = """Доброго дня! Готовий виконати роботу якісно.
Портфоліо робіт у моєму профілі.
Заздалегідь дякую!"""

DAYS = "3"
COST = "1111"

# Путь к пользовательскому профилю Chrome (создастся автоматически при первом запуске)
PROFILE_PATH = "/home/root/chrome_profile"  # замените 'username' на имя пользователя на вашем VPS
COOKIES_FILE = "fh_cookies.pkl"

# ========== Подключение к Telegram ==========
client = TelegramClient("session_name", api_id, api_hash)

# ========== Вспомогательные функции ==========

def extract_links(text):
    return re.findall(r'https?://[^\s*<>"]+', text)

def save_cookies(driver):
    with open(COOKIES_FILE, "wb") as f:
        pickle.dump(driver.get_cookies(), f)
        print("[INFO] Cookies сохранены")

def load_cookies(driver, url):
    if os.path.exists(COOKIES_FILE):
        driver.get(url)
        with open(COOKIES_FILE, "rb") as f:
            cookies = pickle.load(f)
        for cookie in cookies:
            try:
                driver.add_cookie(cookie)
            except:
                pass
        driver.refresh()
        print("[INFO] Cookies загружены")
        return True
    return False

def wait_for_login(driver, wait):
    print("[INFO] Ожидание авторизации вручную...")
    for _ in range(60):
        try:
            if driver.find_element(By.ID, "add-bid").is_displayed():
                print("[INFO] Авторизация подтверждена")
                save_cookies(driver)
                return
        except:
            time.sleep(1)
    print("[WARN] Не удалось подтвердить авторизацию")

# ========== Основная логика ==========

def make_bid(url):
    print(f"[INFO] Обработка ссылки: {url}")

    chrome_options = Options()
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument(f"--user-data-dir={PROFILE_PATH}")
    chrome_options.add_argument("--start-maximized")

    # Без headless, чтобы был видим хром
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    wait = WebDriverWait(driver, 30)

    try:
        driver.get(url)
        wait.until(lambda d: d.execute_script("return document.readyState") == "complete")

        load_cookies(driver, url)
        wait_for_login(driver, wait)

        # Первый клик
        bid_btn = wait.until(EC.element_to_be_clickable((By.ID, "add-bid")))
        driver.execute_script("arguments[0].click();", bid_btn)
        print("[INFO] Кнопка 'Сделать ставку' нажата")

        # Комментарий
        comment_box = wait.until(EC.presence_of_element_located((By.ID, "comment-0")))
        driver.execute_script("arguments[0].value = arguments[1];", comment_box, COMMENT_TEXT)

        # Срок
        days_input = wait.until(EC.presence_of_element_located((By.ID, "days_to_deliver-0")))
        days_input.clear()
        days_input.send_keys(DAYS)

        # Стоимость
        amount_input = wait.until(EC.presence_of_element_located((By.ID, "amount-0")))
        amount_input.clear()
        amount_input.send_keys(COST)

        # Повторный клик
        driver.execute_script("arguments[0].click();", bid_btn)
        print("[SUCCESS] Ставка отправлена!")

        # Оставим окно открытым
        print("[INFO] Браузер остаётся открытым для проверки.")
        while True:
            time.sleep(10)

    except (TimeoutException, NoSuchElementException) as e:
        print(f"[ERROR] Ошибка при работе с проектом: {e}")
        print("[INFO] Оставляю браузер открытым для отладки.")
        while True:
            time.sleep(10)

def process_project(url):
    threading.Thread(target=make_bid, args=(url,), daemon=True).start()

@client.on(events.NewMessage)
async def handle_new_message(event):
    text = (event.raw_text or "").lower()
    if any(kw in text for kw in KEYWORDS):
        print(f"[INFO] Найдено сообщение по ключу: {text[:80]}")
        links = extract_links(text)
        for link in links:
            if "**" not in link:
                print(f"[INFO] Подходит ссылка: {link}")
                process_project(link)
                break

# ========== Запуск ==========
if __name__ == "__main__":
    print("[INFO] Бот запущен. Ожидаем проекты...")
    client.start()
    client.run_until_disconnected()
