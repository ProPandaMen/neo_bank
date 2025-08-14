from selenium.webdriver.support.ui import WebDriverWait

from database.models.task import Task, TaskStatus
from mts_manager.base import wait_click, wait_visible, get_driver
from sms_api.main import wait_sms_code

from datetime import datetime, timezone, timedelta

import time


def start(task_id, sleep_time=20):
    driver = get_driver()

    task = Task.get(id=task_id)
    task.status = TaskStatus.GETTING_CARD
    task.save()

    try:
        # Заходим на сайт        
        driver.get("https://online.mtsdengi.ru/")
        WebDriverWait(driver, sleep_time)
        time.sleep(sleep_time)

        # Вводим номер телефон                
        phone_field = wait_visible(driver, '//*[@id="login"]')
        phone_field.send_keys(task.phone_number[1:])
        WebDriverWait(driver, sleep_time)        

        # Нажимаем кнопку войти
        wait_click(driver, '//*[@id="root"]/div[2]/main/div/div[3]/button')

        # Ждем смс с кодом
        sms_code = wait_sms_code(task.phone_number, datetime.now(timezone.utc) - timedelta(minutes=2))
        WebDriverWait(driver, sleep_time)        

        # Вводим код
        driver.switch_to.active_element.send_keys(sms_code)
        WebDriverWait(driver, sleep_time)

        # Убираем рекламу
        try:
            time.sleep(sleep_time)
            wait_click(driver, '//*[@id="__next"]/div[1]/div/div[2]/div[1]/div[2]')
            WebDriverWait(driver, sleep_time)
            driver.save_screenshot("viewport.png")
        except Exception:
            pass

        # Открываем страницу с картой
        wait_click(driver, '//*[@id="__next"]/div[1]/div/div[2]/div/div/div[3]/div/div[2]/div/div')
        WebDriverWait(driver, sleep_time)

        # Показать номер карты
        wait_click(driver, '//*[@id="__next"]/div[1]/div/div[2]/div[2]/div/div[1]/div[1]/div[2]/div/div[1]/div')
        WebDriverWait(driver, sleep_time)

        # Записываем номер карты
        card_number_block = wait_visible(driver, '//*[@id="__next"]/div[1]/div/div[2]/div[2]/div/div[1]/div[1]/div[2]/div/div[2]/div/div[1]/div/div/div/div/span')
        task.card_number = card_number_block.text
        task.save()
        WebDriverWait(driver, sleep_time)

        # Записываем номер карты
        card_date_block = wait_visible(driver, '//*[@id="__next"]/div[1]/div/div[2]/div[2]/div/div[1]/div[1]/div[2]/div/div[2]/div/div[2]/div/div/div/span')
        task.card_date = card_date_block.text
        task.save()
        WebDriverWait(driver, sleep_time)

        # Показываем CVV 
        wait_click(driver, '//*[@id="__next"]/div[1]/div/div[2]/div[2]/div/div[1]/div[1]/div[2]/div/div[2]/div/div[3]/div/div/i')
        WebDriverWait(driver, sleep_time)

        # Записываем CVV
        card_cvv_value = wait_visible(driver, '//*[@id="__next"]/div[1]/div/div[2]/div[2]/div/div[1]/div[1]/div[2]/div/div[2]/div/div[3]/div/div/div/span[2]')
        task.card_cvv = card_cvv_value.text
        task.save()
        WebDriverWait(driver, sleep_time)

        task.status = TaskStatus.FINISHED
        task.save()
    finally:
        # Закрываем драйвер
        driver.quit()


if __name__ == "__main__":
    start(4)
