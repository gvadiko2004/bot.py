import os
import pickle
import re
import threading
import time
import random
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from telethon import TelegramClient, events

api_id = 21882740
api_hash = "c80a68894509d01a93f5acfeabfdd922"

KEYWORDS = ["#html_и_css_верстка","#веб_программирование","#cms",
"#интернет_магазины_и_электронная_коммерция","#создание_сайта_под_ключ","#дизайн_сайтов"]
KEYWORDS = [k.lower() for k in KEYWORDS]

COMMENT_TEXT = """Доброго дня! Готовий виконати роботу якісно.
Портфоліо робіт у моєму профілі.
Заздалегідь дякую!
"""

PROFILE_PATH = "/home/user/chrome_profile"
EXTENSION_PATH = "/path/to/anticaptcha_extension"

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
            try: driver.add_cookie(cookie)
            except: continue
        return True
    return False

def authorize_manual(driver):
    print("[INFO] Если нужна авторизация, войдите вручную.")
    for _ in range(120):
        try:
            driver.find_element(By.ID, "add-bid")
            print("[INFO] Авторизация завершена")
            save_cookies(driver)
            return True
        except:
            time.sleep(1)
    print("[WARN] Авторизация не выполнена")
    return False

def insert_comment(wait):
    comment_area = wait.until(EC.presence_of_element_located((By.ID, "comment-0")))
    comment_area.clear()
    for ch in COMMENT_TEXT:
        comment_area.send_keys(ch)
        time.sleep(0.05 + random.random()*0.05)
    print("[INFO] Комментарий введен")

def click_js(driver, element):
    driver.execute_script("arguments[0].click();", element)

def safe_click(wait, driver, selector_id):
    """Клик с повтором, если элемент не срабатывает сразу"""
    for _ in range(5):
        try:
            el = wait.until(EC.element_to_be_clickable((By.ID, selector_id)))
            click_js(driver, el)
            return True
        except:
            time.sleep(0.5)
    return False

def make_bid(url):
    chrome_options = Options()
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument(f"--user-data-dir={PROFILE_PATH}")
    chrome_options.add_argument(f"--load-extension={EXTENSION_PATH}")

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    wait = WebDriverWait(driver, 30)
    
    try:
        driver.get(url)
        wait.until(lambda d: d.execute_script("return document.readyState") == "complete")
        print(f"[INFO] Страница загружена: {url}")
        load_cookies(driver, url)
        time.sleep(1)
        driver.refresh()
        wait.until(lambda d: d.execute_script("return document.readyState") == "complete")
        print("[INFO] Страница обновлена и кеш очищен")

        authorize_manual(driver)

        # Первый клик "Сделать ставку"
        safe_click(wait, driver, "add-bid")
        print("[INFO] Кнопка 'Сделать ставку' нажата")

        # Ввод суммы и дней
        try:
            price_span = wait.until(EC.presence_of_element_located(
                (By.CSS_SELECTOR,"span.text-green.bold.pull-right.price.with-tooltip.hidden-xs")))
            price = re.sub(r"[^\d]", "", price_span.text) or "1111"
        except:
            price = "1111"

        amount_input = wait.until(EC.element_to_be_clickable((By.ID, "amount-0")))
        amount_input.clear()
        amount_input.send_keys(price)

        days_input = wait.until(EC.element_to_be_clickable((By.ID, "days_to_deliver-0")))
        days_input.clear()
        days_input.send_keys("3")

        insert_comment(wait)

        # Последний клик по кнопке "Добавить"
        safe_click(wait, driver, "add-0")
        print("[INFO] Ставка отправлена!")

    except TimeoutException as e:
        print(f"[ERROR] Ошибка при обработке проекта: {e}")
    finally:
        driver.quit()

def process_project(url):
    threading.Thread(target=make_bid, args=(url,), daemon=True).start()

client = TelegramClient("session", api_id, api_hash)

@client.on(events.NewMessage)
async def handler(event):
    text = (event.message.text or "").lower()
    if any(k in text for k in KEYWORDS):
        print(f"[INFO] Новый проект: {text[:100]}")
        links = extract_links(text)
        if links:
            process_project(links[0])

if __name__ == "__main__":
    print("[INFO] Бот запущен. Ожидаем новые проекты...")
    client.start()
    client.run_until_disconnected()
