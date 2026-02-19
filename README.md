# El País Opinion Automation (Selenium + BrowserStack)

## Overview
This project automates the El País website using Selenium to:
- Open El País in Spanish
- Go to the Opinion section
- Fetch the first 5 opinion articles
- Print each article title + content in Spanish
- Download the cover image (if available)
- Translate article titles from Spanish to English using RapidAPI
- Analyze translated titles and print words repeated more than 2 times
- Execute the workflow on BrowserStack across 5 parallel threads (desktop + mobile)

---

## Tech Stack
- Python
- Selenium
- Requests
- RapidAPI (Google Translate)
- BrowserStack

---

## Setup

### 1) Create and activate virtual environment
```bash
python -m venv venv
venv\Scripts\activate
