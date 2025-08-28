from seleniumwire.undetected_chromedriver import Chrome
from pathlib import Path

from config import SCREENSHOT_DIR


def save_task_screenshot(driver: Chrome, task_id: int, filename: str):
    base_dir = Path(SCREENSHOT_DIR) / str(task_id)
    base_dir.mkdir(parents=True, exist_ok=True)
    
    driver.save_screenshot(str(base_dir / filename))
