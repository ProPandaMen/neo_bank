from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By

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