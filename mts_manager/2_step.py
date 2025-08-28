from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By

from database.models.task import Task
from mts_manager.base import wait_click, wait_visible, get_driver
from sms_api.main import wait_sms_code

from datetime import datetime, timezone


def start(task_id, sleep_time=5, timeout=120):
    driver = get_driver()
    
    task = Task.get(id=task_id)
    task.save()

    try:
        # Заходим на сайт        
        driver.get("https://mtsdengi.ru/")
        WebDriverWait(driver, sleep_time)
        driver.get("https://mtsdengi.ru/karti/debet-mts-dengi-virtual/")
        WebDriverWait(driver, sleep_time)

        # Вводим номер телефона        
        phone_field = wait_visible(driver, '//*[@id="cardFormInput"]')
        phone_field.send_keys(task.phone_number[1:])
        WebDriverWait(driver, sleep_time)

        wait_click(driver, '//*[@id="issueCard"]/div[2]/form/div/div[5]/button')

        # Ждем смс с кодом        
        sms_code = wait_sms_code(task.phone_number, datetime.now(timezone.utc))
        WebDriverWait(driver, sleep_time)

        # Вводим код        
        driver.switch_to.active_element.send_keys(sms_code)
        WebDriverWait(driver, sleep_time)

        # Ждем регистрации        
        WebDriverWait(driver, timeout).until(
            EC.text_to_be_present_in_element(
                (By.TAG_NAME, "body"),
                "Карта готова"
            )
        )
        WebDriverWait(driver, sleep_time)
    except Exception as e:
        raise Exception(f"Ошибка на шаге 2:\n{e}")
    finally:
        # Закрываем драйвер
        driver.quit()


if __name__ == "__main__":
    start(2)
