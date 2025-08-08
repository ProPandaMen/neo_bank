from gologin_api.main import GoLoginAPI
from database.models.task import Task, TaskStatus
from sms_api.main import get_registration_number

import config


def start():
    """
    # Шаг №1
    # Подготовка данных к работе
    """

    task = Task.create()
    task.status = TaskStatus.PREPARING
    task.save()

    # Создаем профиль в GoLogin
    task.add_log("Создаем профиль в GoLogin")
    profile = GoLoginAPI(config.GOLOGIN_API_TOKEN).create_profile("test")

    # Ищем подходящий номер телефона
    task.add_log("Ищем подходящий номер телефона")
    phone = get_registration_number()

    # Создаем запись в базу данных
    task.add_log("Создаем запись в базу данных")
    task.gologin_profile_id = profile.id
    task.phone_number = phone
    task.save()


if __name__ == "__main__":
    start()
