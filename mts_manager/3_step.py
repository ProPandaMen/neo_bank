from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By

from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from gologin import GoLogin

from gologin_api.main import GoLoginAPI
from database.models.task import Task, TaskStatus
from sms_api.main import wait_sms_code

from datetime import datetime, timezone
import config
import time


def start(task_id, sleep_time=20, timeout=120):
    """
    # Шаг №3
    # Получаем данные карты
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

        # driver.get("https://online.mtsdengi.ru/")
        driver.find_element(
            By.XPATH,
            '//*[@id="__next"]/div/div[2]/div[1]/div[2]/div[2]/a'
        ).click()
        WebDriverWait(driver, sleep_time)
        time.sleep(sleep_time)

        # Вводим номер телефона
        task.add_log("Вводим номер телефона")
        phone_field = driver.find_element(By.XPATH, '//*[@id="login"]')
        phone_field.send_keys(task.phone_number[1:])
        WebDriverWait(driver, sleep_time)

        # Нажимаем кнопку войти
        task.add_log("Нажимаем кнопку войти")
        driver.find_element(
            
            '//*[@id="root"]/div[2]/main/div/div[3]/button'
        ).click()

        # Ждем смс с кодом        
        task.add_log("Ждем смс с кодом")
        sms_code = wait_sms_code(task.phone_number, datetime.now(timezone.utc))
        WebDriverWait(driver, sleep_time)

        # Вводим код    
        task.add_log("Вводим код")
        driver.switch_to.active_element.send_keys(sms_code)
        WebDriverWait(driver, sleep_time * 2)

        # Убираем рекламу
        # Нужно ?
        
        # Открываем страницу с картой
        task.add_log("Открываем страницу с картой")
        driver.find_element(
            By.XPATH, '//*[@id="__next"]/div[1]/div/div[2]/div/div/div[3]/div/div[2]/div/div'
        ).click()
        WebDriverWait(driver, sleep_time * 2)

        # Показать номер карты
        task.add_log("Показать номер карты")
        driver.find_element(
            By.XPATH, '//*[@id="__next"]/div[1]/div/div[2]/div[2]/div/div[1]/div[1]/div[2]/div/div[1]/div'
        ).click()
        WebDriverWait(driver, sleep_time * 2)

        # Записываем номер карты
        task.add_log("Показать номер карты")
        card_number_block = driver.find_element(By.XPATH, '//*[@id="__next"]/div[1]/div/div[2]/div[2]/div/div[1]/div[1]/div[2]/div/div[2]/div/div[1]/div/div/div/div/span')
        print(card_number_block.text)

        # Записываем номер карты
        task.add_log("Записываем номер карты")
        card_date_block = driver.find_element(By.XPATH, '//*[@id="__next"]/div[1]/div/div[2]/div[2]/div/div[1]/div[1]/div[2]/div/div[2]/div/div[2]/div/div/div/span')
        print(card_date_block.text)
        WebDriverWait(driver, sleep_time * 2)

        # Показываем CVV
        task.add_log("Показываем CVV")
        driver.find_element(
            By.XPATH, '//*[@id="__next"]/div[1]/div/div[2]/div[2]/div/div[1]/div[1]/div[2]/div/div[2]/div/div[3]/div/div/i/svg'
        ).click()
        WebDriverWait(driver, sleep_time * 2)

        # Записываем CVV
        task.add_log("Записываем CVV")
        card_cvv_value = driver.find_element(By.XPATH, '//*[@id="__next"]/div[1]/div/div[2]/div[2]/div/div[1]/div[1]/div[2]/div/div[2]/div/div[3]/div/div/div/span[2]')
        print(card_cvv_value.text)
        WebDriverWait(driver, sleep_time * 2)
    finally:
        # Закрываем драйвер
        task.add_log("Закрываем драйвер")
        gl.stop()
        driver.quit()


if __name__ == "__main__":
    start(3)
