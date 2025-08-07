from selenium.webdriver.common.by import By
from selenium import webdriver

import requests
import time


GLOGIN_API_TOKEN = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI2ODgwMjg5OTRlMzEzMDE1YTNkNWM5MDAiLCJ0eXBlIjoiZGV2Iiwiand0aWQiOiI2ODgzNmI4NWYzYzVkNTk1OWEyZWRkYjgifQ.q9xN1LA3upxjbOzShytVOL3Irji8h6uvLuZzpaXg8vo'
GLOGIN_API_URL = 'https://api.gologin.com'
PROFILE_NAME = 'Test profile'

"""
curl --location 'https://api.gologin.com/browser/v2' \
--header 'Authorization: Bearer YOUR_API_TOKEN' \
--header 'Content-Type: application/json'
"""


class GoLogin:
    def set_proxy(self, profile_id):
        url = f"{GLOGIN_API_URL}/browser/{profile_id}/proxy"
        headers = {
            "Authorization": f"Bearer {GLOGIN_API_TOKEN}",
            "Content-Type": "application/json"
        }

        data = {
            "mode": "http",
            "host": "82.97.251.114",
            "port": 12571,
            "username": "TuPurg",
            "password": "ac5beVbyP4KU",
            "changeIpUrl": "https://changeip.mobileproxy.space/?proxy_key=7f8edc283f3be5ec89c1e0517d757695"
        }

        result = requests.patch(url, headers=headers, json=data)
        
        print(result)


    def create_profile(self,token):
        url = "https://api.gologin.com/browser/custom"
        header = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        data = {
            "os": "mac",            
        }

        result = requests.post(url, headers=header, json=data)
            
        return result.json()


if __name__ == "__main__":
    gologin = GoLogin()
    profile = gologin.create_profile(GLOGIN_API_TOKEN)
    gologin.set_proxy(profile.get("id"))
