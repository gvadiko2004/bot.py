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
EMAIL = "Vlari"
PASSWORD = "Gvadiko_2004"
COOKIES_FILE = "fh_cookies.pkl"

COMMENT_TEXT = """Доброго дня! 

Я ознайомився із завданням і готовий приступити до якісного виконання завдання

Стек: Figma / html (bem), scss, js / WordPress ACF PRO

Мої роботи:
https://telya.ch/
https://gvadiko2004.github.io/grill/
https://gvadiko2004.github.io/Anon-shop/
https://iliarchie.github.io/cates/

Зв'яжіться зі мною в особистих повідомленнях.
Заздалегідь дякую"""

# ---------------- Функции ----------------
def type_slow(element, text, delay=0.02):
    for ch in text:
        element.send_keys(ch)
        time.sleep(delay)

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

def authorize(driver, wait):
    """Авторизация на Freelancehunt"""
    try:
        email_input = wait.until(EC.presence_of_element_located((By.ID, "login-0")))
        password_input = wait.until(EC.presence_of_element_located((By.ID, "password-0")))
        submit_btn = wait.until(EC.element_to_be_clickable((By.ID, "save-0")))

        print("[INFO] Авторизация: вводим email и пароль...")
        email_input.clear()
        type_slow(email_input, EMAIL)
        password_input.clear()
        type_slow(password_input, PASSWORD)

        submit_btn.click()
        time.sleep(5)
        save_cookies(driver)
        print("[INFO] Авторизация успешна!")
    except TimeoutException:
        print("[INFO] Авторизация не требуется (уже залогинены)")

def click_register_if_present(driver, wait):
    """Нажать на 'Зарегистрироваться и выполнить проект', если есть"""
    try:
        reg_btn = driver.find_element(By.XPATH, '//a[contains(@href,"/ua/register/freelancer")]')
        reg_btn.click()
        print("[INFO] Нажата кнопка регистрации")
        time.sleep(3)

        login_link = driver.find_element(By.XPATH, '//a[contains(@href,"/ua/profile/login")]')
        login_link.click()
        print("[INFO] Переход на страницу входа")
        time.sleep(3)
    except Exception:
        print("[INFO] Кнопка регистрации не найдена — пропускаем")

def make_bid(driver, wait):
    """Делаем ставку"""
    try:
        # Найти кнопку 'Сделать ставку'
        try:
            bid_btn = wait.until(EC.element_to_be_clickable((By.ID, "add-bid")))
        except TimeoutException:
            bid_btn = wait.until(EC.element_to_be_clickable(
                (By.XPATH, '//a[contains(text(),"Сделать ставку")]')
            ))

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
        type_slow(amount_input, price)

        # Ввод дней
        days_input = wait.until(EC.element_to_be_clickable((By.ID, "days_to_deliver-0")))
        days_input.clear()
        type_slow(days_input, "3")

        # Комментарий
        comment_area = wait.until(EC.element_to_be_clickable((By.ID, "comment-0")))
        type_slow(comment_area, COMMENT_TEXT)

        # Кнопка 'Добавить'
        add_btn = wait.until(EC.element_to_be_clickable(
            (By.XPATH, '//button[contains(text(),"Добавить")]')
        ))
        add_btn.click()
        print("[INFO] Ставка отправлена!")
        time.sleep(2)
    except Exception as e:
        print(f"[ERROR] Ошибка при сделке ставки: {e}")

def open_link_and_process(url):
    chrome_options = Options()
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    # chrome_options.add_argument("--headless")  # для отладки VPS можно закомментировать

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    wait = WebDriverWait(driver, 20)

    try:
        driver.get(url)
        time.sleep(5)

        # Загружаем cookies
        if load_cookies(driver):
            driver.refresh()
            time.sleep(3)

        click_register_if_present(driver, wait)
        authorize(driver, wait)
        make_bid(driver, wait)

    except Exception as e:
        print(f"[ERROR] Ошибка обработки ссылки: {e}")
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
            print(f"[INFO] Открываем: {links[0]}")
            threading.Thread(target=open_link_and_process, args=(links[0],), daemon=True).start()

# ---------------- Запуск ----------------
if __name__ == "__main__":
    print("[INFO] Бот запущен, ждём сообщения...")
    client.start()
    client.run_until_disconnected()
