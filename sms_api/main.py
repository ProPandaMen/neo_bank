import requests
import time


def get_registration_number():
    sms_manager = SMSManager()
    exclude_senders = {"MTC_ID", "MTC.Premium"}

    for phone in sms_manager.get_phone_numbers():
        sms_list = sms_manager.get_sms(phone)
        senders = {sms.get("sender") for sms in sms_list}

        if not (senders & exclude_senders):
            return phone
        else:
            print(f"Excluding phone {phone} due to senders: {senders}")
        time.sleep(1)

    return None


class SMSManager:
    def get_phone_numbers(self):
        response = requests.get("http://95.179.248.237/api/phones?status=active")
        response.raise_for_status()

        data = response.json()
        return data.get("phones", [])    

    def get_sms(self, phone_number):
        response = requests.get(f"http://95.179.248.237/api/sms?&number={phone_number}")
        response.raise_for_status()

        data = response.json()
        return data.get("messages", [])


if __name__ == "__main__":
    print(get_registration_number())
