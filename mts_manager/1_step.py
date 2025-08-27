from database.models.task import Task
from sms_api.main import get_registration_number
from proxy_manager.main import Proxy

import requests


def start(task_id):    
    task = Task.get(id=task_id)
    task.add_log(f"Start task ID:{task_id}")
    
    # Ищем подходящий номер телефона
    phone = get_registration_number()
    task.add_log(f"Select phone: {phone}")

    # Создаем запись в базу данных
    task.phone_number = phone
    task.save()

    # Меняем IP прокси    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows; U; Windows NT 6.1; WOW64; en-US) AppleWebKit/533.34 (KHTML, like Gecko) Chrome/53.0.3445.122 Safari/603.9 Edge/15.62649"
    }

    url = Proxy().change_ip_url
    data = requests.get(url, headers=headers)
    task.add_log(f"Edit proxt IP")

    if data.json().get('code') != 200:
        raise Exception("Не удалось сменить IP прокси")
    
    task.add_log(f"Finish task")



if __name__ == "__main__":
    start(1)
