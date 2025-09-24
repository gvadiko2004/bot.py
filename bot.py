from telethon import TelegramClient, events
from plyer import notification
import threading
import os
import winsound
import re
import time
import subprocess
import sys

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options

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

Стек: html (bem), scss, js / WordPress ACF PRO

Щоб ви були впевнені, що під час роботи не виникне проблем, можете ознайомитися з моєю останньою роботою:

https://telya.ch/

Також наводжу посилання на інші проекти:

https://gvadiko2004.github.io/grill/
https://gvadiko2004.github.io/Anon-shop/
https://iliarchie.github.io/cates/

Якщо вас зацікавив мій відгук, зв'яжіться зі мною в особистих повідомленнях.

Заздалегідь дякую"""

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sound_path = os.path.join(BASE_DIR, "message.wav")
chromedriver_path = os.path.join(BASE_DIR, "chromedriver.exe")

def play_sound():
    winsound.PlaySound(sound_path, winsound.SND_FILENAME | winsound.SND_ASYNC)

def play_sound_thread():
    threading.Thread(target=play_sound, daemon=True).start()

def extract_links(text):
    cleaned_text = text.replace("**", "")
    return re.findall(r"https?://[^\s]+", cleaned_text)

def start_chrome_debug():
    import socket
    s = socket.socket()
    try:
        s.connect(('127.0.0.1', 9222))
        s.close()
        print("Chrome с remote debugging уже запущен.")
        return
    except:
        pass

    chrome_path = r"C:\Program Files\Google\Chrome\Application\chrome.exe"  # поправь под себя
    if not os.path.exists(chrome_path):
        print("Не найден Chrome по пути:", chrome_path)
        sys.exit(1)
    user_data_dir = os.path.join(BASE_DIR, "chrome_profile")
    os.makedirs(user_data_dir, exist_ok=True)

    subprocess.Popen([
        chrome_path,
        "--remote-debugging-port=9222",
        f"--user-data-dir={user_data_dir}",
        "--no-first-run",
        "--no-default-browser-check",
    ], shell=False)
    print("Запущен Chrome с remote debugging на порту 9222.")
    time.sleep(3)

def type_text_slowly(element, text, delay=0.02):
    """Ввод текста посимвольно с задержкой"""
    for ch in text:
        element.send_keys(ch)
        time.sleep(delay)

def open_link_and_click(url):
    options = Options()
    options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")
    service = Service(chromedriver_path)
    driver = webdriver.Chrome(service=service, options=options)

    try:
        # Открываем новую вкладку
        driver.execute_script(f"window.open('{url}', '_blank');")
        driver.switch_to.window(driver.window_handles[-1])

        wait = WebDriverWait(driver, 20)

        # Кликаем кнопку "Сделать ставку"
        button = wait.until(EC.element_to_be_clickable((By.ID, "add-bid")))
        button.click()
        print("✅ Кнопка 'Сделать ставку' нажата!")

        # Получаем сумму заказа из span
        try:
            price_span = wait.until(EC.presence_of_element_located((
                By.CSS_SELECTOR,
                "span.text-green.bold.pull-right.price.with-tooltip.hidden-xs"
            )))
            raw_price = price_span.text
            price_digits = re.sub(r"[^\d]", "", raw_price)
            if not price_digits:
                price_digits = "1111"
            print(f"💰 Сумма для ввода: {price_digits}")
        except Exception:
            price_digits = "1111"
            print("⚠️ Сумма не найдена, вводим 1111")

        # Вводим сумму в input#amount-0
        amount_input = wait.until(EC.element_to_be_clickable((By.ID, "amount-0")))
        amount_input.click()
        time.sleep(0.3)
        amount_input.clear()
        type_text_slowly(amount_input, price_digits)

        # Вводим 3 в input#days_to_deliver-0
        days_input = wait.until(EC.element_to_be_clickable((By.ID, "days_to_deliver-0")))
        days_input.click()
        time.sleep(0.3)
        days_input.clear()
        type_text_slowly(days_input, "3")

        # Вводим комментарий в textarea#comment-0
        textarea = wait.until(EC.element_to_be_clickable((By.ID, "comment-0")))
        textarea.click()
        time.sleep(0.5)
        type_text_slowly(textarea, COMMENT_TEXT)

        print("✅ Все данные введены, нажимаем кнопку 'Добавить'...")

        # Нажимаем кнопку "Добавить"
        submit_btn = wait.until(EC.element_to_be_clickable((
            By.CSS_SELECTOR,
            "button#add-0.btn.btn-primary.btn-lg.ladda-button"
        )))
        submit_btn.click()

        print("✅ Кнопка 'Добавить' нажата! Задача выполнена.")

        # Оставляем вкладку открытой для проверки
        time.sleep(5)

    except Exception as e:
        print(f"❌ Ошибка в open_link_and_click: {e}")

client = TelegramClient("session", api_id, api_hash)

@client.on(events.NewMessage)
async def handler(event):
    message_text = (event.message.text or "").lower()
    if any(keyword in message_text for keyword in KEYWORDS):
        print(f"🔔 Нашёл проект: {message_text[:100]}")

        play_sound_thread()

        notification.notify(
            title="Новый проект на Freelancehunt!",
            message=message_text[:150],
            timeout=10
        )

        links = extract_links(message_text)
        if links:
            print(f"🌐 Открываю и кликаю по ссылке: {links[0]}")
            threading.Thread(target=open_link_and_click, args=(links[0],), daemon=True).start()

if __name__ == "__main__":
    start_chrome_debug()
    print("✅ Бот запущен, ждёт сообщения...")
    client.start()
    client.run_until_disconnected()
