import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

# ==== Налаштування Selenium ====
options = webdriver.ChromeOptions()
options.add_argument("--start-maximized")

driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

try:
    # 1. Відкриваємо сторінку проекту
    url = "https://freelancehunt.com/project/html-css-zverstati-storinki-po/1556809.html"
    driver.get(url)
    print("[INFO] Сторінка проекту відкрита")

    # 2. Чекаємо авторизацію (вручну)
    input("[INFO] Увійдіть у свій акаунт у браузері, потім натисніть Enter у консолі...")

    # 3. Знаходимо textarea для коментаря
    comment_box = driver.find_element(By.CSS_SELECTOR, "textarea[name='comment']")
    comment_box.clear()
    comment_box.send_keys("Привіт! Готовий виконати ваше завдання якісно та вчасно ✅")

    print("[INFO] Коментар вставлено")

    time.sleep(1)

    # 4. Імітуємо TAB 6 разів і ENTER на 7-й
    for _ in range(6):
        comment_box.send_keys(Keys.TAB)
        time.sleep(0.3)

    comment_box.send_keys(Keys.ENTER)
    print("[SUCCESS] Ставка відправлена!")

    time.sleep(3)

finally:
    # 5. Закриваємо браузер
    driver.quit()
    print("[INFO] Браузер закрито")
