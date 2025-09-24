import re
import threading
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import ElementClickInterceptedException, TimeoutException
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

# ===== Текст заявки =====
COMMENT_TEXT = """Доброго дня!  

Ознайомився із завданням і готовий приступити до виконання.  

Стек: Figma / HTML (BEM), SCSS, JS / WordPress ACF PRO  

Приклади робіт доступні в портфоліо.  

Зв'яжіться зі мною в особистих повідомленнях. Дякую!
"""

# ---------------- Функции ----------------
def extract_links(text):
    return re.findall(r"https?://[^\s]+", text)

def type_slow(element, text, delay=0.16):
    for ch in text:
        element.send_keys(ch)
        time.sleep(delay)

def click_element_safe(driver, element, retries=5, delay=0.5):
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

def insert_comment(driver, wait):
    comment_area = wait.until(EC.presence_of_element_located((By.ID, "comment-0")))
    while True:
        comment_area.clear()
        type_slow(comment_area, COMMENT_TEXT)
        entered_text = comment_area.get_attribute("value")
        if entered_text.strip() == COMMENT_TEXT.strip():
            break
        time.sleep(0.5)

def make_bid(driver, wait):
    # Кнопка "Сделать ставку"
    bid_btn = wait.until(EC.element_to_be_clickable((By.ID, "add-bid")))
    click_element_safe(driver, bid_btn)
    
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

    # Печатаем комментарий
    insert_comment(driver, wait)

    # Нажимаем кнопку "Добавить"
    add_btn = wait.until(EC.element_to_be_clickable((By.ID, "add-0")))
    if click_element_safe(driver, add_btn):
        print("[INFO] Заявка успешно отправлена!")
    else:
        print("[ERROR] Не удалось нажать кнопку 'Добавить'")

def process_project(url):
    chrome_options = Options()
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    # Без headless, чтобы можно было авторизоваться вручную
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    wait = WebDriverWait(driver, 30)

    try:
        driver.get(url)
        wait.until(lambda d: d.execute_script("return document.readyState") == "complete")
        print(f"[INFO] Обрабатываем проект: {url}")

        # Ждем авторизацию
        for _ in range(120):
            try:
                driver.find_element(By.ID, "add-bid")
                print("[INFO] Авторизация завершена")
                break
            except:
                time.sleep(1)

        make_bid(driver, wait)
        print("[INFO] Проект обработан, браузер остаётся открытым")

    except Exception as e:
        print(f"[ERROR] Ошибка обработки проекта: {e}")

# ---------------- Телеграм ----------------
client = TelegramClient("session", api_id, api_hash)

@client.on(events.NewMessage)
async def handler(event):
    text = (event.message.text or "").lower()
    if any(k in text for k in KEYWORDS):
        links = extract_links(text)
        if links:
            threading.Thread(target=process_project, args=(links[0],), daemon=True).start()

# ---------------- Запуск ----------------
if __name__ == "__main__":
    print("[INFO] Бот запущен. Ожидаем новые проекты...")
    client.start()
    client.run_until_disconnected()
