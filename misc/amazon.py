import requests
import json
import os

# --- CONFIGURATION ---
WEBHOOK_URL = "YOUR_DISCORD_OR_SLACK_WEBHOOK_URL_HERE"
STATE_FILE = "amazon_seen_jobs.json"

# --- CORE LOGIC ---
def load_seen_jobs():
    """Loads the database of jobs we've already notified you about."""
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r") as f:
            return json.load(f)
    return {}

def save_seen_jobs(seen_jobs):
    """Saves the database to disk."""
    with open(STATE_FILE, "w") as f:
        json.dump(seen_jobs, f, indent=4)

def send_alert(job_title, job_url, location):
    """Sends a push notification via Webhook."""
    print(f"🚨 NEW AMAZON JOB: {job_title} ({location})")
    
    payload = {
        "content": f"🚀 **New Amazon Job Found!**\n**Role:** {job_title}\n**Location:** {location}\n**Link:** {job_url}"
    }
    
    if WEBHOOK_URL != "YOUR_DISCORD_OR_SLACK_WEBHOOK_URL_HERE":
        requests.post(WEBHOOK_URL, json=payload)
    else:
        print("Webhook not configured, skipping push notification.")

def check_amazon_jobs(base_query, country_code):
    """Hits the hidden JSON API powering the Amazon Jobs search bar."""
    url = "https://www.amazon.jobs/en/search.json"
    
    params = {
        "base_query": base_query,
        "country": country_code,
        "result_limit": 10,
        "sort": "recent" # Crucial: ensures we get the newest listings first
    }
    
    # Required to prevent AWS WAF from blocking the request as a bot
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "en-US,en;q=0.9",
    }
    
    try:
        response = requests.get(url, params=params, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        jobs = []
        for job in data.get("jobs", []):
            jobs.append({
                "id": str(job.get("id_icims", job.get("id"))),
                "title": job.get("title", "Unknown Title"),
                "location": job.get("normalized_location", "India"),
                "url": "https://www.amazon.jobs" + job.get("job_path", "")
            })
        return jobs
    except Exception as e:
        print(f"Error fetching Amazon jobs: {e}")
        return []

def main():
    print("Starting Amazon job scan...")
    seen_jobs = load_seen_jobs()
    new_jobs_found = False

    # The key we'll use in our state file to track this specific query
    query_key = "Amazon_SWE_IND"
    amazon_memory = seen_jobs.get(query_key, [])
    new_amazon_memory = amazon_memory.copy()

    # Query for "software engineer" in "IND" (India)
    current_jobs = check_amazon_jobs(base_query="software engineer", country_code="IND")

    for job in current_jobs:
        if job["id"] not in amazon_memory:
            # We found a new job!
            send_alert(job["title"], job["url"], job["location"])
            
            # Add to memory so we don't alert again
            new_amazon_memory.append(job["id"])
            new_jobs_found = True

    seen_jobs[query_key] = new_amazon_memory
        
    if new_jobs_found:
        save_seen_jobs(seen_jobs)
        print("Scan complete. State updated.")
    else:
        print("Scan complete. No new relevant jobs.")

if __name__ == "__main__":
    main()