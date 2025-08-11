from seleniumwire.undetected_chromedriver import Chrome, ChromeOptions
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By

import time


USER = "Yc1Nac"
PASS = "naV2PUr4ag1E"
HOST = "82.97.251.114"
PORT = 12148

sw_options = {
    "proxy": {
        "http":  f"http://{USER}:{PASS}@{HOST}:{PORT}",
        "https": f"http://{USER}:{PASS}@{HOST}:{PORT}",
        "no_proxy": "localhost,127.0.0.1"
    },
    "verify_ssl": False
}

def wait_ready(d):
    WebDriverWait(d, 15).until(lambda x: x.execute_script("return document.readyState") == "complete")


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
    version_main=112,
)

driver.get("https://online.mtsdengi.ru/")
wait_ready(driver)

time.sleep(30)

driver.save_screenshot("viewport.png")
print(driver.page_source)
driver.quit()   
