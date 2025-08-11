# test_2.py
from selenium.webdriver.chrome.service import Service
from selenium.webdriver import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait as W
from selenium.webdriver.support import expected_conditions as EC
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from gologin import GoLogin

from gologin_api.main import GoLoginAPI
from database.models.task import Task
import json, time, os, random, re

import config


def wait_ready(d, t=30):
    """Ждём полной загрузки документа."""
    W(d, t).until(lambda x: x.execute_script("return document.readyState") in ("interactive", "complete"))

def enable_net(d):
    """Включаем сетевые события CDP (для сбора 4xx/5xx)."""
    d.execute_cdp_cmd("Network.enable", {"maxPostDataSize": 0})

def clear_perf(d):
    """Очищаем буфер performance-логов."""
    try:
        d.get_log("performance")
    except Exception:
        pass

def collect_40x_50x(d):
    """Собираем 4xx/5xx с заголовками и фрагментом тела."""
    events = d.get_log("performance")
    req_map, rows = {}, []
    for e in events:
        try:
            msg = json.loads(e["message"])["message"]
        except Exception:
            continue
        if msg.get("method") == "Network.requestWillBeSent":
            p = msg["params"]; rid = p.get("requestId")
            if rid:
                req_map[rid] = p.get("request", {})
    for e in events:
        try:
            msg = json.loads(e["message"])["message"]
        except Exception:
            continue
        if msg.get("method") == "Network.responseReceived":
            p = msg["params"]; resp = p.get("response", {})
            st = int(resp.get("status", 0))
            if 400 <= st:
                rid = p.get("requestId"); req = req_map.get(rid, {})
                row = {
                    "url": resp.get("url"),
                    "status": st,
                    "server": (resp.get("headers", {}) or {}).get("Server") or (resp.get("headers", {}) or {}).get("server"),
                    "req_method": req.get("method"),
                    "req_headers": req.get("headers") or {},
                }
                try:
                    body = d.execute_cdp_cmd("Network.getResponseBody", {"requestId": rid})
                    row["body_snippet"] = (body.get("body") or "")[:800]
                except Exception:
                    row["body_snippet"] = ""
                rows.append(row)
    return rows

QR_PATTERNS = [r"^qrator_", r"^gcfids$", r"^mvid$", r"^mcid$"]

def has_qrator_tokens(d):
    """Есть ли характерные антибот-куки на *.mts*."""
    names = [c["name"] for c in d.get_cookies() if ".mts" in (c.get("domain") or "")]
    return any(any(re.match(p, n) for p in QR_PATTERNS) for n in names)

def wait_sw_ready(d, timeout=10):
    """Ждём готовности сервис-воркера (если используется)."""
    try:
        return W(d, timeout).until(
            lambda x: x.execute_script("return (navigator.serviceWorker && navigator.serviceWorker.ready) ? 1 : 0") == 1
        )
    except Exception:
        return False

def warmup_root(d):
    """Лёгкий прогрев: скролл + шевеление мыши."""
    wait_ready(d, 30)
    ActionChains(d).scroll_by_amount(0, random.randint(300, 900)).perform()
    time.sleep(random.uniform(0.3, 0.8))
    try:
        body = d.find_element(By.TAG_NAME, "body")
        ActionChains(d).move_to_element_with_offset(body, 50, 50)\
                       .pause(0.15).move_by_offset(40, 20).pause(0.1).perform()
    except Exception:
        pass

def open_via_click_new_tab(d, url):
    """Открыть ссылку кликом (trusted) в новой вкладке."""
    d.execute_script("""
      const a=document.createElement('a');
      a.href=arguments[0]; a.text='go'; a.target='_blank'; a.rel='opener';
      a.style='position:fixed;left:8px;top:8px;z-index:999999';
      document.body.appendChild(a);
    """, url)
    before = set(d.window_handles)
    link = d.find_element(By.LINK_TEXT, "go")
    ActionChains(d).move_to_element(link).pause(0.12).click().perform()
    end = time.time() + 6
    while time.time() < end:
        after = set(d.window_handles)
        diff = list(after - before)
        if diff:
            d.switch_to.window(diff[-1]); break
        time.sleep(0.1)

def is_403_page(d):
    """Признаки 403 на странице."""
    body = (d.page_source or "").lower()
    u = (d.current_url or "").lower()
    t = (d.title or "").lower()
    return ("forbidden" in body) or ("403" in t) or ("/qrerror/" in u)

def login_form_present(d, t=12):
    """Присутствует ли поле логина."""
    try:
        W(d, t).until(EC.any_of(
            EC.visibility_of_element_located((By.ID, "login")),
            EC.visibility_of_element_located((By.CSS_SELECTOR, "input[name='login']")),
            EC.visibility_of_element_located((By.CSS_SELECTOR, "input[type='tel']"))
        ))
        return True
    except Exception:
        return False

def fp_probe(d):
    """Чек webdriver/язык/платформа."""
    try:
        return d.execute_script("""
          return {
            webdriver: navigator.webdriver,
            lang: navigator.language,
            langs: navigator.languages,
            platform: navigator.platform,
            vendor: navigator.vendor
          };
        """)
    except Exception:
        return {}

def prewarm_login_host(d, attempts=3):
    """Пробуем открыть login.mts.ru кликом; ждём пока уйдёт 401/403, закрываем вкладку."""
    rows = []
    for _ in range(attempts):
        clear_perf(d)
        open_via_click_new_tab(d, "https://login.mts.ru/")
        wait_ready(d, 30)
        time.sleep(1.0)
        rows = collect_40x_50x(d)
        blocked = is_403_page(d) or any("__qrator/validate" in (r.get("url") or "") and r.get("status") in (401,403) for r in rows)
        d.close()
        d.switch_to.window(d.window_handles[0])
        if not blocked:
            return True, rows
        warmup_root(d)
        time.sleep(0.6)
    return False, rows

def apply_min_stealth(d):
    """Мини-стелс: webdriver/languages/plugins/permissions."""
    d.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
        "source": r"""
// webdriver -> undefined
Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
// languages
Object.defineProperty(navigator, 'languages', { get: () => ['ru-RU','ru'] });
Object.defineProperty(navigator, 'language',  { get: () => 'ru-RU' });
// plugins (не ноль)
Object.defineProperty(navigator, 'plugins',   { get: () => [ {name:'Chrome PDF Plugin'} ] });
// permissions
const origQuery = window.navigator.permissions && window.navigator.permissions.query;
if (origQuery) {
  window.navigator.permissions.query = (params) => {
    if (params && params.name === 'notifications') {
      return Promise.resolve({ state: Notification.permission });
    }
    return origQuery(params);
  };
}
        """
    })

def start(task_id):
    task = Task.get(id=task_id)
    gl = None
    driver = None
    try:
        profile = GoLoginAPI(config.GOLOGIN_API_TOKEN).get_profile_by_id(task.gologin_profile_id)
        gl = GoLogin({"token": config.GOLOGIN_API_TOKEN, "profile_id": profile.id})
        dbg = gl.start()

        service = Service(ChromeDriverManager(driver_version=gl.get_chromium_version()).install())

        opts = webdriver.ChromeOptions()
        opts.add_experimental_option("debuggerAddress", dbg)
        opts.set_capability("goog:loggingPrefs", {"performance": "ALL"})

        driver = webdriver.Chrome(service=service, options=opts)

        apply_min_stealth(driver)
        enable_net(driver)
        clear_perf(driver)

        # 1) Корневой домен → прогрев
        driver.get("https://mtsdengi.ru/")
        warmup_root(driver)
        sw = wait_sw_ready(driver, 8)
        tokens_before = has_qrator_tokens(driver)
        print(f"[warmup] sw_ready={sw}, tokens_before={tokens_before}, fp={fp_probe(driver)}")

        # 2) Пилот: прогреть login.mts.ru кликом
        ok_prewarm, rows_login = prewarm_login_host(driver, attempts=3)
        print(f"[login-prewarm] ok={ok_prewarm}")

        # 3) Теперь online.mtsdengi.ru кликом (новая вкладка)
        clear_perf(driver)
        open_via_click_new_tab(driver, "https://online.mtsdengi.ru/")
        wait_ready(driver, 30)
        time.sleep(1.0)

        rows_final = collect_40x_50x(driver)
        blocked_qrator = any("__qrator/validate" in (r.get("url") or "") and r.get("status") in (401,403) for r in rows_final)
        ok = (not is_403_page(driver)) and (not blocked_qrator) and login_form_present(driver, t=8)
        status = "OK" if ok else "BLOCKED"

        report = {
            "sw_ready": sw,
            "tokens_before": tokens_before,
            "login_prewarm_ok": ok_prewarm,
            "final_url": driver.current_url,
            "status": status,
            "login_prewarm_40x": rows_login,
            "final_40x": rows_final
        }
        path = os.path.abspath("test_2_report.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)

        print(f"[result] status={status} url={driver.current_url}")
        print(f"[report] saved to {path}")

    finally:
        try:
            if driver:
                driver.quit()
        finally:
            try:
                if gl:
                    gl.stop()
            except Exception:
                pass


if __name__ == "__main__":
    start(2)
