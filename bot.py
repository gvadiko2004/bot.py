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

# ===== Настройки Telegram =====
api_id = 21882740
api_hash = "c80a68894509d01a93f5acfeabfdd922"
ALERT_BOT_TOKEN = "8338607025:AAH8hiO48IzQG5V8Dbv8cMofJlJ80femgYY"
ALERT_CHAT_ID = "YOUR_CHAT_ID"  # сюда вставь свой Telegram ID для уведомлений

# Клиент для уведомлений
alert_client = TelegramClient('alert_session', api_id, api_hash)

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

def load_cookies(driver, url):
    if os.path.exists(COOKIES_FILE):
        with open(COOKIES_FILE, "rb") as f:
            cookies = pickle.load(f)
        driver.get(url)
        for cookie in cookies:
            try:
                driver.add_cookie(cookie)
            except Exception:
                pass
        driver.refresh()
        print("[INFO] Cookies загружены.")
        return True
    return False

def login_if_needed(driver):
    if os.path.exists(COOKIES_FILE):
        print("[INFO] Cookies найдены, пропускаем авторизацию.")
        return

    print("[INFO] Нет сохранённых cookies, авторизация...")
    driver.get(LOGIN_URL)
    wait = WebDriverWait(driver, 30)

    wait.until(EC.presence_of_element_located((By.ID, "login-0")))
    driver.execute_script(f'document.getElementById("login-0").value="{LOGIN_DATA["login"]}";')
    driver.execute_script(f'document.getElementById("password-0").value="{LOGIN_DATA["password"]}";')
    print("[INFO] Логин и пароль введены.")

    js_click_login = """
    const loginBtn = document.querySelector('#save-0');
    if (loginBtn) { loginBtn.click(); }
    """
    driver.execute_script(js_click_login)
    time.sleep(5)
    save_cookies(driver)

# ---------------- Отправка уведомлений ----------------
async def send_alert(message: str):
    try:
        await alert_client.send_message(ALERT_CHAT_ID, message)
    except Exception as e:
        print(f"[ERROR] Не удалось отправить уведомление: {e}")

# ---------------- Функция ставок ----------------
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
        print(f"[INFO] Страница проекта загружена: {url}")

        wait_short = WebDriverWait(driver, 5)
        try:
            bid_btn = wait_short.until(EC.element_to_be_clickable((By.ID, "add-bid")))
            driver.execute_script("arguments[0].click();", bid_btn)
            print("[INFO] Нажата кнопка 'Сделать ставку'")
        except TimeoutException:
            try:
                alert_div = driver.find_element(By.CSS_SELECTOR, "div.alert.alert-info")
                print(f"[ALERT] {alert_div.text.strip()}")
                await send_alert(f"❌ Не удалось сделать ставку: {alert_div.text.strip()}\nСсылка: {url}")
                return
            except NoSuchElementException:
                print("[WARNING] Нет кнопки 'Сделать ставку'")
                await send_alert(f"⚠️ Не удалось найти кнопку 'Сделать ставку' для проекта: {url}")
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
        driver.execute_script("document.getElementById('comment-0').value = arguments[0];", COMMENT_TEXT)
        print(f"[INFO] Поля формы заполнены. Сумма: {price}")

        js_click_code = """
        const addButton = document.querySelector('#add-0');
        if (addButton) {
            const rect = addButton.getBoundingClientRect();
            const x = rect.left + rect.width/2;
            const y = rect.top + rect.height/2;
            const evt = new MouseEvent('click', {bubbles:true, clientX:x, clientY:y});
            addButton.dispatchEvent(evt);
        }
        """
        driver.execute_script(js_click_code)
        print("[SUCCESS] Заявка отправлена кнопкой 'Добавить' через JS")
        await send_alert(f"✅ Ставка успешно отправлена!\nСсылка: {url}\nСумма: {price}")

    except Exception as e:
        print(f"[ERROR] Ошибка при отправке заявки: {e}")
        await send_alert(f"❌ Ошибка при отправке ставки: {e}\nСсылка: {url}")

    print("[INFO] Браузер оставлен открытым для проверки.")

# ---------------- Телеграм ----------------
client = TelegramClient("session", api_id, api_hash)

@client.on(events.NewMessage)
async def handler(event):
    text = (event.message.text or "").lower()
    links = extract_links(text)

    if any(k in text for k in KEYWORDS) and links:
        print(f"[INFO] Подходит ссылка: {links[0]}")
        await make_bid(links[0])
        print("[INFO] Готов к следующему проекту")

# ---------------- Запуск ----------------
if __name__ == "__main__":
    print("[INFO] Бот запущен. Ожидаем новые проекты...")
    alert_client.start()
    client.start()
    client.run_until_disconnected()
