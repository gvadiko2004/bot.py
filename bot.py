import os
import pickle
import re
import time
import asyncio

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

from webdriver_manager.chrome import ChromeDriverManager
from telethon import TelegramClient, events
from telegram import Bot

# ===== Настройки Telegram =====
api_id = 21882740
api_hash = "c80a68894509d01a93f5acfeabfdd922"
ALERT_BOT_TOKEN = "6566504110:AAFK9hA4jxZ0eA7KZGhVvPe8mL2HZj2tQmE"
ALERT_CHAT_ID = 1168962519

alert_bot = Bot(token=ALERT_BOT_TOKEN)

# ===== Ключевые слова и текст заявки =====
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
LOGIN_URL = "https://freelancehunt.com/profile/login"
LOGIN_DATA = {"login": "Vlari", "password": "Gvadiko_2004"}

# ---------------- Функции ----------------
def extract_links(text: str):
    return [link for link in re.findall(r"https?://[^\s]+", text)
            if link.startswith("https://freelancehunt.com/")]

def save_cookies(driver):
    with open(COOKIES_FILE, "wb") as f:
        pickle.dump(driver.get_cookies(), f)
    print("[INFO] Cookies сохранены.")

def login_if_needed(driver):
    if os.path.exists(COOKIES_FILE):
        print("[INFO] Cookies найдены, пропускаем авторизацию.")
        driver.get("https://freelancehunt.com/")
        for cookie in pickle.load(open(COOKIES_FILE, "rb")):
            driver.add_cookie(cookie)
        return

    driver.get(LOGIN_URL)
    wait = WebDriverWait(driver, 30)
    wait.until(EC.presence_of_element_located((By.ID, "login-0")))
    driver.execute_script(f'document.getElementById("login-0").value="{LOGIN_DATA["login"]}";')
    driver.execute_script(f'document.getElementById("password-0").value="{LOGIN_DATA["password"]}";')
    driver.execute_script("document.querySelector('#save-0').click();")
    time.sleep(5)
    save_cookies(driver)

# ---------------- Отправка уведомлений ----------------
async def send_alert(message: str):
    try:
        await alert_bot.send_message(chat_id=ALERT_CHAT_ID, text=message)
    except Exception as e:
        print(f"[ERROR] Не удалось отправить уведомление: {e}")

# ---------------- Функция ставок ----------------
async def make_bid(url):
    chrome_options = Options()
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument(f"--user-data-dir={PROFILE_PATH}")
    chrome_options.add_argument("--headless")  # можно убрать для визуализации
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    wait = WebDriverWait(driver, 30)

    try:
        login_if_needed(driver)
        driver.get(url)
        wait.until(lambda d: d.execute_script("return document.readyState") == "complete")
        print(f"[INFO] Страница проекта загружена: {url}")

        try:
            bid_btn = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.ID, "add-bid"))
            )
            driver.execute_script("arguments[0].click();", bid_btn)
            print("[INFO] Нажата кнопка 'Сделать ставку'")
        except TimeoutException:
            await send_alert(f"⚠️ Нет кнопки 'Сделать ставку' для проекта: {url}")
            return

        # Заполнение формы
        try:
            price = "1111"  # можно динамически брать из проекта
            driver.find_element(By.ID, "amount-0").send_keys(price)
            driver.find_element(By.ID, "days_to_deliver-0").send_keys("3")
            driver.execute_script(f"document.getElementById('comment-0').value=`{COMMENT_TEXT}`;")
            driver.execute_script("document.querySelector('#add-0').click();")
            print("[SUCCESS] Ставка отправлена")
            await send_alert(f"✅ Ставка успешно отправлена!\nСсылка: {url}\nСумма: {price}")
        except Exception as e:
            await send_alert(f"❌ Ошибка при заполнении формы: {e}\nСсылка: {url}")

    except Exception as e:
        await send_alert(f"❌ Ошибка при открытии проекта: {e}\nСсылка: {url}")
    finally:
        driver.quit()

# ---------------- Telegram Client ----------------
client = TelegramClient("session", api_id, api_hash)

@client.on(events.NewMessage)
async def handler(event):
    text = (event.message.message or "").lower()
    links = extract_links(text)
    if any(k in text for k in KEYWORDS) and links:
        print(f"[INFO] Найден проект: {links[0]}")
        await make_bid(links[0])

# ---------------- Запуск ----------------
async def main():
    await client.start()
    print("[INFO] Telegram бот запущен. Ожидаем новые проекты...")
    await client.run_until_disconnected()

if __name__ == "__main__":
    asyncio.run(main())
