from celery.utils.log import get_task_logger
from utils.task_logging import log_task

from datetime import datetime, timezone

import requests
import time
import re


def get_registration_number(task_id=None):
    attempt = 0
    
    sms_manager = SMSManager()
    exclude_senders = {"MTC.dengi", "MTC_ID", "MTC.Premium", "MTS.dengi"}

    for phone in sms_manager.get_phone_numbers():
        if task_id:
            log_task(task_id, "Поиск номера", f"Попытка поиска номера телефона №{attempt}")        

        sms_list = sms_manager.get_sms(phone)
        if not sms_list:            
            return phone

        senders = {sms.get("sender") for sms in sms_list}
        if not (senders & exclude_senders):
            return phone
                
        if task_id:
            log_task(task_id, "Поиск номера", f"Пропускае номер {phone}")

        attempt += 1
        time.sleep(1)

    return None


def parse_api_datetime(dt_string):
    try:
        nums = re.findall(r'\d+', dt_string)
        if len(nums) >= 7:
            year, month, day, hour, minute, second, microsecond = map(int, nums[:7])
            return datetime(year, month, day, hour, minute, second, microsecond, tzinfo=timezone.utc)
    except Exception:
        pass
    return None


def wait_sms_code(phone_number, after_datetime, timeout=120, poll_interval=5, authorization=False):
    start_time = time.time()    
    code_pattern = re.compile(r'\b\d{4,6}\b')
    allowed_senders = {"MTC.dengi", "MTS.dengi", "MTC_ID", "MTC.Premium"}

    while time.time() - start_time < timeout:
        sms_list = SMSManager().get_sms(phone_number)
        for sms in sms_list:
            sender = sms.get("sender", "")
            if sender not in allowed_senders:
                continue

            event_date = sms.get("event_date")
            if isinstance(event_date, str):
                event_date = parse_api_datetime(event_date)
            if not event_date:
                continue

            if event_date > after_datetime:
                text = sms.get("text", "")
                match = code_pattern.search(text)
                if match:
                    return match.group(0)
                
        time.sleep(poll_interval)

    return None


class SMSManager:
    def get_phone_numbers(self, tag_name="__EMPTY__"):
        url = f"http://95.179.248.237/api/phones?tag_name={tag_name}"
        response = requests.get(url)
        response.raise_for_status()

        data = response.json()
        return data.get("phones", [])    

    def get_sms(self, phone_number):
        url = f"http://95.179.248.237/api/sms?&number={phone_number}"
        response = requests.get(url)
        response.raise_for_status()

        data = response.json()
        return data.get("messages", [])
    
    def update_tag(self, phone_numer, tag_name="bot"):
        url = "http://95.179.248.237/api/phones/update"
        data = {
            "phone_number": phone_numer,
            "tag_name": tag_name
        }
        response = requests.post(url, data=data)
        response.raise_for_status()

        return response.json()



if __name__ == "__main__":
    # print(get_registration_number())
    # print(SMSManager().get_sms("79815292153"))

    print(wait_sms_code("79510406674", datetime.now(timezone.utc)))
