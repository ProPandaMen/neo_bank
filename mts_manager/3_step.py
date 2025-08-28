from selenium.webdriver.support.ui import WebDriverWait

from database.models.task import Task
from mts_manager.base import wait_click, wait_visible, get_driver
from sms_api.main import wait_sms_code
from utils.task_logging import log_task

from datetime import datetime, timezone, timedelta

import time

import argparse


def start(task_id, sleep_time=20):
    task = Task.get(id=task_id)
    if not task:
        raise Exception(f"Отсутствует задача ID {task_id}")    
    log_task(task_id, "загрузка данных", f"Задача #{task_id}, номер: {task.phone_number}")

    driver = get_driver()
    log_task(task_id, "инициализация", "Драйвер запущен")


    try:
        # Заходим на сайт
        log_task(task_id, "открытие сайта", "Переход на https://online.mtsdengi.ru/")
        driver.get("https://online.mtsdengi.ru/")
        WebDriverWait(driver, sleep_time)
        time.sleep(sleep_time)

        # Вводим номер телефон
        log_task(task_id, "ввод данных", f"Ввод номера телефона {task.phone_number}")            
        phone_field = wait_visible(driver, '//*[@id="login"]')
        phone_field.send_keys(task.phone_number[1:])
        WebDriverWait(driver, sleep_time)        

        # Нажимаем кнопку войти
        log_task(task_id, "отправка формы", "Кнопка 'Войти' нажата")
        wait_click(driver, '//*[@id="root"]/div[2]/main/div/div[3]/button')

        # Ждем смс с кодом
        log_task(task_id, "смс", "Ожидание SMS-кода")
        sms_code = wait_sms_code(task.phone_number, datetime.now(timezone.utc) - timedelta(minutes=2))
        WebDriverWait(driver, sleep_time)        

        # Вводим код
        log_task(task_id, "ввод данных", f"Ввод SMS-кода {sms_code}")
        driver.switch_to.active_element.send_keys(sms_code)
        WebDriverWait(driver, sleep_time)

        # Убираем рекламу
        try:
            time.sleep(sleep_time)
            log_task(task_id, "интерфейс", "Попытка закрыть рекламу")
            wait_click(driver, '//*[@id="__next"]/div[1]/div/div[2]/div[1]/div[2]')
            WebDriverWait(driver, sleep_time)
            driver.save_screenshot("viewport.png")
            log_task(task_id, "интерфейс", "Реклама закрыта")
        except Exception:
            log_task(task_id, "интерфейс", "Рекламы не было")

        # Открываем страницу с картой
        log_task(task_id, "карта", "Открываем страницу карты")
        wait_click(driver, '//*[@id="__next"]/div[1]/div/div[2]/div/div/div[3]/div/div[2]/div/div')
        WebDriverWait(driver, sleep_time)

        # Показать номер карты
        log_task(task_id, "карта", "Нажатие на кнопку 'Показать номер карты'")
        wait_click(driver, '//*[@id="__next"]/div[1]/div/div[2]/div[2]/div/div[1]/div[1]/div[2]/div/div[1]/div')
        WebDriverWait(driver, sleep_time)

        # Записываем номер карты
        card_number_block = wait_visible(driver, '//*[@id="__next"]/div[1]/div/div[2]/div[2]/div/div[1]/div[1]/div[2]/div/div[2]/div/div[1]/div/div/div/div/span')
        task.card_number = card_number_block.text
        task.save()
        log_task(task_id, "карта", f"Считан номер карты: {task.card_number}")
        WebDriverWait(driver, sleep_time)

        # Записываем номер карты
        card_date_block = wait_visible(driver, '//*[@id="__next"]/div[1]/div/div[2]/div[2]/div/div[1]/div[1]/div[2]/div/div[2]/div/div[2]/div/div/div/span')
        task.card_date = card_date_block.text
        task.save()
        log_task(task_id, "карта", f"Считана дата карты: {task.card_date}")
        WebDriverWait(driver, sleep_time)

        # Показываем CVV
        log_task(task_id, "карта", "Нажатие на кнопку 'Показать CVV'")
        wait_click(driver, '//*[@id="__next"]/div[1]/div/div[2]/div[2]/div/div[1]/div[1]/div[2]/div/div[2]/div/div[3]/div/div/i')
        WebDriverWait(driver, sleep_time)

        # Записываем CVV
        card_cvv_value = wait_visible(driver, '//*[@id="__next"]/div[1]/div/div[2]/div[2]/div/div[1]/div[1]/div[2]/div/div[2]/div/div[3]/div/div/div/span[2]')
        task.card_cvv = card_cvv_value.text
        task.save()
        log_task(task_id, "карта", f"Считан CVV: {task.card_cvv}")
        WebDriverWait(driver, sleep_time)

        log_task(task_id, "завершение", "Шаг 3 выполнен успешно")
    except Exception as e:
        log_task(task_id, "ошибка", f"Ошибка на шаге 3: {e}")
        raise Exception(f"Ошибка на шаге 3:\n{e}")
    finally:
        # Закрываем драйвер
        driver.quit()
        log_task(task_id, "ресурсы", "Драйвер закрыт")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("task_id", type=int)
    parser.add_argument("--sleep", type=int, default=5)
    parser.add_argument("--timeout", type=int, default=120)
    args = parser.parse_args()

    start(args.task_id, sleep_time=args.sleep, timeout=args.timeout)
