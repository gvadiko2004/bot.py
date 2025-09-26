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
ALERT_CHAT_ID = 1168962519  # твій Telegram ID

alert_bot = Bot(token=ALERT_BOT_TOKEN)

# ===== Настройки Freelancehunt =====
COMMENT_TEXT = """Доброго дня! Готовий виконати роботу якісно.
Портфоліо робіт у моєму профілі.
Заздалегідь дякую!
"""

PROFILE_PATH = "/home/user/chrome_profile"
COOKIES_FILE = "fh_cookies.pkl"
LOGIN_URL = "https://freelancehunt.com/profile/login"
LOGIN_DATA = {"login": "Vlari", "password": "Gvadiko_2004"}

# ---------------- Функції ----------------
def extract_links(text: str):
    """Витягує посилання на Freelancehunt з тексту"""
    return [link for link in re.findall(r"https?://[^\s]+", text)
            if link.startswith("https://freelancehunt.com/")]

def save_cookies(driver):
    with open(COOKIES_FILE, "wb") as f:
        pickle.dump(driver.get_cookies(), f)
    print("[INFO] Cookies збережені.")

def login_if_needed(driver):
    """Логін через браузер, якщо cookies немає"""
    if os.path.exists(COOKIES_FILE):
        print("[INFO] Cookies знайдено, авторизація пропущена.")
        return

    driver.get(LOGIN_URL)
    wait = WebDriverWait(driver, 30)
    wait.until(EC.presence_of_element_located((By.ID, "login-0")))
    driver.execute_script(f'document.getElementById("login-0").value="{LOGIN_DATA["login"]}";')
    driver.execute_script(f'document.getElementById("password-0").value="{LOGIN_DATA["password"]}";')
    driver.execute_script("const btn=document.querySelector('#save-0');if(btn){btn.click();}")
    time.sleep(5)
    save_cookies(driver)

# ---------------- Відправка повідомлень ----------------
async def send_alert(message: str):
    try:
        await alert_bot.send_message(chat_id=ALERT_CHAT_ID, text=message)
    except Exception as e:
        print(f"[ERROR] Не вдалося надіслати повідомлення: {e}")

# ---------------- Відправка ставки ----------------
async def make_bid(url):
    chrome_options = Options()
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument(f"--user-data-dir={PROFILE_PATH}")
    chrome_options.add_argument("--start-minimized")
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("--disable-gpu")

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    wait = WebDriverWait(driver, 30)

    try:
        login_if_needed(driver)
        driver.get(url)
        wait.until(lambda d: d.execute_script("return document.readyState") == "complete")
        print(f"[INFO] Сторінка проекту завантажена: {url}")

        wait_short = WebDriverWait(driver, 5)
        try:
            bid_btn = wait_short.until(EC.element_to_be_clickable((By.ID, "add-bid")))
            driver.execute_script("arguments[0].click();", bid_btn)
            print("[INFO] Натиснута кнопка 'Зробити ставку'")
        except TimeoutException:
            try:
                alert_div = driver.find_element(By.CSS_SELECTOR, "div.alert.alert-info")
                print(f"[ALERT] {alert_div.text.strip()}")
                await send_alert(f"❌ Не вдалося зробити ставку: {alert_div.text.strip()}\nПосилання: {url}")
                return
            except NoSuchElementException:
                print("[WARNING] Кнопку 'Зробити ставку' не знайдено")
                await send_alert(f"⚠️ Не знайдено кнопку 'Зробити ставку' для проекту: {url}")
                return

        time.sleep(1)
        try:
            price_span = wait.until(EC.presence_of_element_located((
                By.CSS_SELECTOR, "span.text-green.bold.pull-right.price.with-tooltip.hidden-xs"
            )))
            price = re.sub(r"[^\d]", "", price_span.text) or "1111"
        except Exception:
            price = "1111"

        driver.find_element(By.ID, "amount-0").send_keys(price)
        driver.find_element(By.ID, "days_to_deliver-0").send_keys("3")
        driver.execute_script(f"document.getElementById('comment-0').value = `{COMMENT_TEXT}`;")
        js_click_code = """
        const addButton = document.querySelector('#add-0');
        if (addButton) {
            const rect = addButton.getBoundingClientRect();
            const evt = new MouseEvent('click',{bubbles:true, clientX:rect.left+rect.width/2, clientY:rect.top+rect.height/2});
            addButton.dispatchEvent(evt);
        }
        """
        driver.execute_script(js_click_code)
        print("[SUCCESS] Ставка відправлена через JS")
        await send_alert(f"✅ Ставка успішно відправлена!\nПосилання: {url}\nСума: {price}")

    except Exception as e:
        print(f"[ERROR] Помилка при відправці ставки: {e}")
        await send_alert(f"❌ Помилка при відправці ставки: {e}\nПосилання: {url}")

    print("[INFO] Браузер залишений відкритим для перевірки.")

# ---------------- Telegram ----------------
client = TelegramClient("session", api_id, api_hash)

@client.on(events.NewMessage)
async def handler(event):
    text = (event.message.text or "").lower()
    links = extract_links(text)
    # Реагуємо на будь-який хештег і посилання на Freelancehunt
    if "#" in text and links:
        print(f"[INFO] Найдено посилання: {links[0]}")
        await make_bid(links[0])
        print("[INFO] Готовий до наступного проекту")

# ---------------- Запуск ----------------
async def main():
    print("[INFO] Запуск бота уведомлень через @iliarchie_bot...")
    await alert_bot.initialize()
    print("[INFO] Бот уведомлень запущений.")
    await client.start()
    print("[INFO] Telegram бот запущений. Очікуємо нові проекти...")
    await client.run_until_disconnected()

if __name__ == "__main__":
    asyncio.run(main())
