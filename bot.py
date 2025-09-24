from telethon import TelegramClient, events
import threading
import re
import time

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, ElementClickInterceptedException
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

# ==== Настройки Telegram ====
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

# ==== Данные авторизации Freelancehunt ====
EMAIL = "Vlari"
PASSWORD = "Gvadiko_2004"

# ---------------- Функции ----------------
def type_text_slowly(element, text, delay=0.02):
    for ch in text:
        element.send_keys(ch)
        time.sleep(delay)

def extract_links(text):
    cleaned_text = text.replace("**", "")
    return re.findall(r"https?://[^\s]+", cleaned_text)

def login_if_needed(driver, wait):
    """Авторизация если пользователь не залогинен"""
    try:
        register_btn = wait.until(EC.element_to_be_clickable(
            (By.XPATH, '//a[contains(text(),"Зареєструватися та виконати проєкт")]')
        ))
        register_btn.click()
        print("➡️ Перенаправление на страницу входа...")

        login_input = wait.until(EC.element_to_be_clickable((By.ID, "login-0")))
        login_input.clear()
        type_text_slowly(login_input, EMAIL)

        pass_input = wait.until(EC.element_to_be_clickable((By.ID, "password-0")))
        pass_input.clear()
        type_text_slowly(pass_input, PASSWORD)

        pass_input.submit()
        print("✅ Авторизация выполнена!")
        time.sleep(3)

    except TimeoutException:
        print("🔑 Пользователь уже авторизован или кнопка не найдена.")

def make_bid(driver, wait):
    """Основная логика: сделать ставку"""
    try:
        # Кнопка "Сделать ставку"
        try:
            button = wait.until(EC.element_to_be_clickable((By.ID, "add-bid")))
        except TimeoutException:
            button = wait.until(EC.element_to_be_clickable(
                (By.XPATH, '//a[contains(text(),"Сделать ставку")]')
            ))

        try:
            button.click()
        except ElementClickInterceptedException:
            driver.execute_script("arguments[0].click();", button)

        print("✅ Кнопка 'Сделать ставку' нажата!")

        # Ввод цены
        try:
            price_span = wait.until(EC.presence_of_element_located((
                By.CSS_SELECTOR,
                "span.text-green.bold.pull-right.price.with-tooltip.hidden-xs"
            )))
            raw_price = price_span.text
            price_digits = re.sub(r"[^\d]", "", raw_price) or "1111"
        except Exception:
            price_digits = "1111"

        amount_input = wait.until(EC.element_to_be_clickable((By.ID, "amount-0")))
        amount_input.clear()
        type_text_slowly(amount_input, price_digits)

        # Ввод дней
        days_input = wait.until(EC.element_to_be_clickable((By.ID, "days_to_deliver-0")))
        days_input.clear()
        type_text_slowly(days_input, "3")

        # Ввод комментария
        textarea = wait.until(EC.element_to_be_clickable((By.ID, "comment-0")))
        type_text_slowly(textarea, COMMENT_TEXT)

        # Кнопка "Добавить"
        submit_btn = wait.until(EC.element_to_be_clickable(
            (By.XPATH, '//button[contains(text(),"Добавить")]')
        ))
        submit_btn.click()
        print("✅ Ставка отправлена!")

    except Exception as e:
        print(f"❌ Ошибка при сделке ставки: {e}")

def open_link_and_click(url):
    """Открываем ссылку и выполняем логику ставки"""
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Без GUI
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    wait = WebDriverWait(driver, 20)

    try:
        driver.get(url)
        print(f"🌐 Открыта страница: {url}")

        login_if_needed(driver, wait)
        make_bid(driver, wait)

    except Exception as e:
        print(f"❌ Ошибка в open_link_and_click: {e}")
    finally:
        driver.quit()

# ---------------- Телеграм ----------------
client = TelegramClient("session", api_id, api_hash)

@client.on(events.NewMessage)
async def handler(event):
    message_text = (event.message.text or "").lower()
    if any(keyword in message_text for keyword in KEYWORDS):
        print(f"🔔 Нашёл проект: {message_text[:100]}")
        links = extract_links(message_text)
        if links:
            print(f"🌐 Открываю и кликаю по ссылке: {links[0]}")
            threading.Thread(target=open_link_and_click, args=(links[0],), daemon=True).start()

# ---------------- Запуск ----------------
if __name__ == "__main__":
    print("✅ Бот запущен, ждёт сообщения...")
    client.start()
    client.run_until_disconnected()
