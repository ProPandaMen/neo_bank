from dotenv import load_dotenv

import os

load_dotenv(override=True)

"""
# GoLogin
"""
GOLOGIN_API_TOKEN = os.getenv("GOLOGIN_API_TOKEN")
GOLOGIN_API_URL = os.getenv("GOLOGIN_API_URL")

PROFILE_NAME = os.getenv("PROFILE_NAME")

"""
# Proxy
"""
PROXY_MODE = os.getenv("PROXY_MODE")
PROXY_HOST = os.getenv("PROXY_HOST")
PROXY_PORT = int(os.getenv("PROXY_PORT"))
PROXY_USERNAME = os.getenv("PROXY_USERNAME")
PROXY_PASSWORD = os.getenv("PROXY_PASSWORD")
PROXY_CHANGE_IP_URL = os.getenv("PROXY_CHANGE_IP_URL")
