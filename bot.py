import os
import pickle
import re
import time
import asyncio
import tempfile

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

COOKIES_FILE = "fh_cookies.pkl"
LOGIN_URL = "https://freelancehunt.com/profile/login"
LOGIN_DATA = {"login": "Vlari", "password": "Gvadiko_2004"}

# ---------------- Функции ----------------
def extract_links(text: str):
    """Извлекаем все ссылки Freelancehunt из текста"""
    return [link for link in re.findall(r"https?://[^\s]+", text)
            if "freelancehunt.com" in link]

async def send_alert(message: str):
    """Отправка уведомления в Telegram"""
    try:
        await alert_bot.send_message(chat_id=ALERT_CHAT_ID, text=message)
    except Exception as e:
        print(f"[ERROR] Не удалось отправить уведомление: {e}")

async def make_bid(url):
    """Функция для автоматического выполнения ставки на проект"""
    tmp_profile = tempfile.mkdtemp()
    chrome_options = Options()
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument(f"--user-data-dir={tmp_profile}")

    try:
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
        wait = WebDriverWait(driver, 30)

        # Логин, если cookies нет
        if not os.path.exists(COOKIES_FILE):
            driver.get(LOGIN_URL)
            wait.until(EC.presence_of_element_located((By.ID, "login-0")))
            driver.execute_script(f'document.getElementById("login-0").value="{LOGIN_DATA["login"]}";')
            driver.execute_script(f'document.getElementById("password-0").value="{LOGIN_DATA["password"]}";')
            driver.execute_script("const btn=document.querySelector('#save-0'); if(btn){btn.click();}")
            time.sleep(5)
            with open(COOKIES_FILE, "wb") as f:
                pickle.dump(driver.get_cookies(), f)
            print("[INFO] Cookies сохранены.")

        driver.get(url)
        wait.until(lambda d: d.execute_script("return document.readyState") == "complete")
        print(f"[INFO] Страница проекта загружена: {url}")

        try:
            bid_btn = WebDriverWait(driver, 5).until(EC.element_to_be_clickable((By.ID, "add-bid")))
            driver.execute_script("arguments[0].click();", bid_btn)
            print("[INFO] Нажата кнопка 'Сделать ставку'")
        except TimeoutException:
            try:
                alert_div = driver.find_element(By.CSS_SELECTOR, "div.alert.alert-info")
                await send_alert(f"❌ Не удалось сделать ставку: {alert_div.text.strip()}\nСсылка: {url}")
                return
            except NoSuchElementException:
                await send_alert(f"⚠️ Нет кнопки 'Сделать ставку' для проекта: {url}")
                return

        # Заполняем форму
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
        driver.execute_script("""
        const addButton = document.querySelector('#add-0');
        if (addButton) {
            const rect = addButton.getBoundingClientRect();
            const evt = new MouseEvent('click',{bubbles:true, clientX:rect.left+rect.width/2, clientY:rect.top+rect.height/2});
            addButton.dispatchEvent(evt);
        }
        """)
        print("[SUCCESS] Ставка отправлена через JS")
        await send_alert(f"✅ Ставка успешно отправлена!\nСсылка: {url}\nСумма: {price}")

    except Exception as e:
        print(f"[ERROR] Ошибка при отправке заявки: {e}")
        await send_alert(f"❌ Ошибка при отправке ставки: {e}\nСсылка: {url}")
    finally:
        driver.quit()

# ---------------- Телеграм ----------------
client = TelegramClient("session", api_id, api_hash)

@client.on(events.NewMessage)
async def handler(event):
    text = (event.message.text or "").lower()
    links = extract_links(text)
    if any(k in text for k in KEYWORDS) and links:
        for link in links:
            print(f"[INFO] Подходит ссылка: {link}")
            await make_bid(link)
            print("[INFO] Готов к следующему проекту")

# ---------------- Запуск ----------------
async def main():
    print("[INFO] Запуск бота уведомлений через Telegram Bot...")
    await alert_bot.initialize()
    print("[INFO] Бот уведомлений запущен.")
    await client.start()
    print("[INFO] Telegram бот запущен. Ожидаем новые проекты...")
    await client.run_until_disconnected()

if __name__ == "__main__":
    asyncio.run(main())
