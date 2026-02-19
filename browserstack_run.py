import os
import time
import threading
import requests
from dotenv import load_dotenv

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


# ----------------------------
# Load env
# ----------------------------
load_dotenv()

BROWSERSTACK_USERNAME = os.getenv("BROWSERSTACK_USERNAME")
BROWSERSTACK_ACCESS_KEY = os.getenv("BROWSERSTACK_ACCESS_KEY")

RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY")
RAPIDAPI_HOST = os.getenv("RAPIDAPI_HOST")

if not BROWSERSTACK_USERNAME or not BROWSERSTACK_ACCESS_KEY:
    raise Exception("Missing BrowserStack creds in .env")

if not RAPIDAPI_KEY or not RAPIDAPI_HOST:
    raise Exception("Missing RapidAPI creds in .env")

BROWSERSTACK_URL = f"https://{BROWSERSTACK_USERNAME}:{BROWSERSTACK_ACCESS_KEY}@hub-cloud.browserstack.com/wd/hub"


# ----------------------------
# Translation
# ----------------------------
def translate_to_english(spanish_title: str) -> str:
    url = f"https://{RAPIDAPI_HOST}/api/v1/translator/json"

    payload = {
        "from": "es",
        "to": "en",
        "json": {"title": spanish_title}
    }

    headers = {
        "Content-Type": "application/json",
        "x-rapidapi-host": RAPIDAPI_HOST,
        "x-rapidapi-key": RAPIDAPI_KEY
    }

    res = requests.post(url, json=payload, headers=headers, timeout=20)
    data = res.json()
    return data["trans"]["title"]


# ----------------------------
# One test run
# ----------------------------
def run_test(capabilities, thread_name):
    print(f"\n--- STARTING: {thread_name} ---")

    options = webdriver.ChromeOptions()

    # W3C capabilities
    options.set_capability("browserName", capabilities["browserName"])
    options.set_capability("browserVersion", capabilities.get("browserVersion", "latest"))
    options.set_capability("bstack:options", capabilities["bstack:options"])

    driver = webdriver.Remote(
        command_executor=BROWSERSTACK_URL,
        options=options
    )

    wait = WebDriverWait(driver, 25)

    try:
        # Open homepage first (cookie appears here)
        driver.get("https://elpais.com/")

        # Accept cookies (if shown)
        try:
            accept_btn = wait.until(
                EC.element_to_be_clickable((By.ID, "didomi-notice-agree-button"))
            )
            accept_btn.click()
        except:
            pass

        # IMPORTANT: Go directly to Opinion page (NO clicking)
        driver.get("https://elpais.com/opinion/")
        time.sleep(4)

        # Collect first 5 REAL articles
        article_links = driver.find_elements(By.CSS_SELECTOR, "article a")

        articles = []
        seen = set()

        for a in article_links:
            url = a.get_attribute("href")
            title = a.text.strip()

            if not url:
                continue
            if "/opinion/" not in url:
                continue
            if not url.endswith(".html"):
                continue
            if url in seen:
                continue
            if not title:
                continue

            seen.add(url)
            articles.append({"title": title, "url": url})

            if len(articles) == 5:
                break

        print(f"[{thread_name}] Collected {len(articles)} articles")

        # Visit each + translate title
        for i, art in enumerate(articles, start=1):
            driver.get(art["url"])
            time.sleep(3)

            # Spanish title
            try:
                title_es = wait.until(
                    EC.presence_of_element_located((By.TAG_NAME, "h1"))
                ).text.strip()
            except:
                title_es = art["title"]

            # Translate
            try:
                title_en = translate_to_english(title_es)
            except Exception as e:
                title_en = "TRANSLATION FAILED"
                print(f"[{thread_name}] Translation error:", e)

            print(f"[{thread_name}] {i}. ES: {title_es}")
            print(f"[{thread_name}]    EN: {title_en}")

        print(f"--- FINISHED: {thread_name} ---")

    finally:
        driver.quit()


# ----------------------------
# 5 parallel configs
# ----------------------------
CAPS = [
    {
        "browserName": "Chrome",
        "browserVersion": "latest",
        "bstack:options": {
            "os": "Windows",
            "osVersion": "11",
            "sessionName": "Chrome Win11"
        }
    },
    {
        "browserName": "Firefox",
        "browserVersion": "latest",
        "bstack:options": {
            "os": "Windows",
            "osVersion": "10",
            "sessionName": "Firefox Win10"
        }
    },
    {
        "browserName": "Edge",
        "browserVersion": "latest",
        "bstack:options": {
            "os": "Windows",
            "osVersion": "11",
            "sessionName": "Edge Win11"
        }
    },
    {
        "browserName": "Safari",
        "browserVersion": "latest",
        "bstack:options": {
            "os": "OS X",
            "osVersion": "Ventura",
            "sessionName": "Safari macOS"
        }
    },
    {
        "browserName": "Safari",
        "browserVersion": "latest",
        "bstack:options": {
            "deviceName": "iPhone 14",
            "realMobile": "true",
            "osVersion": "16",
            "sessionName": "iPhone Safari"
        }
    }
]


threads = []

for i, cap in enumerate(CAPS, start=1):
    t = threading.Thread(target=run_test, args=(cap, f"Thread-{i}"))
    threads.append(t)

for t in threads:
    t.start()

for t in threads:
    t.join()

print("\nALL 5 PARALLEL TESTS COMPLETED!")
