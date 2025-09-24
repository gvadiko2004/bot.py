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
from selenium.common.exceptions import TimeoutException, ElementClickInterceptedException
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

# ===== Настройки Freelancehunt =====
COOKIES_FILE = "fh_cookies.pkl"

COMMENT_TEXT = """Доброго дня!  

Ознайомився із завданням і готовий приступити до виконання.  

Стек: Figma / HTML (BEM), SCSS, JS / WordPress ACF PRO  

Приклади робіт доступні в портфоліо.  

Зв'яжіться зі мною в особистих повідомленнях. Дякую!
"""

# ---------------- Функции ----------------
def extract_links(text):
    return re.findall(r"https?://[^\s]+", text)

def save_cookies(driver):
    with open(COOKIES_FILE, "wb") as f:
        pickle.dump(driver.get_cookies(), f)

def load_cookies(driver):
    if os.path.exists(COOKIES_FILE):
        with open(COOKIES_FILE, "rb") as f:
            cookies = pickle.load(f)
        for cookie in cookies:
            driver.add_cookie(cookie)
        return True
    return False

def authorize_manual(driver):
    """Ждем ручную авторизацию пользователя"""
    print("[INFO] Если вы не авторизованы, войдите вручную в открывшемся браузере.")
    for _ in range(120):
        try:
            driver.find_element(By.ID, "add-bid")
            print("[INFO] Авторизация завершена")
            save_cookies(driver)
            return True
        except:
            time.sleep(1)
    print("[WARN] Авторизация не выполнена, продолжим без нее")
    return False

def insert_comment(driver, wait):
    """Вставка комментария через JS до полного совпадения"""
    comment_area = wait.until(EC.presence_of_element_located((By.ID, "comment-0")))
    while True:
        driver.execute_script("arguments[0].value = arguments[1];", comment_area, COMMENT_TEXT)
        entered_text = comment_area.get_attribute("value")
        if entered_text.strip() == COMMENT_TEXT.strip():
            print("[INFO] Текст комментария соответствует шаблону")
            break
        print("[WARN] Текст не совпадает, повторяем вставку...")
        time.sleep(0.5)

def make_bid(url):
    """Полный цикл обработки одной ссылки"""
    chrome_options = Options()
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    # Для возможности ручной авторизации
    # chrome_options.add_argument("--headless")

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    wait = WebDriverWait(driver, 30)

    try:
        driver.get(url)
        wait.until(lambda d: d.execute_script("return document.readyState") == "complete")
        print(f"[INFO] Страница {url} полностью загружена")

        # Подгружаем cookies, если есть
        if load_cookies(driver):
            driver.refresh()
            wait.until(lambda d: d.execute_script("return document.readyState") == "complete")
            print("[INFO] Cookies загружены и страница обновлена")

        authorize_manual(driver)

        # Кнопка "Сделать ставку"
        bid_btn = wait.until(EC.element_to_be_clickable((By.ID, "add-bid")))
        try:
            bid_btn.click()
        except ElementClickInterceptedException:
            driver.execute_script("arguments[0].click();", bid_btn)
        print("[INFO] Кнопка 'Сделать ставку' нажата")

        # Ввод цены
        try:
            price_span = wait.until(EC.presence_of_element_located((
                By.CSS_SELECTOR, "span.text-green.bold.pull-right.price.with-tooltip.hidden-xs"
            )))
            price = re.sub(r"[^\d]", "", price_span.text) or "1111"
        except Exception:
            price = "1111"

        amount_input = wait.until(EC.element_to_be_clickable((By.ID, "amount-0")))
        amount_input.clear()
        amount_input.send_keys(price)

        # Ввод дней
        days_input = wait.until(EC.element_to_be_clickable((By.ID, "days_to_deliver-0")))
        days_input.clear()
        days_input.send_keys("3")

        # Вставка комментария
        insert_comment(driver, wait)

        # Кнопка "Добавить" с ID btn-submit-0
        add_btn = wait.until(EC.element_to_be_clickable((By.ID, "btn-submit-0")))
        try:
            add_btn.click()
        except ElementClickInterceptedException:
            driver.execute_script("arguments[0].click();", add_btn)
        print("[INFO] Ставка отправлена успешно!")

    except Exception as e:
        print(f"[ERROR] Ошибка обработки ссылки {url}: {e}")
    finally:
        driver.quit()

# ---------------- Телеграм ----------------
client = TelegramClient("session", api_id, api_hash)

@client.on(events.NewMessage)
async def handler(event):
    text = (event.message.text or "").lower()
    if any(k in text for k in KEYWORDS):
        print(f"[INFO] Новый проект: {text[:100]}")
        links = extract_links(text)
        for link in links:
            print(f"[INFO] Открываем: {link}")
            # Новый поток на каждую ссылку, полностью чистый цикл
            threading.Thread(target=make_bid, args=(link,), daemon=True).start()

# ---------------- Запуск ----------------
if __name__ == "__main__":
    print("[INFO] Бот запущен, ждём сообщения...")
    client.start()
    client.run_until_disconnected()
