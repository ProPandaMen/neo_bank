from seleniumwire.undetected_chromedriver import Chrome, ChromeOptions
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By

from proxy_manager.main import Proxy

import random
import time


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


def get_driver():
    proxy = Proxy().get_data()

    USER = proxy.get("username")
    PASS = proxy.get("password")
    HOST = proxy.get("host")
    PORT = proxy.get("port")

    sw_options = {
        "proxy": {
            "http":  f"http://{USER}:{PASS}@{HOST}:{PORT}",
            "https": f"http://{USER}:{PASS}@{HOST}:{PORT}",
            "no_proxy": "localhost,127.0.0.1"
        },
        "verify_ssl": False
    }


    opts = ChromeOptions()
    opts.add_argument("--headless=new")
    opts.add_argument("--ignore-certificate-errors")
    opts.add_argument("--allow-insecure-localhost")
    opts.add_argument("--ignore-ssl-errors=yes")
    opts.add_argument("--test-type")
    opts.set_capability("acceptInsecureCerts", True)

    driver = Chrome(
        options=opts,
        seleniumwire_options=sw_options,
        # version_main=112,
    )

    return driver
