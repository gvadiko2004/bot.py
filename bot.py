import re
import threading
import time

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import ElementClickInterceptedException, TimeoutException
from webdriver_manager.chrome import ChromeDriverManager

from telethon import TelegramClient, events

# ===== Telegram =====
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

# ===== Комментарий =====
COMMENT_TEXT = """Доброго дня!  

Ознайомився із завданням і готовий приступити до виконання.  

Стек: Figma / HTML (BEM), SCSS, JS / WordPress ACF PRO  

Приклади робіт доступні в портфоліо.  

Зв'яжіться зі мною в особистих повідомленнях. Дякую!
"""

# ---------------- Функции ----------------
def extract_links(text):
    return re.findall(r"https?://[^\s]+", text)

def click_element_safe(driver, element, retries=3, delay=0.5):
    for _ in range(retries):
        try:
            element.click()
            return True
        except ElementClickInterceptedException:
            driver.execute_script("arguments[0].click();", element)
            return True
        except:
            time.sleep(delay)
    return False

def process_project(url):
    chrome_options = Options()
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    # chrome_options.add_argument("--headless") # можно включить, если GUI не нужен

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    wait = WebDriverWait(driver, 30)

    try:
        driver.get(url)
        wait.until(lambda d: d.execute_script("return document.readyState") == "complete")
        print(f"[INFO] Обрабатываем проект: {url}")

        # Ждём кнопку "Сделать ставку"
        bid_btn = wait.until(EC.element_to_be_clickable((By.ID, "add-bid")))

        # Первый клик — открыть форму
        click_element_safe(driver, bid_btn)
        print("[INFO] Кнопка 'Сделать ставку' нажата (открытие формы)")

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

        # Вставка комментария через JS до точного совпадения
        comment_area = wait.until(EC.presence_of_element_located((By.ID, "comment-0")))
        while True:
            driver.execute_script("arguments[0].value = arguments[1];", comment_area, COMMENT_TEXT)
            if comment_area.get_attribute("value").strip() == COMMENT_TEXT.strip():
                print("[INFO] Комментарий вставлен корректно")
                break
            time.sleep(0.5)

        # Второй клик по той же кнопке "Сделать ставку" для подтверждения
        click_element_safe(driver, bid_btn)
        print("[INFO] Ставка подтверждена! Цикл завершён")

    except Exception as e:
        print(f"[ERROR] Проект не обработан: {e}")

# ---------------- Телеграм ----------------
client = TelegramClient("session", api_id, api_hash)

@client.on(events.NewMessage)
async def handler(event):
    text = (event.message.text or "").lower()
    if any(k in text for k in KEYWORDS):
        print(f"[INFO] Новый проект: {text[:100]}")
        links = extract_links(text)
        if links:
            threading.Thread(target=process_project, args=(links[0],), daemon=True).start()

# ---------------- Запуск ----------------
if __name__ == "__main__":
    print("[INFO] Бот запущен. Ожидаем новые проекты...")
    client.start()
    client.run_until_disconnected()
