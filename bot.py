import os
import pickle
import re
import time
import sys
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
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

PROFILE_PATH = "/home/user/chrome_profile"
COOKIES_FILE = "fh_cookies.pkl"

# ---------------- Функции ----------------
def extract_links(text):
    return re.findall(r"https?://[^\s]+", text)

def save_cookies(driver):
    with open(COOKIES_FILE, "wb") as f:
        pickle.dump(driver.get_cookies(), f)

def load_cookies(driver, url):
    if os.path.exists(COOKIES_FILE):
        with open(COOKIES_FILE, "rb") as f:
            cookies = pickle.load(f)
        driver.get(url)
        for cookie in cookies:
            try:
                driver.add_cookie(cookie)
            except:
                continue
        driver.refresh()
        return True
    return False

def clear_browser_cache(driver):
    """Очистка кук и локального хранилища"""
    driver.delete_all_cookies()
    driver.execute_script("window.localStorage.clear();")
    driver.execute_script("window.sessionStorage.clear();")
    print("[INFO] Кэш и куки очищены")

def authorize_manual(driver, wait):
    print("[INFO] Если требуется авторизация, войдите вручную в браузере.")
    for _ in range(60):
        try:
            if driver.find_element(By.ID, "add-bid").is_displayed():
                print("[INFO] Авторизация завершена")
                save_cookies(driver)
                return True
        except:
            time.sleep(1)
    print("[WARN] Авторизация не выполнена, продолжаем")
    return False

def click_submit(driver, wait, max_attempts=5):
    """Надёжное нажатие на кнопку 'Добавить'"""
    for attempt in range(max_attempts):
        try:
            submit_btn = wait.until(EC.presence_of_element_located((By.ID, "btn-submit-0")))
            wait.until(EC.element_to_be_clickable((By.ID, "btn-submit-0")))

            driver.execute_script("""
                var evt = new MouseEvent('click', {bubbles:true,cancelable:true,view:window});
                arguments[0].dispatchEvent(evt);
            """, submit_btn)

            print(f"[SUCCESS] Ставка отправлена! (попытка {attempt+1})")
            return True
        except Exception as e:
            print(f"[WARN] Попытка {attempt+1} не удалась: {e}")
            time.sleep(1)
    print("[ERROR] Не удалось отправить ставку после нескольких попыток")
    return False

def make_bid(url):
    """Основная функция обработки проекта"""
    chrome_options = Options()
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument(f"--user-data-dir={PROFILE_PATH}")
    chrome_options.add_argument("--start-maximized")
    chrome_options.add_argument("--window-position=-10000,-10000")  # свернутое окно

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    wait = WebDriverWait(driver, 30)

    try:
        driver.get(url)
        wait.until(lambda d: d.execute_script("return document.readyState") == "complete")
        print(f"[INFO] Страница проекта загружена: {url}")

        load_cookies(driver, url)
        authorize_manual(driver, wait)

        bid_btn = wait.until(EC.element_to_be_clickable((By.ID, "add-bid")))
        driver.execute_script("arguments[0].click();", bid_btn)
        print("[INFO] Кнопка 'Сделать ставку' нажата")

        # Ввод суммы
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

        comment_area = wait.until(EC.presence_of_element_located((By.ID, "comment-0")))
        driver.execute_script("arguments[0].value = arguments[1];", comment_area, COMMENT_TEXT)
        print("[INFO] Комментарий вставлен")

        click_submit(driver, wait)

    except (TimeoutException, NoSuchElementException) as e:
        print(f"[ERROR] Не удалось сделать ставку: {e}")

    finally:
        clear_browser_cache(driver)
        driver.quit()
        print("[INFO] Браузер закрыт после завершения ставки.")

def process_project(url):
    """Обработка проекта и перезапуск скрипта"""
    make_bid(url)
    print("[INFO] Перезапуск скрипта для следующих проектов...")
    python = sys.executable
    os.execl(python, python, *sys.argv)

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

# ---------------- Запуск ----------------
if __name__ == "__main__":
    print("[INFO] Бот запущен. Ожидаем новые проекты...")
    client.start()
    client.run_until_disconnected()
