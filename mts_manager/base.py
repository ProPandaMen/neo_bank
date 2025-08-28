from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options

from proxy_manager.main import Proxy
from pathlib import Path

from config import CHROME_PROFILE_DIR

import undetected_chromedriver as uc
import zipfile
import random
import json
import time
import os


def proxy_ext(host, port, username, password, scheme="http"):
    """
    # Если много прокси нужно переписывать
    """
    manifest = {
        "version": "1.0.0",
        "manifest_version": 3,
        "name": "ProxyAuth",
        "permissions": ["proxy", "storage", "webRequest", "webRequestAuthProvider"],
        "host_permissions": ["<all_urls>"],
        "background": {"service_worker": "bg.js"}
    }

    bg = f'''
        chrome.runtime.onInstalled.addListener(()=>{{
            chrome.proxy.settings.set({{value:{{mode:"fixed_servers",rules:{{singleProxy:{{scheme:"{scheme}",host:"{host}",port:{int(port)}}}}}}},scope:"regular"}});
        }});

        chrome.webRequest.onAuthRequired.addListener(
            d=>{{return {{authCredentials:{{username:"{username}",password:"{password}"}}}};}},
            {{urls:["<all_urls>"]}},
            ["blocking"]
        );
    '''.strip()
    
    path = os.path.abspath("proxy_auth_ext.zip")
    with zipfile.ZipFile(path, "w") as z:
        z.writestr("manifest.json", json.dumps(manifest))
        z.writestr("bg.js", bg)

    return path

def get_driver(profile_name: str):
    proxy = Proxy().get_data()
    profile_dir = Path(CHROME_PROFILE_DIR) / str(profile_name)

    opts = Options()
    opts.add_argument("--headless=new")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--disable-blink-features=AutomationControlled")
    opts.add_argument("--window-size=1366,860")
    opts.add_argument("--lang=ru-RU")
    opts.add_experimental_option("prefs", {"intl.accept_languages":"ru-RU,ru,en-US,en"})
    opts.add_argument("--force-webrtc-ip-handling-policy=disable_non_proxied_udp")
    opts.add_argument(f"--user-data-dir={profile_dir}")

    if proxy:
        ext = proxy_ext(proxy["host"], proxy["port"], proxy["username"], proxy["password"])
        opts.add_argument(f"--load-extension={ext}")

    driver = uc.Chrome(options=opts, use_subprocess=False)
    driver.execute_cdp_cmd("Network.setUserAgentOverride", {
        "userAgent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "acceptLanguage": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
        "platform": "Windows"
    })

    driver.execute_cdp_cmd("Network.enable", {})

    return driver


def human_pause(a=0.6, b=1.8):
    time.sleep(random.uniform(a, b))


def wait_click(driver, xpath, timeout=30):
    el = WebDriverWait(driver, timeout).until(
        EC.element_to_be_clickable((By.XPATH, xpath))
    )
    el.click()
    human_pause()

    return el


def wait_visible(driver, xpath, timeout=30):
    el = WebDriverWait(driver, timeout).until(
        EC.visibility_of_element_located((By.XPATH, xpath))
    )
    human_pause()

    return el
