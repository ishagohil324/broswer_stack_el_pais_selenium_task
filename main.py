from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import os
import requests
import re
from collections import Counter
from dotenv import load_dotenv

# -----------------------------
# Load env variables
# -----------------------------
load_dotenv()

RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY")
RAPIDAPI_HOST = os.getenv("RAPIDAPI_HOST")

if not RAPIDAPI_KEY or not RAPIDAPI_HOST:
    raise Exception("RAPIDAPI_KEY or RAPIDAPI_HOST missing in .env file!")

# Create images folder
os.makedirs("images", exist_ok=True)

# -----------------------------
# Translate function
# -----------------------------
def translate_to_english(spanish_title: str) -> str:
    url = f"https://{RAPIDAPI_HOST}/api/v1/translator/json"

    payload = {
        "from": "es",
        "to": "en",
        "json": {
            "title": spanish_title
        }
    }

    headers = {
        "Content-Type": "application/json",
        "x-rapidapi-host": RAPIDAPI_HOST,
        "x-rapidapi-key": RAPIDAPI_KEY
    }

    res = requests.post(url, json=payload, headers=headers, timeout=20)
    data = res.json()

    # Correct extraction based on your API response
    return data["trans"]["title"]

# -----------------------------
# Selenium setup
# -----------------------------
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
wait = WebDriverWait(driver, 15)

driver.get("https://elpais.com/")

# -----------------------------
# Accept cookies
# -----------------------------
try:
    accept_btn = wait.until(
        EC.element_to_be_clickable((By.ID, "didomi-notice-agree-button"))
    )
    accept_btn.click()
    print("Cookies accepted!")
except:
    print("No cookie popup found.")

# -----------------------------
# Go to Opinion section
# -----------------------------
opinion_link = wait.until(
    EC.element_to_be_clickable((By.LINK_TEXT, "Opinión"))
)
opinion_link.click()
print("Opened Opinion section!")

time.sleep(3)

# -----------------------------
# Collect first 5 REAL article links
# Only those ending with .html
# -----------------------------
article_links = driver.find_elements(By.CSS_SELECTOR, "article a")

articles = []
seen = set()

for a in article_links:
    url = a.get_attribute("href")
    title = a.text.strip()

    if not url:
        continue

    # must be Opinion URL
    if "/opinion/" not in url:
        continue

    # must be a real article page
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

print("\nCollected 5 Opinion articles:\n")
for i, art in enumerate(articles, start=1):
    print(f"{i}. {art['title']}")
    print(f"   {art['url']}\n")

# -----------------------------
# Visit each article:
# - print Spanish title
# - print Spanish content
# - download cover image (if exists)
# - translate title
# -----------------------------
translated_titles = []

for i, art in enumerate(articles, start=1):
    print("=" * 90)
    print(f"ARTICLE {i}")
    print("URL:", art["url"])

    driver.get(art["url"])
    time.sleep(3)

    # Spanish Title
    try:
        title_es = wait.until(
            EC.presence_of_element_located((By.TAG_NAME, "h1"))
        ).text.strip()
    except:
        title_es = art["title"]

    # Spanish Content
    paragraphs = driver.find_elements(By.CSS_SELECTOR, "article p")
    content_es = "\n".join([p.text.strip() for p in paragraphs if p.text.strip()])

    print("\nTITLE (Spanish):")
    print(title_es)

    print("\nCONTENT (Spanish):")
    print(content_es[:1200])
    print("\n... (trimmed)\n")

    # Cover image
    image_url = None
    try:
        img = driver.find_element(By.CSS_SELECTOR, "article img")
        image_url = img.get_attribute("src")
    except:
        pass

    if image_url and image_url.startswith("http"):
        try:
            img_data = requests.get(image_url, timeout=10).content
            file_path = f"images/article_{i}.jpg"
            with open(file_path, "wb") as f:
                f.write(img_data)
            print(f"Cover image saved: {file_path}")
        except:
            print("Image found but download failed.")
    else:
        print("No cover image found.")

    # Translate title
    try:
        title_en = translate_to_english(title_es)
    except Exception as e:
        title_en = "TRANSLATION FAILED"
        print("Translation error:", e)

    translated_titles.append(title_en)

    print("\nTITLE (English):")
    print(title_en)

# -----------------------------
# Step 10: Word repetition analysis
# Words repeated more than 2 times across translated titles
# -----------------------------
print("\n" + "=" * 90)
print("ANALYSIS: Repeated words (>2 times) across translated titles\n")

all_text = " ".join(translated_titles).lower()

# remove punctuation
all_text = re.sub(r"[^a-zA-Z\s]", "", all_text)

words = all_text.split()

counts = Counter(words)

repeated = {w: c for w, c in counts.items() if c > 2}

if not repeated:
    print("No words repeated more than 2 times.")
else:
    for w, c in sorted(repeated.items(), key=lambda x: x[1], reverse=True):
        print(f"{w}: {c}")

driver.quit()
