from database.models.task import Task
from proxy_manager.main import Proxy
from sms_api.main import SMSManager

from sms_api.main import get_registration_number
from utils.task_logging import log_task

import requests


def start(task_id):
    task = Task.get(id=task_id)
    log_task(task_id, "старт", f"Старт задачи #{task_id}")
    
    # Ищем подходящий номер телефона
    phone = get_registration_number(task_id)
    log_task(task_id, "поиск номера", f"Выбран номер: {phone}")

    SMSManager().update_tag(phone)
    log_task(task_id, "обновления тега", f"Тег обновлен: {phone}")

    # Создаем запись в базу данных
    task.phone_number = phone
    task.save()
    log_task(task_id, "сохранение данных", "Номер сохранён")

    # Меняем IP прокси    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows; U; Windows NT 6.1; WOW64; en-US) AppleWebKit/533.34 (KHTML, like Gecko) Chrome/53.0.3445.122 Safari/603.9 Edge/15.62649"
    }

    url = Proxy().change_ip_url
    data = requests.get(url, headers=headers)
    log_task(task_id, "смена ip", "Запрос на смену IP отправлен")

    if data.json().get('code') != 200:
        log_task(task_id, "смена ip", "Не удалось сменить IP")
        raise Exception("Не удалось сменить IP прокси")
    
    log_task(task_id, "завершение", "Шаг завершён")


if __name__ == "__main__":
    start(1)
