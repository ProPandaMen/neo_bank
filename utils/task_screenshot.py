from seleniumwire.undetected_chromedriver import Chrome
from pathlib import Path


def save_task_screenshot(driver: Chrome, task_id: int, filename: str):
    base_dir = Path("/app/storage/screenshot") / str(task_id)
    base_dir.mkdir(parents=True, exist_ok=True)
    
    driver.save_screenshot(str(base_dir / filename))
