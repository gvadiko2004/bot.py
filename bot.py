import os
import re
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from telethon import TelegramClient, events

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

def extract_links(text):
    return re.findall(r"https?://[^\s]+", text)

def make_bid(url):
    options = Options()
    options.add_argument(f"--user-data-dir={PROFILE_PATH}")
    options.add_argument("--start-maximized")
    options.add_argument("--disable-extensions")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    wait = WebDriverWait(driver, 30)

    try:
        driver.get(url)
        wait.until(lambda d: d.execute_script("return document.readyState") == "complete")
        print(f"[INFO] Страница проекта загружена: {url}")

        # 1. Нажимаем кнопку "Сделать ставку"
        bid_btn = wait.until(EC.element_to_be_clickable((By.ID, "add-bid")))
        bid_btn.click()
        print("[INFO] Нажата кнопка 'Сделать ставку'")

        # 2. Ждём появления формы
        wait.until(EC.element_to_be_clickable((By.ID, "amount-0")))
        print("[INFO] Форма ставки активна")

        # 3. Заполняем поля
        try:
            price_span = driver.find_element(By.CSS_SELECTOR, "span.text-green.bold.pull-right.price.with-tooltip.hidden-xs")
            price = re.sub(r"[^\d]", "", price_span.text) or "1111"
        except:
            price = "1111"

        driver.find_element(By.ID, "amount-0").send_keys(price)
        driver.find_element(By.ID, "days_to_deliver-0").send_keys("3")
        driver.execute_script("document.getElementById('comment-0').value = arguments[0];", COMMENT_TEXT)
        print("[INFO] Поля формы заполнены")

        # 4. TAB 6 раз + ENTER
        actions = webdriver.ActionChains(driver)
        for i in range(6):
            actions.send_keys(Keys.TAB)
            print(f"[INFO] TAB {i+1}")
            time.sleep(0.2)
        actions.send_keys(Keys.ENTER)
        actions.perform()
        print("[SUCCESS] ENTER для отправки заявки выполнен!")

        print("[INFO] Браузер оставлен открытым для проверки.")

    except Exception as e:
        print(f"[ERROR] Не удалось сделать ставку: {e}")

    return driver

def process_project(url):
    make_bid(url)
    print("[INFO] Готов к следующему проекту")

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
            process_project(links[0])

if __name__ == "__main__":
    print("[INFO] Бот запущен. Ожидаем новые проекты...")
    client.start()
    client.run_until_disconnected()
