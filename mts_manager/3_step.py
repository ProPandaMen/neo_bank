from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By

from webdriver_manager.chrome import ChromeDriverManager
from selenium import webdriver
from gologin import GoLogin

from database.models.task import Task, TaskStatus
from gologin_api.main import GoLoginAPI
from mts_manager.base import wait_click, wait_visible
from sms_api.main import wait_sms_code

from datetime import datetime, timezone
import config


def start(task_id, sleep_time=20, timeout=120):
    """
    # Шаг №3
    # Получаем данные карты
    """
    
    task = Task.get(id=task_id)
    task.status = TaskStatus.GETTING_CARD
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

        # Нажимаем кнопку входа
        task.add_log("Нажимаем кнопку авторизации")
        wait_click(driver, '//*[@id="__next"]/div/div[2]/div[1]/div[2]/div[2]/a')
        WebDriverWait(driver, sleep_time)

        # Вводим номер телефона
        task.add_log("Вводим номер телефона")
        phone_field = wait_visible(driver, '//*[@id="login"]')
        phone_field.send_keys(task.phone_number[1:])
        WebDriverWait(driver, sleep_time)

        # Нажимаем кнопку войти
        task.add_log("Нажимаем кнопку войти")
        wait_click(driver, '//*[@id="root"]/div[2]/main/div/div[3]/button')

        # Ждем смс с кодом        
        task.add_log("Ждем смс с кодом")
        sms_code = wait_sms_code(task.phone_number, datetime.now(timezone.utc))
        WebDriverWait(driver, sleep_time)

        # Вводим код    
        task.add_log("Вводим код")
        driver.switch_to.active_element.send_keys(sms_code)
        WebDriverWait(driver, sleep_time)

        # Убираем рекламу
        try:
            task.add_log("Убираем рекламу")
            wait_click(driver, '//*[@id="__next"]/div[1]/div/div[2]/div[1]/div[2]')
            WebDriverWait(driver, sleep_time)
        except Exception:
            pass
        
        # Открываем страницу с картой
        task.add_log("Открываем страницу с картой")
        wait_click(driver, '//*[@id="__next"]/div[1]/div/div[2]/div/div/div[3]/div/div[2]/div/div')
        WebDriverWait(driver, sleep_time)

        # Показать номер карты
        task.add_log("Показать номер карты")        
        wait_click(driver, '//*[@id="__next"]/div[1]/div/div[2]/div[2]/div/div[1]/div[1]/div[2]/div/div[1]/div')
        WebDriverWait(driver, sleep_time)

        # Записываем номер карты
        task.add_log("Показать номер карты")
        card_number_block = wait_visible(driver, '//*[@id="__next"]/div[1]/div/div[2]/div[2]/div/div[1]/div[1]/div[2]/div/div[2]/div/div[1]/div/div/div/div/span')
        task.card_number = card_number_block.text
        task.save()
        WebDriverWait(driver, sleep_time)

        # Записываем номер карты
        task.add_log("Записываем номер карты")
        card_date_block = wait_visible(driver, '//*[@id="__next"]/div[1]/div/div[2]/div[2]/div/div[1]/div[1]/div[2]/div/div[2]/div/div[2]/div/div/div/span')
        task.card_date = card_date_block.text
        task.save()
        WebDriverWait(driver, sleep_time)

        # Показываем CVV
        task.add_log("Показываем CVV")        
        wait_click(driver, '//*[@id="__next"]/div[1]/div/div[2]/div[2]/div/div[1]/div[1]/div[2]/div/div[2]/div/div[3]/div/div/i')
        WebDriverWait(driver, sleep_time)

        # Записываем CVV
        task.add_log("Записываем CVV")
        card_cvv_value = wait_visible(driver, '//*[@id="__next"]/div[1]/div/div[2]/div[2]/div/div[1]/div[1]/div[2]/div/div[2]/div/div[3]/div/div/div/span[2]')
        task.card_cvv = card_cvv_value.text
        task.save()
        WebDriverWait(driver, sleep_time)

        task.status = TaskStatus.FINISHED
        task.save()
    finally:
        # Закрываем драйвер
        task.add_log("Закрываем драйвер")
        gl.stop()
        driver.quit()


if __name__ == "__main__":
    start(2)
