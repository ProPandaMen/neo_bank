from webdriver_manager.chrome import ChromeDriverManager

from selenium.webdriver.chrome.service import Service
from selenium import webdriver

from database.models.task import Task
from gologin_api.main import GoLoginAPI
from gologin import GoLogin


import json, time
import config


def collect_403(driver):
    events = driver.get_log("performance")
    req_map, rows = {}, []
    for e in events:
        try:
            msg = json.loads(e["message"])["message"]
        except: 
            continue
        if msg.get("method") == "Network.requestWillBeSent":
            p = msg["params"]; rid = p.get("requestId")
            if rid: req_map[rid] = p.get("request", {})
    for e in events:
        try:
            msg = json.loads(e["message"])["message"]
        except:
            continue
        if msg.get("method") == "Network.responseReceived":
            p = msg["params"]; resp = p.get("response", {})
            if int(resp.get("status", 0)) == 403:
                rid = p.get("requestId")
                row = {
                    "url": resp.get("url"),
                    "status": 403,
                    "server": (resp.get("headers", {}) or {}).get("Server") or (resp.get("headers", {}) or {}).get("server"),
                    "req": req_map.get(rid, {}),
                }
                try:
                    body = driver.execute_cdp_cmd("Network.getResponseBody", {"requestId": rid})
                    row["body_snippet"] = (body.get("body") or "")[:800]
                except Exception:
                    row["body_snippet"] = ""
                rows.append(row)
    return rows

def start(task_id):
    profile = GoLoginAPI(config.GOLOGIN_API_TOKEN).get_profile_by_id(
        Task.get(id=task_id).gologin_profile_id
    )
    gl = GoLogin({"token": config.GOLOGIN_API_TOKEN, "profile_id": profile.id})
    debugger_address = gl.start()

    chromium_version = gl.get_chromium_version()
    service = Service(ChromeDriverManager(driver_version=chromium_version).install())

    opts = webdriver.ChromeOptions()
    opts.add_experimental_option("debuggerAddress", debugger_address)
    opts.set_capability("goog:loggingPrefs", {"performance": "ALL"})

    driver = None
    try:
        driver = webdriver.Chrome(service=service, options=opts)
        driver.execute_cdp_cmd("Network.enable", {"maxPostDataSize": 0})
        try: driver.get_log("performance")
        except: pass

        time.sleep(2)
        driver.get("https://online.mtsdengi.ru/")
        time.sleep(3)

        rows = collect_403(driver)
        for i, r in enumerate(rows, 1):
            req = r.get("req", {})
            rh = (req.get("headers") or {})
            print(f"[{i}] 403 -> {r['url']}")
            print(f"    Server: {r.get('server')}")
            print(f"    Referer: {rh.get('Referer')}")
            print(f"    Sec-Fetch-Site: {rh.get('Sec-Fetch-Site')}")
            print(f"    UA: {rh.get('User-Agent')}")
            snippet = (r.get("body_snippet") or "").replace("\n", " ")[:180]
            print(f"    Body: {snippet}...")

        with open("403_report.json", "w", encoding="utf-8") as f:
            json.dump(rows, f, ensure_ascii=False, indent=2)
        print("Saved: 403_report.json")

    finally:
        try:
            if driver: driver.quit()
        finally:
            try: gl.stop()
            except: pass

if __name__ == "__main__":
    start(1)
