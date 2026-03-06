import requests
import json
import os
import time

# --- CONFIGURATION ---
# We use environment variables so we don't hardcode secrets in GitHub
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
STATE_FILE = "seen_jobs.json"

# This is your central configuration hub. Add companies here.
TARGETS = [
    {"name": "Stripe", "ats": "greenhouse", "id": "stripe", "keywords": ["software engineer", "sde"]},
    {"name": "Figma", "ats": "lever", "id": "figma", "keywords": ["software engineer", "sde"]},
    {"name": "Amazon", "ats": "amazon", "country": "IND", "keywords": ["software engineer", "sde"]}
]

# --- NOTIFICATION ENGINE ---
def send_telegram_alert(company, title, url, location=""):
    """Fires a push notification to your phone via Telegram."""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print(f"🚨 [LOCAL ALERT] {company}: {title} - {url}")
        return

    message = f"🚀 **New {company} Job!**\n**Role:** {title}\n"
    if location:
        message += f"**Location:** {location}\n"
    message += f"**Link:** {url}"

    api_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "Markdown"}
    
    try:
        requests.post(api_url, json=payload)
    except Exception as e:
        print(f"Failed to send Telegram alert: {e}")

# --- SCRAPER MODULES ---
def scrape_greenhouse(target):
    jobs_found = []
    url = f"https://boards-api.greenhouse.io/v1/boards/{target['id']}/jobs"
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            for job in response.json().get("jobs", []):
                jobs_found.append({"id": str(job["id"]), "title": job["title"], "url": job["absolute_url"]})
    except Exception as e:
        print(f"Error scraping Greenhouse for {target['name']}: {e}")
    return jobs_found

def scrape_lever(target):
    jobs_found = []
    url = f"https://api.lever.co/v0/postings/{target['id']}"
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            for job in response.json():
                jobs_found.append({"id": str(job["id"]), "title": job["text"], "url": job["hostedUrl"]})
    except Exception as e:
        print(f"Error scraping Lever for {target['name']}: {e}")
    return jobs_found

def scrape_amazon(target):
    jobs_found = []
    url = "https://www.amazon.jobs/en/search.json"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    }
    # For Amazon, we map the first keyword as the base query
    base_query = target["keywords"][0] if target["keywords"] else ""
    params = {"base_query": base_query, "country": target.get("country", "IND"), "result_limit": 10, "sort": "recent"}
    
    try:
        response = requests.get(url, params=params, headers=headers, timeout=10)
        if response.status_code == 200:
            for job in response.json().get("jobs", []):
                jobs_found.append({
                    "id": str(job.get("id_icims", job.get("id"))),
                    "title": job.get("title", "Unknown"),
                    "location": job.get("normalized_location", ""),
                    "url": "https://www.amazon.jobs" + job.get("job_path", "")
                })
    except Exception as e:
         print(f"Error scraping Amazon: {e}")
    return jobs_found

# --- CORE LOGIC ---
def is_relevant(title, keywords):
    if not keywords: return True
    return any(k.lower() in title.lower() for k in keywords)

def main():
    print("Initiating scan...")
    # Load state
    state = {}
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r") as f:
            state = json.load(f)

    state_changed = False

    # The Dispatcher Dictionary
    scrapers = {
        "greenhouse": scrape_greenhouse,
        "lever": scrape_lever,
        "amazon": scrape_amazon
    }

    for target in TARGETS:
        company_name = target["name"]
        ats_type = target["ats"]
        
        if ats_type not in scrapers:
            print(f"Unknown ATS '{ats_type}' for {company_name}")
            continue

        # Route to the correct scraper function
        current_jobs = scrapers[ats_type](target)
        
        # Initialize memory for this company if it doesn't exist
        if company_name not in state:
            state[company_name] = []

        for job in current_jobs:
            if job["id"] not in state[company_name]:
                if is_relevant(job["title"], target.get("keywords", [])):
                    send_telegram_alert(company_name, job["title"], job["url"], job.get("location", ""))
                
                state[company_name].append(job["id"])
                state_changed = True
        
        time.sleep(1) # Be polite to APIs

    # Save state if new jobs were found
    if state_changed:
        with open(STATE_FILE, "w") as f:
            json.dump(state, f, indent=4)
        print("Scan complete. State updated.")
    else:
        print("Scan complete. No new matches.")

if __name__ == "__main__":
    main()