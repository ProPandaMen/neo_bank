from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By

from database.models.task import Task
from utils.task_screenshot import save_task_screenshot
from mts_manager.base import wait_click, wait_visible, get_driver
from sms_api.main import wait_sms_code
from utils.task_logging import log_task

from datetime import datetime, timezone, timedelta

import argparse


def start(task_id, sleep_time=5, timeout=120, screenshot=True):
    task = Task.get(id=task_id)
    if not task:
        raise Exception(f"Отсутствует задача ID {task_id}")
    log_task(task_id, "загрузка данных", f"Задача #{task_id}, номер: {task.phone_number}")

    # Инициализация драйвера
    driver = get_driver(task_id)
    log_task(task_id, "старт", f"Старт шага 2, инициализация драйвера")

    try:
        # Заходим на сайт
        driver.get("https://mtsdengi.ru/")
        log_task(task_id, "открытие сайта", "Открыт mtsdengi.ru")
        WebDriverWait(driver, sleep_time)

        driver.get("https://mtsdengi.ru/karti/debet-mts-dengi-virtual/")
        log_task(task_id, "открытие сайта", "Открыта страница оформления карты")
        WebDriverWait(driver, sleep_time)
        if screenshot:
            save_task_screenshot(driver, task_id, "step_2_1.png")

        # Вводим номер телефона
        phone_field = wait_visible(driver, '//*[@id="cardFormInput"]')
        phone_field.send_keys(task.phone_number[1:])
        log_task(task_id, "ввод данных", f"Введён номер телефона {task.phone_number}")
        WebDriverWait(driver, sleep_time)
        if screenshot:
            save_task_screenshot(driver, task_id, "step_2_2.png")

        wait_click(driver, '//*[@id="issueCard"]/div[2]/form/div/div[5]/button')
        log_task(task_id, "отправка формы", "Кнопка отправки нажата")

        # Ждем смс с кодом
        log_task(task_id, "отправка формы", "Ждем смс с кодом")
        sms_code = wait_sms_code(
            task.phone_number, 
            datetime.now(timezone.utc) - timedelta(minutes=2)
        )
        if not sms_code:
            raise Exception(f"Отсутствует задача ID {task_id}")
        log_task(task_id, "смс", f"Получен SMS-код {sms_code}")
        WebDriverWait(driver, sleep_time)

        # Вводим код
        driver.switch_to.active_element.send_keys(sms_code)
        log_task(task_id, "ввод данных", "SMS-код введён")
        WebDriverWait(driver, sleep_time)
        if screenshot:
            save_task_screenshot(driver, task_id, "step_2_3.png")

        # Ждем регистрации
        WebDriverWait(driver, timeout).until(
            EC.text_to_be_present_in_element(
                (By.TAG_NAME, "body"),
                "Карта готова"
            )
        )
        log_task(task_id, "регистрация", "Карта успешно оформлена")
        WebDriverWait(driver, sleep_time)
        if screenshot:
            save_task_screenshot(driver, task_id, "step_2_4.png")

        log_task(task_id, "завершение", "Шаг 2 завершён успешно")
    except Exception as e:
        log_task(task_id, "ошибка", f"Ошибка на шаге 2: {e}")
        raise Exception(f"Ошибка на шаге 2:\n{e}")
    finally:
        driver.quit()
        log_task(task_id, "ресурсы", "Драйвер закрыт")



if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("task_id", type=int)
    parser.add_argument("--sleep", type=int, default=5)
    parser.add_argument("--timeout", type=int, default=120)
    args = parser.parse_args()

    start(args.task_id, sleep_time=args.sleep, timeout=args.timeout)
