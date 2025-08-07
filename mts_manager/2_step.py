from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By

from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from gologin import GoLogin

from gologin_api.main import GoLoginAPI
from database.manager.task import TaskManager
from sms_api.main import wait_sms_code

from datetime import datetime, timezone
import config
import time


def start(task_id, sleep_time=5, timeout=120):
    """
    # Шаг №2
    # Регистрируемся на MTS деньги
    """

    # Создаем сессию GoLogin
    print("Создаем сессию GoLogin")
    task = TaskManager().get_task_by_id(task_id)
    profile = GoLoginAPI(config.GOLOGIN_API_TOKEN).get_profile_by_id(task.gologin_profile_id)

    try:
        gl = GoLogin({
            "token": config.GOLOGIN_API_TOKEN,
            "profile_id": profile.id
        })
        
        debugger_address = gl.start()

        chromium_version = gl.get_chromium_version()
        service = Service(ChromeDriverManager(driver_version=chromium_version).install())

        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_experimental_option("debuggerAddress", debugger_address)

        driver = webdriver.Chrome(service=service, options=chrome_options)

        # Заходим на сайт
        print("Заходим на сайт")
        driver.get("https://mtsdengi.ru/")        
        time.sleep(sleep_time)

        driver.get("https://mtsdengi.ru/karti/debet-mts-dengi-virtual/")
        time.sleep(sleep_time)

        # Вводим номер телефона
        print("Вводим номер телефона")
        phone_field = driver.find_element(By.XPATH, '//*[@id="cardFormInput"]')
        phone_field.send_keys(task.phone_number[1:])
        time.sleep(sleep_time)

        button = driver.find_element(By.XPATH, '//*[@id="issueCard"]/div[2]/form/div/div[5]/button')
        button.click()

        # Ждем смс с кодом
        print("Ждем смс с кодом")
        sms_code = wait_sms_code(task.phone_number, datetime.now(timezone.utc))
        time.sleep(sleep_time)

        # Вводим код
        print("Вводим код")
        driver.switch_to.active_element.send_keys(sms_code)

        # Ждем регистрации
        print("Ждем регистрации")
        WebDriverWait(driver, timeout).until(
            EC.text_to_be_present_in_element(
                (By.TAG_NAME, "body"),
                "Карта готова"
            )
        )
    finally:
        # Закрываем драйвер
        print("Закрываем драйвер")
        driver.quit()


if __name__ == "__main__":
    # Пример использования
    task_id = 3
    start(task_id)
