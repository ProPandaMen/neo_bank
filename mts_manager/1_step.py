from gologin_api.main import GoLoginAPI
from database.manager.task import TaskManager
from sms_api.main import get_registration_number

import config


def start():
    """
    # Шаг №1
    # Подготовка данных к работе
    """

    # Создаем профиль в GoLogin
    print("Создаем профиль в GoLogin")
    profile = GoLoginAPI(config.GOLOGIN_API_TOKEN).create_profile("test")

    # Ищем подходящий номер телефона
    print("Ищем подходящий номер телефона")
    phone = get_registration_number()

    # Создаем запись в базу данных
    print("Создаем запись в базу данных")
    TaskManager().create_task(
        gologin_profile_id=profile.id,
        phone_number=phone
    )


if __name__ == "__main__":
    start()
