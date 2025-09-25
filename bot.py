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
COMMENT_TEXT = """Доброго дня! Ознайомився із завданням і готовий приступити до виконання.
Стек: Figma / HTML (BEM), SCSS, JS / WordPress ACF PRO
Приклади робіт доступні в портфоліо. Дякую!"""

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
            try:
                driver.add_cookie(cookie)
            except:
                continue
        return True
    return False

def authorize_manual(driver):
    print("[INFO] Если требуется авторизация, войдите вручную в открывшемся браузере.")
    for _ in range(120):
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
    """Вставка комментария через JS и проверка полного совпадения"""
    comment_area = wait.until(EC.presence_of_element_located((By.ID, "comment-0")))
    while True:
        driver.execute_script("arguments[0].value = arguments[1];", comment_area, COMMENT_TEXT)
        entered_text = comment_area.get_attribute("value")
        if entered_text.strip() == COMMENT_TEXT.strip():
            print("[INFO] Текст комментария введён корректно")
            break
        time.sleep(0.2)

def click_js(driver, element):
    """Кликаем через JS для обхода конфликтов DOM"""
    try:
        driver.execute_script("arguments[0].click();", element)
        return True
    except:
        return False

def make_bid(driver, wait):
    try:
        # Перезагрузка страницы и очистка кэша перед вводом данных
        driver.execute_script("window.localStorage.clear(); window.sessionStorage.clear();")
        driver.refresh()
        wait.until(lambda d: d.execute_script("return document.readyState") == "complete")
        print("[INFO] Страница перезагружена и кэш очищен")

        authorize_manual(driver)

        # Нажатие "Сделать ставку"
        bid_btn = wait.until(EC.element_to_be_clickable((By.ID, "add-bid")))
        click_js(driver, bid_btn)
        print("[INFO] Кнопка 'Сделать ставку' нажата")

        # Ввод цены
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

        # Ввод дней
        days_input = wait.until(EC.element_to_be_clickable((By.ID, "days_to_deliver-0")))
        days_input.clear()
        days_input.send_keys("3")

        # Вставка комментария
        insert_comment(driver, wait)

        # Клик по кнопке "Добавить"
        add_btn = wait.until(EC.element_to_be_clickable((By.ID, "add-0")))
        click_js(driver, add_btn)
        print("[INFO] Заявка успешно отправлена!")

    except Exception as e:
        print(f"[ERROR] Ошибка при обработке проекта: {e}")

def open_link_and_process(url):
    chrome_options = Options()
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    # Постоянный профиль Chrome для сохранения авторизации
    profile_path = "/home/user/chrome_profile"  # <-- поменяйте под себя
    chrome_options.add_argument(f"--user-data-dir={profile_path}")

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    wait = WebDriverWait(driver, 30)
    try:
        driver.get(url)
        wait.until(lambda d: d.execute_script("return document.readyState") == "complete")
        print(f"[INFO] Страница проекта загружена: {url}")

        if load_cookies(driver):
            driver.refresh()
            wait.until(lambda d: d.execute_script("return document.readyState") == "complete")
            print("[INFO] Cookies загружены и страница обновлена")

        make_bid(driver, wait)
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
        if links:
            threading.Thread(target=open_link_and_process, args=(links[0],), daemon=True).start()

# ---------------- Запуск ----------------
if __name__ == "__main__":
    print("[INFO] Бот запущен, ждём сообщения...")
    client.start()
    client.run_until_disconnected()
