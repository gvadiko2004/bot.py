import os
import pickle
import re
import threading
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
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

PROFILE_PATH = "/home/user/chrome_profile"  # Путь к постоянному профилю Chrome

# ---------------- Функции ----------------
def extract_links(text):
    return re.findall(r"https?://[^\s]+", text)

def save_cookies(driver):
    with open("fh_cookies.pkl", "wb") as f:
        pickle.dump(driver.get_cookies(), f)

def load_cookies(driver, url):
    if os.path.exists("fh_cookies.pkl"):
        with open("fh_cookies.pkl", "rb") as f:
            cookies = pickle.load(f)
        driver.get(url)
        for cookie in cookies:
            try:
                driver.add_cookie(cookie)
            except:
                continue
        return True
    return False

def authorize_manual(driver):
    print("[INFO] Если требуется авторизация, войдите вручную в открывшемся браузере.")
    for _ in range(60):
        try:
            driver.find_element(By.ID, "add-bid")
            print("[INFO] Авторизация завершена")
            save_cookies(driver)
            return True
        except:
            time.sleep(1)
    print("[WARN] Авторизация не выполнена, продолжаем")
    return False

def insert_comment(driver, wait):
    """Вставка комментария через JS (копипастом)"""
    comment_area = wait.until(EC.presence_of_element_located((By.ID, "comment-0")))
    driver.execute_script("arguments[0].value = arguments[1];", comment_area, COMMENT_TEXT)
    print("[INFO] Текст комментария вставлен через JS")

def click_js(driver, element):
    """Надёжный клик через JS"""
    driver.execute_script("arguments[0].click();", element)

def make_bid(url):
    chrome_options = Options()
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument(f"--user-data-dir={PROFILE_PATH}")

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    wait = WebDriverWait(driver, 30)

    try:
        driver.get(url)
        wait.until(lambda d: d.execute_script("return document.readyState") == "complete")
        print(f"[INFO] Страница проекта загружена: {url}")

        if load_cookies(driver, url):
            driver.refresh()
            wait.until(lambda d: d.execute_script("return document.readyState") == "complete")
            print("[INFO] Cookies загружены и страница обновлена")

        authorize_manual(driver)

        # Первый клик "Сделать ставку" чтобы открыть форму
        bid_btn = wait.until(EC.element_to_be_clickable((By.ID, "add-bid")))
        click_js(driver, bid_btn)
        print("[INFO] Первый клик 'Сделать ставку' выполнен")

        # Ввод суммы и дней
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

        days_input = wait.until(EC.element_to_be_clickable((By.ID, "days_to_deliver-0")))
        days_input.clear()
        days_input.send_keys("3")

        # Вставка комментария через JS
        insert_comment(driver, wait)

        # Второй клик "Сделать ставку" чтобы подтвердить
        click_js(driver, bid_btn)
        print("[INFO] Второй клик 'Сделать ставку' выполнен. Ставка отправлена!")

    except TimeoutException as e:
        print(f"[ERROR] Ошибка при обработке проекта: {e}")
    finally:
        driver.quit()

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
    print("[INFO] Бот запущен. Ожидаем новые проекты...")
    client.start()
    client.run_until_disconnected()
