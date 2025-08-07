from proxy_manager.main import Proxy

import requests
import config


class GoLoginProfile:
    def __init__(self, data):
        self.__dict__.update(data)

    def __str__(self):
        return f"GoLoginProfile(id={self.id}, name={self.name}, os={self.os})"


class GoLoginAPI:
    def __init__(self, token):
        self.token = token

    def get_profiles(self, limit=100, offset=0):
        url = f"{config.GOLOGIN_API_URL}/browser/v2"
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
        params = {"limit": limit, "offset": offset}
        response = requests.get(url, headers=headers, params=params)

        if response.status_code != 200:
            raise Exception(f"Ошибка получения профилей: {response.status_code}, {response.text}")
            
        profiles = response.json().get("profiles", [])

        return [GoLoginProfile(p) for p in profiles]
    

    def get_profile_by_id(self, profile_id):
        url = f"{config.GOLOGIN_API_URL}/browser/{profile_id}"
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            raise Exception(f"Ошибка получения профиля: {response.status_code}, {response.text}")

        profile_data = response.json()
        return GoLoginProfile(profile_data)
    

    def create_profile(self, name, proxy=None):
        url = f"{config.GOLOGIN_API_URL}/browser/custom"
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
        payload = {
            "os": "mac",
            "name": name,
            "proxy": Proxy().get_data()
        }
        response = requests.post(url, headers=headers, json=payload)
        if response.status_code != 201:
            raise Exception(f"Ошибка создания профиля: {response.status_code}, {response.text}")
        
        profile_data = response.json()
        profile = GoLoginProfile(profile_data)
        
        return profile


if __name__ == "__main__":
    gologin = GoLoginAPI(config.GOLOGIN_API_TOKEN)
    profile = gologin.create_profile("test")
