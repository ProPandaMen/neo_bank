from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from gologin_api.main import GoLoginAPI
from gologin import GoLogin

from enum import Enum

import threading
import config
import time



class TaskStage(Enum):
    PREPARE = "Подготовка"
    STEP1 = "Шаг 1"
    STEP2 = "Шаг 2"
    DONE = "Завершено"
    FAILED = "Ошибка"



class MTSTask:
    def __init__(self, task_id):
        self.task_id = task_id
        self.stage = TaskStage.PREPARE
        self.retry_counts = {TaskStage.STEP1: 0, TaskStage.STEP2: 0}
        self.max_retries = 3
        self.success = False


    def run(self):
        try:
            # 1. Подготовка
            self.stage = TaskStage.PREPARE
            time.sleep(1)  # эмулируем работу
            # 2. Выполнение шага 1 с ретраями
            self.stage = TaskStage.STEP1
            while self.retry_counts[TaskStage.STEP1] < self.max_retries:
                if self.do_step1():
                    break
                self.retry_counts[TaskStage.STEP1] += 1
                time.sleep(1)
            else:
                self.stage = TaskStage.FAILED
                return

            # 3. Выполнение шага 2 с ретраями
            self.stage = TaskStage.STEP2
            while self.retry_counts[TaskStage.STEP2] < self.max_retries:
                if self.do_step2():
                    break
                self.retry_counts[TaskStage.STEP2] += 1
                time.sleep(1)
            else:
                self.stage = TaskStage.FAILED
                return

            self.stage = TaskStage.DONE
            self.success = True
        except Exception as ex:
            self.stage = TaskStage.FAILED


    def do_step1(self):
        # Возвращает True если успех, иначе False
        print(f"Выполнение шага 1, попытка {self.retry_counts[TaskStage.STEP1]+1}")
        # Тут твоя логика. Для теста эмулируем ошибку:
        return self.retry_counts[TaskStage.STEP1] == 2


    def do_step2(self):
        print(f"Выполнение шага 2, попытка {self.retry_counts[TaskStage.STEP2]+1}")
        # Для примера — успех со второй попытки:
        return self.retry_counts[TaskStage.STEP2] >= 1


# def main(profile, phone_number):
#     profile = GoLoginAPI(config.GOLOGIN_API_TOKEN).create_profile("test")

#     gl = GoLogin({
#         "token": config.GOLOGIN_API_TOKEN,
#         "profile_id": profile.id
#     })
    
#     debugger_address = gl.start()

#     chromium_version = gl.get_chromium_version()
#     service = Service(ChromeDriverManager(driver_version=chromium_version).install())

#     chrome_options = webdriver.ChromeOptions()
#     chrome_options.add_experimental_option("debuggerAddress", debugger_address)

#     driver = webdriver.Chrome(service=service, options=chrome_options)

#     try:
#         driver.get("https://mtsdengi.ru/")        
#         time.sleep(5)

#         driver.get("https://mtsdengi.ru/karti/debet-mts-dengi-virtual/")
#         time.sleep(5)

#         phone_field = driver.find_element(By.XPATH, '//*[@id="cardFormInput"]')
#         phone_field.send_keys(phone_number)
#         time.sleep(5)

#         button = driver.find_element(By.XPATH, '//*[@id="issueCard"]/div[2]/form/div/div[5]/button')
#         button.click()

#         time.sleep(5)

#         sms_code = input("Введите код из SMS: ")
#         driver.switch_to.active_element.send_keys(sms_code)

#         time.sleep(10000)
#     finally:
#         driver.quit()
#         gl.stop()

# if __name__ == "__main__":
#     # main(profile, phone_number)
#     pass
