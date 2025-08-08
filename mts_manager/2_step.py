from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By

from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from gologin import GoLogin

from gologin_api.main import GoLoginAPI
from database.models.task import Task, TaskStatus
from mts_manager.base import wait_click, wait_visible
from sms_api.main import wait_sms_code

from datetime import datetime, timezone
import config


def start(task_id, sleep_time=5, timeout=120):
    """
    # Шаг №2
    # Регистрируемся на MTS деньги
    """
    
    task = Task.get(id=task_id)
    task.status = TaskStatus.REGISTERING
    task.save()

    # Создаем сессию GoLogin
    task.add_log("Создаем сессию GoLogin")
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
        task.add_log("Заходим на сайт")
        driver.get("https://mtsdengi.ru/")
        WebDriverWait(driver, sleep_time)

        driver.get("https://mtsdengi.ru/karti/debet-mts-dengi-virtual/")
        WebDriverWait(driver, sleep_time)

        # Вводим номер телефона
        task.add_log("Вводим номер телефона")
        phone_field = wait_visible(driver, '//*[@id="cardFormInput"]')
        phone_field.send_keys(task.phone_number[1:])
        WebDriverWait(driver, sleep_time)

        button = driver.find_element(By.XPATH, '//*[@id="issueCard"]/div[2]/form/div/div[5]/button')
        button.click()

        # Ждем смс с кодом
        task.add_log("Ждем смс с кодом")
        sms_code = wait_sms_code(task.phone_number, datetime.now(timezone.utc))
        WebDriverWait(driver, sleep_time)

        # Вводим код
        task.add_log("Вводим код")
        driver.switch_to.active_element.send_keys(sms_code)
        WebDriverWait(driver, sleep_time)

        # Ждем регистрации
        task.add_log("Ждем регистрации")
        WebDriverWait(driver, timeout).until(
            EC.text_to_be_present_in_element(
                (By.TAG_NAME, "body"),
                "Карта готова"
            )
        )
        WebDriverWait(driver, sleep_time)
    finally:
        # Закрываем драйвер
        task.add_log("Закрываем драйвер")
        gl.stop()
        driver.quit()


if __name__ == "__main__":
    start(1)
