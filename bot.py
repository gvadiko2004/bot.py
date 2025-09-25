import os
import pickle
import re
import sys
import time

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver import ActionChains
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

# ---------------- Вспомогательные функции ----------------
def extract_links(text: str):
    return re.findall(r"https?://[^\s]+", text)

def clear_browser_cache(driver):
    try:
        driver.delete_all_cookies()
    except:
        pass

def save_cookies(driver):
    try:
        with open(COOKIES_FILE, "wb") as f:
            pickle.dump(driver.get_cookies(), f)
    except:
        pass

def load_cookies(driver, url):
    if os.path.exists(COOKIES_FILE):
        try:
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
        except:
            return False
    return False

def authorize_manual(driver, wait):
    print("[INFO] Якщо потрібно — авторизуйтесь вручну у браузері.")
    for _ in range(60):
        try:
            if driver.find_element(By.ID, "add-bid").is_displayed():
                print("[INFO] Авторизація завершена")
                save_cookies(driver)
                return True
        except:
            time.sleep(1)
    print("[WARN] Авторизація не виконана")
    return False

def send_tab_and_enter(driver):
    try:
        actions = ActionChains(driver)
        for _ in range(6):
            actions.send_keys(Keys.TAB)
        actions.send_keys(Keys.ENTER)
        actions.perform()
        print("[INFO] TAB x6 + ENTER виконано")
    except Exception as e:
        print(f"[ERROR] TAB+ENTER не спрацював: {e}")

# ---------------- Основна логіка ----------------
def make_bid(url):
    chrome_options = Options()
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument(f"--user-data-dir={PROFILE_PATH}")
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--start-maximized")

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    wait = WebDriverWait(driver, 30)

    try:
        driver.get(url)
        wait.until(lambda d: d.execute_script("return document.readyState") == "complete")
        print(f"[INFO] Сторінка проекту завантажена: {url}")

        clear_browser_cache(driver)
        load_cookies(driver, url)
        authorize_manual(driver, wait)

        bid_btn = wait.until(EC.element_to_be_clickable((By.ID, "add-bid")))
        driver.execute_script("arguments[0].click();", bid_btn)
        print("[INFO] Кнопка 'Зробити ставку' натиснута")

        # Сума
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

        # Дні
        days_input = wait.until(EC.element_to_be_clickable((By.ID, "days_to_deliver-0")))
        days_input.clear()
        days_input.send_keys("3")

        # Коментар
        comment_area = wait.until(EC.presence_of_element_located((By.ID, "comment-0")))
        driver.execute_script("arguments[0].value = arguments[1];", comment_area, COMMENT_TEXT)
        print("[INFO] Коментар вставлений")

        # Імітація TAB x6 + ENTER
        send_tab_and_enter(driver)

        print("[SUCCESS] Ставка відправлена!")

    except (TimeoutException, NoSuchElementException) as e:
        print(f"[ERROR] Не вдалося зробити ставку: {e}")

    finally:
        driver.quit()
        print("[INFO] Браузер закрито після завершення ставки.")

def process_project(url):
    make_bid(url)
    print("[INFO] Перезапуск скрипта для наступного проекту...")
    python = sys.executable
    os.execl(python, python, *sys.argv)

# ---------------- Телеграм ----------------
client = TelegramClient("session", api_id, api_hash)

@client.on(events.NewMessage)
async def handler(event):
    text = (event.message.text or "").lower()
    if any(k in text for k in KEYWORDS):
        print(f"[INFO] Знайдено повідомлення по ключу: {text[:100]}")
        links = extract_links(text)
        if links:
            print(f"[INFO] Підходить посилання: {links[0]}")
            process_project(links[0])

# ---------------- Запуск ----------------
if __name__ == "__main__":
    print("[INFO] Бот запущений. Очікуємо нові проекти...")
    client.start()
    client.run_until_disconnected()
