import requests
import json
import os
import time
from datetime import datetime, timezone, timedelta
import re
from urllib.parse import urlparse

# --- CONFIGURATION ---
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
STATE_FILE = "seen_jobs.json"

SWE_KEYWORDS = [
    "software engineer",
    "sde",
    "developer",
    "programmer",
    "backend",
    "frontend",
    "fullstack",
    "full stack",
    "member of technical staff",
    "mts",
    "technology analyst",
    "tech analyst",
    "technical associate",
    "associate",
    "sde 2",
    "sde2",
    "software engineer ii",
    "software engineer 2",
    "sde ii",
    "mid",
    "c++",
    "node",
    "react",
    "javascript",
    "typescript",
    "python",
    "software",
    "software developer",
    "swe",
    "software development engineer",
    "technical",
]

EXCLUDED_KEYWORDS = [
    "staff", 
    "director", 
    "principal", 
    "manager", 
    "vp", 
    "head", 
    "president",
    "lead",
    "iii",
    "talent",
    "Recruiter"
]

def is_india(location_str):
    """Ensures the job is located in an Indian tech hub or is generically Remote."""
    if not location_str:
        return False
    
    loc = location_str.lower().strip()
    
    # 1. Check for explicitly Indian locations and Indian Remote variations (Substring Match)
    indian_hubs = [
        "india",
        "ind",
        "blr",
        "bengaluru",
        "bangalore",
        "delhi",
        "ncr",
        "new delhi",
        "gurgaon",
        "gurugram",
        "noida",
        "mumbai",
        "bombay",
        "hyderabad",
        "pune",
        "chennai",
        "madras",
        "kolkata",
        "ahmedabad",
        "del",
        "mum",
        "hyd",
        "chen",
        "kolk",
        "ahmd",
        "remote - in",
        "remote-in",
        "remote (india)",
        "remote (in)",
        "remote india",
    ]
    
    if any(hub in loc for hub in indian_hubs):
        return True
        
    # 2. Check for purely generic remote (Exact matches)
    # By removing "remote" from the substring list above and putting it here,
    # we prevent "Remote - US" or "Remote, Canada" from falsely triggering.
    pure_remote_strings = [
        "remote",
        "remote/unspecified",
        "remote / unspecified",
        "fully remote",
        "remote - global",
        "remote (global)",
        "anywhere",
        "wfh",
    ]
    
    if loc in pure_remote_strings:
        return True
        
    return False

TARGETS = [
    # Custom API
    {"name": "Amazon", "ats": "amazon", "country": "IND", "keywords": SWE_KEYWORDS},
    
    # GREENHOUSE (VERIFIED LIVE)
    {"name": "Stripe", "ats": "greenhouse", "id": "stripe", "keywords": SWE_KEYWORDS},
    {"name": "Groww", "ats": "greenhouse", "id": "groww", "keywords": SWE_KEYWORDS},
    {"name": "PhonePe", "ats": "greenhouse", "id": "phonepe", "keywords": SWE_KEYWORDS},
    {"name": "Razorpay", "ats": "greenhouse", "id": "razorpaysoftwareprivatelimited", "keywords": SWE_KEYWORDS},
    {"name": "Slice", "ats": "greenhouse", "id": "slice", "keywords": SWE_KEYWORDS},
    {"name": "Brex", "ats": "greenhouse", "id": "brex", "keywords": SWE_KEYWORDS},
    {"name": "Airbnb", "ats": "greenhouse", "id": "airbnb", "keywords": SWE_KEYWORDS},
    {"name": "Tower Research Capital", "ats": "greenhouse", "id": "towerresearchcapital", "keywords": SWE_KEYWORDS},
    {"name": "AlphaGrep", "ats": "greenhouse", "id": "alphagrepsecurities", "keywords": SWE_KEYWORDS},
    {"name": "Databricks", "ats": "greenhouse", "id": "databricks", "keywords": SWE_KEYWORDS},
    {"name": "Rubrik", "ats": "greenhouse", "id": "rubrik", "keywords": SWE_KEYWORDS},
    {"name": "Cloudflare", "ats": "greenhouse", "id": "cloudflare", "keywords": SWE_KEYWORDS},
    {"name": "Cleartax", "ats": "greenhouse", "id": "clear", "keywords": SWE_KEYWORDS},
    {"name": "Agoda", "ats": "greenhouse", "id": "agoda", "keywords": SWE_KEYWORDS},
    {"name": "DoorDash", "ats": "greenhouse", "id": "doordashusa", "keywords": SWE_KEYWORDS},
    {"name": "Twilio", "ats": "greenhouse", "id": "twilio", "keywords": SWE_KEYWORDS},
    {"name": "Dropbox", "ats": "greenhouse", "id": "dropbox", "keywords": SWE_KEYWORDS},
    {"name": "Anthropic", "ats": "greenhouse", "id": "anthropic", "keywords": SWE_KEYWORDS},
    {"name": "Figma", "ats": "greenhouse", "id": "figma", "keywords": SWE_KEYWORDS},
    {"name": "Coinbase", "ats": "greenhouse", "id": "coinbase", "keywords": SWE_KEYWORDS},
    {"name": "Discord", "ats": "greenhouse", "id": "discord", "keywords": SWE_KEYWORDS},
    {"name": "Reddit", "ats": "greenhouse", "id": "reddit", "keywords": SWE_KEYWORDS},
    {"name": "Affirm", "ats": "greenhouse", "id": "affirm", "keywords": SWE_KEYWORDS},
    {"name": "Robinhood", "ats": "greenhouse", "id": "robinhood", "keywords": SWE_KEYWORDS},
    {"name": "Vercel", "ats": "greenhouse", "id": "vercel", "keywords": SWE_KEYWORDS},
    {"name": "MongoDB", "ats": "greenhouse", "id": "mongodb", "keywords": SWE_KEYWORDS},
    {"name": "Datadog", "ats": "greenhouse", "id": "datadog", "keywords": SWE_KEYWORDS},
    {"name": "Elastic", "ats": "greenhouse", "id": "elastic", "keywords": SWE_KEYWORDS},
    {"name": "Asana", "ats": "greenhouse", "id": "asana", "keywords": SWE_KEYWORDS},
    {"name": "Coursera", "ats": "greenhouse", "id": "coursera", "keywords": SWE_KEYWORDS},
    {"name": "Udemy", "ats": "greenhouse", "id": "udemy", "keywords": SWE_KEYWORDS},
    {"name": "Netlify", "ats": "greenhouse", "id": "netlify", "keywords": SWE_KEYWORDS},
    {"name": "Airtable", "ats": "greenhouse", "id": "airtable", "keywords": SWE_KEYWORDS},
    {"name": "Scale AI", "ats": "greenhouse", "id": "scaleai", "keywords": SWE_KEYWORDS},
    {"name": "Netskope", "ats": "greenhouse", "id": "netskope", "keywords": SWE_KEYWORDS},
    {"name": "Samsara", "ats": "greenhouse", "id": "samsara", "keywords": SWE_KEYWORDS},
    {"name": "Duolingo", "ats": "greenhouse", "id": "duolingo", "keywords": SWE_KEYWORDS},
    {"name": "Pinterest", "ats": "greenhouse", "id": "pinterest", "keywords": SWE_KEYWORDS},
    {"name": "Twitch", "ats": "greenhouse", "id": "twitch", "keywords": SWE_KEYWORDS},
    {"name": "Optiver", "ats": "greenhouse", "id": "optiver", "keywords": SWE_KEYWORDS},
    {"name": "Jump Trading", "ats": "greenhouse", "id": "jumptrading", "keywords": SWE_KEYWORDS},
    {"name": "Postman", "ats": "greenhouse", "id": "postman", "keywords": SWE_KEYWORDS},
    {"name": "Gong", "ats": "greenhouse", "id": "gongio", "keywords": SWE_KEYWORDS},
    {"name": "Apollo GraphQL", "ats": "greenhouse", "id": "apolloio", "keywords": SWE_KEYWORDS},
    {"name": "Glean", "ats": "greenhouse", "id": "glean", "keywords": SWE_KEYWORDS},

    # ASHBY (NEWLY DISCOVERED / REMAPPED)
    {"name": "OpenAI", "ats": "ashby", "id": "openai", "keywords": SWE_KEYWORDS},
    {"name": "Notion", "ats": "ashby", "id": "notion", "keywords": SWE_KEYWORDS},
    {"name": "Plaid", "ats": "ashby", "id": "plaid", "keywords": SWE_KEYWORDS},
    {"name": "Ramp", "ats": "ashby", "id": "ramp", "keywords": SWE_KEYWORDS},
    {"name": "Cohere", "ats": "ashby", "id": "cohere", "keywords": SWE_KEYWORDS},
    {"name": "Supabase", "ats": "ashby", "id": "supabase", "keywords": SWE_KEYWORDS},
    {"name": "PostHog", "ats": "ashby", "id": "posthog", "keywords": SWE_KEYWORDS},
    {"name": "Miro", "ats": "ashby", "id": "miro", "keywords": SWE_KEYWORDS},
    {"name": "Confluent", "ats": "ashby", "id": "confluent", "keywords": SWE_KEYWORDS},
    {"name": "Checkout.com", "ats": "ashby", "id": "checkout.com", "keywords": SWE_KEYWORDS},
    {"name": "Deliveroo", "ats": "ashby", "id": "deliveroo", "keywords": SWE_KEYWORDS},

    # LEVER (VERIFIED LIVE)
    {"name": "Palantir", "ats": "lever", "id": "palantir", "keywords": SWE_KEYWORDS},
    {"name": "Paytm", "ats": "lever", "id": "paytm", "keywords": SWE_KEYWORDS},
    {"name": "Meesho", "ats": "lever", "id": "meesho", "keywords": SWE_KEYWORDS},
    {"name": "Dream11", "ats": "lever", "id": "dreamsports", "keywords": SWE_KEYWORDS},
    {"name": "Fi Money", "ats": "lever", "id": "fi", "keywords": SWE_KEYWORDS},
    {"name": "Zeta", "ats": "lever", "id": "zeta", "keywords": SWE_KEYWORDS},
    {"name": "CRED", "ats": "lever", "id": "cred", "keywords": SWE_KEYWORDS},
    {"name": "MindTickle", "ats": "lever", "id": "mindtickle", "keywords": SWE_KEYWORDS},

    # WORKDAY (VERIFIED LIVE)
    {"name": "Mastercard", "ats": "workday", "url": "https://mastercard.wd1.myworkdayjobs.com/CorporateCareers", "keywords": SWE_KEYWORDS},
    {"name": "Salesforce", "ats": "workday", "url": "https://salesforce.wd12.myworkdayjobs.com/External_Career_Site", "keywords": SWE_KEYWORDS},
    {"name": "American Express", "ats": "workday", "url": "https://travelhrportal.wd1.myworkdayjobs.com/Jobs", "keywords": SWE_KEYWORDS},
    {"name": "Bank of America", "ats": "workday", "url": "https://ghr.wd1.myworkdayjobs.com/lateral-apac", "keywords": SWE_KEYWORDS},
    {"name": "BlackRock", "ats": "workday", "url": "https://blackrock.wd1.myworkdayjobs.com/BlackRock_Professional", "keywords": SWE_KEYWORDS},
    {"name": "Blackstone", "ats": "workday", "url": "https://blackstone.wd1.myworkdayjobs.com/Blackstone_Careers", "keywords": SWE_KEYWORDS},
    {"name": "Capital Group", "ats": "workday", "url": "https://capgroup.wd1.myworkdayjobs.com/capitalgroupcareers", "keywords": SWE_KEYWORDS},
    {"name": "CME Group", "ats": "workday", "url": "https://cmegroup.wd1.myworkdayjobs.com/cme_careers", "keywords": SWE_KEYWORDS},
    {"name": "FactSet", "ats": "workday", "url": "https://factset.wd108.myworkdayjobs.com/FactSetCareers", "keywords": SWE_KEYWORDS},
    {"name": "Fiserv", "ats": "workday", "url": "https://fiserv.wd5.myworkdayjobs.com/EXT", "keywords": SWE_KEYWORDS},
    {"name": "Franklin Templeton", "ats": "workday", "url": "https://franklintempleton.wd5.myworkdayjobs.com/Primary-External-1", "keywords": SWE_KEYWORDS},
    {"name": "Invesco", "ats": "workday", "url": "https://invesco.wd1.myworkdayjobs.com/IVZ", "keywords": SWE_KEYWORDS},
    {"name": "PayPal", "ats": "workday", "url": "https://paypal.wd1.myworkdayjobs.com/jobs", "keywords": SWE_KEYWORDS},
    {"name": "Adobe", "ats": "workday", "url": "https://adobe.wd5.myworkdayjobs.com/external_experienced", "keywords": SWE_KEYWORDS},
    {"name": "Workday", "ats": "workday", "url": "https://workday.wd5.myworkdayjobs.com/Workday", "keywords": SWE_KEYWORDS},
    {"name": "CrowdStrike", "ats": "workday", "url": "https://crowdstrike.wd5.myworkdayjobs.com/crowdstrikecareers", "keywords": SWE_KEYWORDS},
    {"name": "NVIDIA", "ats": "workday", "url": "https://nvidia.wd5.myworkdayjobs.com/NVIDIAExternalCareerSite", "keywords": SWE_KEYWORDS},
    {"name": "Cisco", "ats": "workday", "url": "https://cisco.wd5.myworkdayjobs.com/Cisco_Careers", "keywords": SWE_KEYWORDS},
    {"name": "Intel", "ats": "workday", "url": "https://intel.wd1.myworkdayjobs.com/External", "keywords": SWE_KEYWORDS},
    {"name": "Target", "ats": "workday", "url": "https://target.wd5.myworkdayjobs.com/targetcareers", "keywords": SWE_KEYWORDS},
    {"name": "Zoom", "ats": "workday", "url": "https://zoom.wd5.myworkdayjobs.com/Zoom", "keywords": SWE_KEYWORDS},
    {"name": "Expedia", "ats": "workday", "url": "https://expedia.wd108.myworkdayjobs.com/search", "keywords": SWE_KEYWORDS},
    {"name": "Sprinklr", "ats": "workday", "url": "https://sprinklr.wd1.myworkdayjobs.com/careers", "keywords": SWE_KEYWORDS},
    {"name": "Zendesk", "ats": "workday", "url": "https://zendesk.wd1.myworkdayjobs.com/zendesk", "keywords": SWE_KEYWORDS},
    {"name": "Visa", "ats": "workday", "url": "https://visa.wd5.myworkdayjobs.com/Visa", "keywords": SWE_KEYWORDS},
    {"name": "Autodesk", "ats": "workday", "url": "https://autodesk.wd1.myworkdayjobs.com/Ext", "keywords": SWE_KEYWORDS},
    {"name": "Disney", "ats": "workday", "url": "https://disney.wd5.myworkdayjobs.com/disneycareer", "keywords": SWE_KEYWORDS},
    {"name": "Warner Bros. Discovery", "ats": "workday", "url": "https://warnerbros.wd5.myworkdayjobs.com/global", "keywords": SWE_KEYWORDS},
    {"name": "Kyndryl", "ats": "workday", "url": "https://kyndryl.wd5.myworkdayjobs.com/KyndrylProfessionalCareers", "keywords": SWE_KEYWORDS},
    {"name": "BrowserStack", "ats": "workday", "url": "https://browserstack.wd3.myworkdayjobs.com/External", "keywords": SWE_KEYWORDS},

    # PHASE 3: Unsupported / Deprecated Platforms (Script ignores these)
    {"name": "Walmart Global Tech", "ats": "deprecated", "url": "https://walmart.wd5.myworkdayjobs.com/WalmartExternal", "keywords": SWE_KEYWORDS},
    {"name": "Citi Group", "ats": "phenom", "url": "https://jobs.citi.com/search-jobs", "keywords": SWE_KEYWORDS},
    {"name": "Fidelity Investments", "ats": "phenom", "url": "https://jobs.fidelity.com/in/jobs/", "keywords": SWE_KEYWORDS},
    {"name": "FIS", "ats": "phenom", "url": "https://careers.fisglobal.com/us/en", "keywords": SWE_KEYWORDS},
    {"name": "Intuit", "ats": "phenom", "url": "https://jobs.intuit.com/search-jobs", "keywords": SWE_KEYWORDS},
    {"name": "Macquarie Group", "ats": "taleo", "url": "https://www.macquarie.com/in/en/careers.html", "keywords": SWE_KEYWORDS},
    {"name": "Moody Analytics", "ats": "phenom", "url": "https://careers.moodys.com/jobs", "keywords": SWE_KEYWORDS},
    {"name": "S&P Global", "ats": "phenom", "url": "https://careers.spglobal.com/jobs", "keywords": SWE_KEYWORDS},
    {"name": "State Street", "ats": "custom", "url": "https://careers.statestreet.com/global/en", "keywords": SWE_KEYWORDS},
    {"name": "Wells Fargo", "ats": "phenom", "url": "https://www.wellsfargojobs.com/en/jobs/", "keywords": SWE_KEYWORDS},
    {"name": "Snowflake", "ats": "phenom", "url": "https://careers.snowflake.com/us/en/search-results", "keywords": SWE_KEYWORDS},
    {"name": "ServiceNow", "ats": "smartrecruiters", "url": "https://careers.servicenow.com/careers", "keywords": SWE_KEYWORDS},
    {"name": "Palo Alto Networks", "ats": "phenom", "url": "https://jobs.paloaltonetworks.com/en/", "keywords": SWE_KEYWORDS},
    {"name": "Zscaler", "ats": "phenom", "url": "https://careers.zscaler.com/careers", "keywords": SWE_KEYWORDS},
    {"name": "AMD", "ats": "phenom", "url": "https://careers.amd.com/careers-home", "keywords": SWE_KEYWORDS},
    {"name": "Akamai", "ats": "phenom", "url": "https://careers.akamai.com/jobs", "keywords": SWE_KEYWORDS},
    {"name": "Splunk", "ats": "deprecated", "url": "Acquired by Cisco", "keywords": SWE_KEYWORDS},

    # Dead Greenhouse Platforms
    {"name": "Rippling", "ats": "custom", "id": "rippling", "keywords": SWE_KEYWORDS},
    {"name": "Cohesity", "ats": "custom", "id": "cohesity", "keywords": SWE_KEYWORDS},
    {"name": "Upstox", "ats": "custom", "id": "upstox", "keywords": SWE_KEYWORDS},
    {"name": "Grab", "ats": "custom", "id": "grab", "keywords": SWE_KEYWORDS},
    {"name": "GoTo", "ats": "custom", "id": "gojek", "keywords": SWE_KEYWORDS},
    {"name": "MobiKwik", "ats": "custom", "id": "mobikwik", "keywords": SWE_KEYWORDS},
    {"name": "Pine Labs", "ats": "custom", "id": "pinelabs", "keywords": SWE_KEYWORDS},
    {"name": "Wise", "ats": "custom", "id": "wise", "keywords": SWE_KEYWORDS},
    {"name": "Chargebee", "ats": "custom", "id": "chargebee", "keywords": SWE_KEYWORDS},
    {"name": "Yubi", "ats": "custom", "id": "credavenue", "keywords": SWE_KEYWORDS},
    {"name": "LendingKart", "ats": "custom", "id": "lendingkart", "keywords": SWE_KEYWORDS},
    {"name": "Quadeye", "ats": "custom", "id": "quadeye", "keywords": SWE_KEYWORDS},
    {"name": "GitHub", "ats": "custom", "id": "github", "keywords": SWE_KEYWORDS},
    {"name": "Grammarly", "ats": "custom", "id": "grammarly", "keywords": SWE_KEYWORDS},
    {"name": "Hasura", "ats": "custom", "id": "hasura", "keywords": SWE_KEYWORDS},
    {"name": "HashiCorp", "ats": "ibm", "id": "hashicorp", "keywords": SWE_KEYWORDS},
    {"name": "DigitalOcean", "ats": "workable", "id": "digitalocean", "keywords": SWE_KEYWORDS},
    {"name": "Hugging Face", "ats": "custom", "id": "huggingface", "keywords": SWE_KEYWORDS},
    {"name": "Deel", "ats": "custom", "id": "deel", "keywords": SWE_KEYWORDS},
    {"name": "Polygon", "ats": "custom", "id": "polygon", "keywords": SWE_KEYWORDS},
    {"name": "Innovaccer", "ats": "custom", "id": "innovaccer", "keywords": SWE_KEYWORDS},
    {"name": "Yelp", "ats": "custom", "id": "yelp", "keywords": SWE_KEYWORDS},
    {"name": "Two Sigma", "ats": "custom", "id": "twosigma", "keywords": SWE_KEYWORDS},
    {"name": "Hudson River Trading", "ats": "custom", "id": "hudsonrivertrading", "keywords": SWE_KEYWORDS},
    {"name": "PayU", "ats": "custom", "id": "payu", "keywords": SWE_KEYWORDS},
    {"name": "Freshworks", "ats": "smartrecruiters", "id": "freshworks", "keywords": SWE_KEYWORDS},

    # Dead Lever Platforms
    {"name": "Revolut", "ats": "custom", "id": "revolut", "keywords": SWE_KEYWORDS},
    {"name": "Perfios", "ats": "custom", "id": "perfios", "keywords": SWE_KEYWORDS},
    {"name": "PolicyBazaar", "ats": "custom", "id": "policybazaar", "keywords": SWE_KEYWORDS},
    {"name": "BizNext", "ats": "custom", "id": "biznext", "keywords": SWE_KEYWORDS},
    {"name": "Jumbotail", "ats": "custom", "id": "jumbotail", "keywords": SWE_KEYWORDS},
    {"name": "Atlassian", "ats": "custom", "id": "atlassian", "keywords": SWE_KEYWORDS},
    {"name": "Graviton Research Capital", "ats": "custom", "id": "gravitonresearchcapital", "keywords": SWE_KEYWORDS},
    {"name": "Swiggy", "ats": "custom", "id": "swiggy", "keywords": SWE_KEYWORDS},
    {"name": "Zomato", "ats": "custom", "id": "zomato", "keywords": SWE_KEYWORDS},
    {"name": "Zepto", "ats": "custom", "id": "zepto", "keywords": SWE_KEYWORDS},
    {"name": "Blinkit", "ats": "custom", "id": "blinkit", "keywords": SWE_KEYWORDS},
    {"name": "Lenskart", "ats": "custom", "id": "lenskart", "keywords": SWE_KEYWORDS},
    {"name": "Delhivery", "ats": "custom", "id": "delhivery", "keywords": SWE_KEYWORDS},
    {"name": "Tekion", "ats": "custom", "id": "tekion", "keywords": SWE_KEYWORDS},
    {"name": "Unacademy", "ats": "custom", "id": "unacademy", "keywords": SWE_KEYWORDS},
    {"name": "BharatPe", "ats": "custom", "id": "bharatpe", "keywords": SWE_KEYWORDS},
    {"name": "Spinny", "ats": "custom", "id": "spinny", "keywords": SWE_KEYWORDS},
    {"name": "Acko", "ats": "custom", "id": "acko", "keywords": SWE_KEYWORDS},
    {"name": "Navi", "ats": "custom", "id": "navi", "keywords": SWE_KEYWORDS},
    {"name": "Udaan", "ats": "custom", "id": "udaan", "keywords": SWE_KEYWORDS},
    {"name": "Khatabook", "ats": "custom", "id": "khatabook", "keywords": SWE_KEYWORDS},
    {"name": "UpGrad", "ats": "custom", "id": "upgrad", "keywords": SWE_KEYWORDS},
    {"name": "Whatfix", "ats": "custom", "id": "whatfix", "keywords": SWE_KEYWORDS},
    {"name": "Jupiter Money", "ats": "custom", "id": "jupiter", "keywords": SWE_KEYWORDS},
    {"name": "Smallcase", "ats": "custom", "id": "smallcase", "keywords": SWE_KEYWORDS},
    {"name": "KreditBee", "ats": "custom", "id": "kreditbee", "keywords": SWE_KEYWORDS},
    {"name": "Cashfree", "ats": "custom", "id": "cashfree", "keywords": SWE_KEYWORDS},
    {"name": "Instamojo", "ats": "custom", "id": "instamojo", "keywords": SWE_KEYWORDS},
    {"name": "Open Financial Technologies", "ats": "custom", "id": "open", "keywords": SWE_KEYWORDS},
    {"name": "Signzy", "ats": "custom", "id": "signzy", "keywords": SWE_KEYWORDS},
    {"name": "InMobi", "ats": "custom", "id": "inmobi", "keywords": SWE_KEYWORDS},
    {"name": "Glance", "ats": "custom", "id": "glance", "keywords": SWE_KEYWORDS},
    {"name": "MoEngage", "ats": "custom", "id": "moengage", "keywords": SWE_KEYWORDS},
    {"name": "CleverTap", "ats": "custom", "id": "clevertap", "keywords": SWE_KEYWORDS},
    {"name": "LeadSquared", "ats": "custom", "id": "leadsquared", "keywords": SWE_KEYWORDS},
    {"name": "Amagi", "ats": "custom", "id": "amagi", "keywords": SWE_KEYWORDS},
    {"name": "Shiprocket", "ats": "custom", "id": "shiprocket", "keywords": SWE_KEYWORDS},
    {"name": "Locus", "ats": "custom", "id": "locus", "keywords": SWE_KEYWORDS},
    {"name": "GreyOrange", "ats": "custom", "id": "greyorange", "keywords": SWE_KEYWORDS},
    {"name": "Urban Company", "ats": "custom", "id": "urbancompany", "keywords": SWE_KEYWORDS},
    {"name": "Practo", "ats": "custom", "id": "practo", "keywords": SWE_KEYWORDS},
    {"name": "HealthifyMe", "ats": "custom", "id": "healthifyme", "keywords": SWE_KEYWORDS},
    {"name": "Licious", "ats": "custom", "id": "licious", "keywords": SWE_KEYWORDS},
    {"name": "Vedantu", "ats": "custom", "id": "vedantu", "keywords": SWE_KEYWORDS},
    {"name": "Apna", "ats": "custom", "id": "apna", "keywords": SWE_KEYWORDS},

    # Dead Eightfold Platforms (OAuth2 Locked)
    {"name": "BNY Mellon", "ats": "eightfold_deprecated", "url": "https://bnymellon.eightfold.ai/careers", "keywords": SWE_KEYWORDS},
    {"name": "Morgan Stanley", "ats": "eightfold_deprecated", "url": "https://morganstanley.eightfold.ai/careers", "keywords": SWE_KEYWORDS},
    {"name": "HSBC", "ats": "eightfold_deprecated", "url": "https://hsbc.eightfold.ai/careers", "keywords": SWE_KEYWORDS},
    {"name": "NTT DATA", "ats": "eightfold_deprecated", "url": "https://nttdata.eightfold.ai/careers", "keywords": SWE_KEYWORDS},
    {"name": "Nutanix", "ats": "eightfold_deprecated", "url": "https://nutanix.eightfold.ai/careers", "keywords": SWE_KEYWORDS},
    {"name": "UiPath", "ats": "eightfold_deprecated", "url": "https://uipath.eightfold.ai/careers", "keywords": SWE_KEYWORDS},
    {"name": "Micron Technology", "ats": "eightfold_deprecated", "url": "https://micron.eightfold.ai/careers", "keywords": SWE_KEYWORDS},
    {"name": "Western Digital", "ats": "eightfold_deprecated", "url": "https://westerndigital.eightfold.ai/careers", "keywords": SWE_KEYWORDS},
    {"name": "Ericsson", "ats": "eightfold_deprecated", "url": "https://ericsson.eightfold.ai/careers", "keywords": SWE_KEYWORDS},
    {"name": "STMicroelectronics", "ats": "eightfold_deprecated", "url": "https://stmicroelectronics.eightfold.ai/careers", "keywords": SWE_KEYWORDS},
    {"name": "Lam Research", "ats": "eightfold_deprecated", "url": "https://lamresearch.eightfold.ai/careers", "keywords": SWE_KEYWORDS},
    {"name": "Fortive", "ats": "eightfold_deprecated", "url": "https://fortive.eightfold.ai/careers", "keywords": SWE_KEYWORDS},
    {"name": "Dexcom", "ats": "eightfold_deprecated", "url": "https://dexcom.eightfold.ai/careers", "keywords": SWE_KEYWORDS},
    {"name": "Northrop Grumman", "ats": "eightfold_deprecated", "url": "https://ngc.eightfold.ai/careers", "keywords": SWE_KEYWORDS},
    {"name": "Eightfold AI (Themselves)", "ats": "eightfold_deprecated", "url": "https://app.eightfold.ai/careers", "keywords": SWE_KEYWORDS},
#New 100 companies list from gemini deep research 29/06/2026 4:53PM IST -------------------------------------
    {"name": "Stripe", "ats": "greenhouse", "id": "stripe", "keywords": SWE_KEYWORDS},
{"name": "Coinbase", "ats": "greenhouse", "id": "coinbase", "keywords": SWE_KEYWORDS},
{"name": "Revolut", "ats": "lever", "id": "revolut", "keywords": SWE_KEYWORDS},
{"name": "Affirm", "ats": "greenhouse", "id": "affirm", "keywords": SWE_KEYWORDS},
{"name": "Brex", "ats": "greenhouse", "id": "brex", "keywords": SWE_KEYWORDS},
{"name": "Chime", "ats": "greenhouse", "id": "chime", "keywords": SWE_KEYWORDS},
{"name": "Razorpay", "ats": "greenhouse", "id": "razorpaysoftwareprivatelimited", "keywords": SWE_KEYWORDS},
{"name": "PhonePe", "ats": "greenhouse", "id": "phonepe", "keywords": SWE_KEYWORDS},
{"name": "Paytm", "ats": "lever", "id": "paytm", "keywords": SWE_KEYWORDS},
{"name": "Groww", "ats": "greenhouse", "id": "groww", "keywords": SWE_KEYWORDS},
{"name": "Pine Labs", "ats": "lever", "id": "pinelabs", "keywords": SWE_KEYWORDS},
{"name": "FalconX", "ats": "greenhouse", "id": "falconx", "keywords": SWE_KEYWORDS},
{"name": "Fireblocks", "ats": "greenhouse", "id": "fireblocks", "keywords": SWE_KEYWORDS},
{"name": "Addepar", "ats": "greenhouse", "id": "addepar1", "keywords": SWE_KEYWORDS},
{"name": "Sezzle", "ats": "greenhouse", "id": "sezzle", "keywords": SWE_KEYWORDS},
{"name": "Earnin", "ats": "greenhouse", "id": "earnin", "keywords": SWE_KEYWORDS},
{"name": "Salary Finance", "ats": "greenhouse", "id": "salaryfinance", "keywords": SWE_KEYWORDS},
{"name": "Visa", "ats": "workday", "url": "[https://visa.wd5.myworkdayjobs.com/Visa](https://visa.wd5.myworkdayjobs.com/Visa)", "keywords": SWE_KEYWORDS},
{"name": "PayPal", "ats": "workday", "url": "[https://paypal.wd1.myworkdayjobs.com/jobs](https://paypal.wd1.myworkdayjobs.com/jobs)", "keywords": SWE_KEYWORDS},
{"name": "Mastercard", "ats": "workday", "url": "[https://mastercard.wd1.myworkdayjobs.com/CorporateCareers](https://mastercard.wd1.myworkdayjobs.com/CorporateCareers)", "keywords": SWE_KEYWORDS},
{"name": "CRED", "ats": "greenhouse", "id": "cred", "keywords": SWE_KEYWORDS},
{"name": "Wealthfront", "ats": "greenhouse", "id": "wealthfront", "keywords": SWE_KEYWORDS},
{"name": "Plaid", "ats": "greenhouse", "id": "plaid", "keywords": SWE_KEYWORDS},
{"name": "GoCardless", "ats": "lever", "id": "gocardless", "keywords": SWE_KEYWORDS},
{"name": "Wise", "ats": "lever", "id": "wise", "keywords": SWE_KEYWORDS},

# --- GLOBAL SAAS & PRODUCTIVITY ---
{"name": "Figma", "ats": "greenhouse", "id": "figma", "keywords": SWE_KEYWORDS},
{"name": "Notion", "ats": "greenhouse", "id": "notion", "keywords": SWE_KEYWORDS},
{"name": "Slack", "ats": "greenhouse", "id": "slack", "keywords": SWE_KEYWORDS},
{"name": "Okta", "ats": "greenhouse", "id": "okta", "keywords": SWE_KEYWORDS},
{"name": "Kaseya", "ats": "greenhouse", "id": "kaseya", "keywords": SWE_KEYWORDS},
{"name": "Rubrik", "ats": "greenhouse", "id": "rubrik", "keywords": SWE_KEYWORDS},
{"name": "Acryl Data", "ats": "greenhouse", "id": "acryldata", "keywords": SWE_KEYWORDS},
{"name": "Cambridge Mobile Telematics", "ats": "greenhouse", "id": "cambridgemobiletelematics", "keywords": SWE_KEYWORDS},
{"name": "Instead", "ats": "greenhouse", "id": "instead", "keywords": SWE_KEYWORDS},
{"name": "Toast", "ats": "greenhouse", "id": "toast", "keywords": SWE_KEYWORDS},
{"name": "Datadog", "ats": "greenhouse", "id": "datadog", "keywords": SWE_KEYWORDS},
{"name": "Propel", "ats": "greenhouse", "id": "propel", "keywords": SWE_KEYWORDS},
{"name": "Atlassian", "ats": "lever", "id": "atlassian", "keywords": SWE_KEYWORDS},
{"name": "Canva", "ats": "lever", "id": "canva", "keywords": SWE_KEYWORDS},
{"name": "GitLab", "ats": "lever", "id": "gitlab", "keywords": SWE_KEYWORDS},
{"name": "Discord", "ats": "lever", "id": "discord", "keywords": SWE_KEYWORDS},
{"name": "Automattic", "ats": "lever", "id": "automattic", "keywords": SWE_KEYWORDS},
{"name": "Zeta", "ats": "lever", "id": "zeta", "keywords": SWE_KEYWORDS},
{"name": "AllTrails", "ats": "lever", "id": "alltrails", "keywords": SWE_KEYWORDS},
{"name": "Salesforce", "ats": "workday", "url": "[https://salesforce.wd12.myworkdayjobs.com/External_Career_Site](https://salesforce.wd12.myworkdayjobs.com/External_Career_Site)", "keywords": SWE_KEYWORDS},
{"name": "Workday", "ats": "workday", "url": "[https://workday.wd5.myworkdayjobs.com/Workday](https://workday.wd5.myworkdayjobs.com/Workday)", "keywords": SWE_KEYWORDS},
{"name": "Adobe", "ats": "workday", "url": "[https://adobe.wd5.myworkdayjobs.com/external_experienced](https://adobe.wd5.myworkdayjobs.com/external_experienced)", "keywords": SWE_KEYWORDS},
{"name": "Autodesk", "ats": "workday", "url": "[https://autodesk.wd1.myworkdayjobs.com/Ext](https://autodesk.wd1.myworkdayjobs.com/Ext)", "keywords": SWE_KEYWORDS},
{"name": "Ryan", "ats": "workday", "url": "[https://ryan.wd1.myworkdayjobs.com/RyanCareers](https://ryan.wd1.myworkdayjobs.com/RyanCareers)", "keywords": SWE_KEYWORDS},
{"name": "Uniphore", "ats": "lever", "id": "uniphore", "keywords": SWE_KEYWORDS},

# --- CONSUMER TECH & MARKETPLACES ---
{"name": "Airbnb", "ats": "greenhouse", "id": "airbnb", "keywords": SWE_KEYWORDS},
{"name": "Uber", "ats": "greenhouse", "id": "uber", "keywords": SWE_KEYWORDS},
{"name": "Lyft", "ats": "greenhouse", "id": "lyft", "keywords": SWE_KEYWORDS},
{"name": "Coupang", "ats": "greenhouse", "id": "coupang", "keywords": SWE_KEYWORDS},
{"name": "Roku", "ats": "greenhouse", "id": "roku", "keywords": SWE_KEYWORDS},
{"name": "Spotify", "ats": "greenhouse", "id": "spotify", "keywords": SWE_KEYWORDS},
{"name": "Pinterest", "ats": "greenhouse", "id": "pinterest", "keywords": SWE_KEYWORDS},
{"name": "Snap", "ats": "greenhouse", "id": "snap", "keywords": SWE_KEYWORDS},
{"name": "ByteDance", "ats": "greenhouse", "id": "bytedance", "keywords": SWE_KEYWORDS},
{"name": "Reddit", "ats": "greenhouse", "id": "reddit", "keywords": SWE_KEYWORDS},
{"name": "DoorDash", "ats": "greenhouse", "id": "doordash", "keywords": SWE_KEYWORDS},
{"name": "Instacart", "ats": "greenhouse", "id": "instacart", "keywords": SWE_KEYWORDS},
{"name": "Zillow", "ats": "greenhouse", "id": "zillow", "keywords": SWE_KEYWORDS},
{"name": "Robinhood", "ats": "greenhouse", "id": "robinhood", "keywords": SWE_KEYWORDS},
{"name": "Epic Games", "ats": "greenhouse", "id": "epicgames", "keywords": SWE_KEYWORDS},
{"name": "Booking.com", "ats": "greenhouse", "id": "booking", "keywords": SWE_KEYWORDS},
{"name": "Zomato", "ats": "greenhouse", "id": "zomato", "keywords": SWE_KEYWORDS},
{"name": "Swiggy", "ats": "greenhouse", "id": "swiggy", "keywords": SWE_KEYWORDS},
{"name": "Myntra", "ats": "greenhouse", "id": "myntra", "keywords": SWE_KEYWORDS},
{"name": "MakeMyTrip", "ats": "greenhouse", "id": "makemytrip", "keywords": SWE_KEYWORDS},
{"name": "Meesho", "ats": "greenhouse", "id": "meesho", "keywords": SWE_KEYWORDS},
{"name": "Shiprocket", "ats": "greenhouse", "id": "shiprocket", "keywords": SWE_KEYWORDS},
{"name": "Livspace", "ats": "greenhouse", "id": "livspace", "keywords": SWE_KEYWORDS},
{"name": "Lenskart", "ats": "lever", "id": "lenskart", "keywords": SWE_KEYWORDS},
{"name": "Expedia", "ats": "workday", "url": "[https://expedia.wd5.myworkdayjobs.com/search](https://expedia.wd5.myworkdayjobs.com/search)", "keywords": SWE_KEYWORDS},

# --- DATA, AI & INFRASTRUCTURE LEADERS ---
{"name": "Anthropic", "ats": "greenhouse", "id": "anthropic", "keywords": SWE_KEYWORDS},
{"name": "Databricks", "ats": "greenhouse", "id": "databricks", "keywords": SWE_KEYWORDS},
{"name": "Snowflake", "ats": "greenhouse", "id": "snowflake", "keywords": SWE_KEYWORDS},
{"name": "Cloudflare", "ats": "greenhouse", "id": "cloudflare", "keywords": SWE_KEYWORDS},
{"name": "Confluent", "ats": "greenhouse", "id": "confluent", "keywords": SWE_KEYWORDS},
{"name": "HashiCorp", "ats": "greenhouse", "id": "hashicorp", "keywords": SWE_KEYWORDS},
{"name": "MongoDB", "ats": "greenhouse", "id": "mongodb", "keywords": SWE_KEYWORDS},
{"name": "Elastic", "ats": "greenhouse", "id": "elastic", "keywords": SWE_KEYWORDS},
{"name": "Redis", "ats": "greenhouse", "id": "redis", "keywords": SWE_KEYWORDS},
{"name": "Postman", "ats": "greenhouse", "id": "postman", "keywords": SWE_KEYWORDS},
{"name": "BrowserStack", "ats": "greenhouse", "id": "browserstack", "keywords": SWE_KEYWORDS},
{"name": "Lynx Analytics", "ats": "greenhouse", "id": "lynxanalytics", "keywords": SWE_KEYWORDS},
{"name": "Samsara", "ats": "greenhouse", "id": "samsara", "keywords": SWE_KEYWORDS},
{"name": "Palantir", "ats": "lever", "id": "palantir", "keywords": SWE_KEYWORDS},
{"name": "Mistral", "ats": "lever", "id": "mistral", "keywords": SWE_KEYWORDS},
{"name": "Nvidia", "ats": "eightfold", "url": "[https://nvidia.eightfold.ai/careers](https://nvidia.eightfold.ai/careers)", "keywords": SWE_KEYWORDS},
{"name": "Fortive", "ats": "eightfold", "url": "[https://fortive.eightfold.ai/careers](https://fortive.eightfold.ai/careers)", "keywords": SWE_KEYWORDS},
{"name": "UKG", "ats": "eightfold", "url": "[https://ukg.eightfold.ai/careers](https://ukg.eightfold.ai/careers)", "keywords": SWE_KEYWORDS},
{"name": "NTT Data", "ats": "eightfold", "url": "[https://nttdata.eightfold.ai/careers](https://nttdata.eightfold.ai/careers)", "keywords": SWE_KEYWORDS},
{"name": "Intel", "ats": "eightfold", "url": "[https://intel.eightfold.ai/careers](https://intel.eightfold.ai/careers)", "keywords": SWE_KEYWORDS},
{"name": "Cisco", "ats": "eightfold", "url": "[https://cisco.eightfold.ai/careers](https://cisco.eightfold.ai/careers)", "keywords": SWE_KEYWORDS},
{"name": "Nutanix", "ats": "eightfold", "url": "[https://nutanix.eightfold.ai/careers](https://nutanix.eightfold.ai/careers)", "keywords": SWE_KEYWORDS},
{"name": "UiPath", "ats": "eightfold", "url": "[https://uipath.eightfold.ai/careers](https://uipath.eightfold.ai/careers)", "keywords": SWE_KEYWORDS},
{"name": "Dell", "ats": "eightfold", "url": "[https://dell.eightfold.ai/careers](https://dell.eightfold.ai/careers)", "keywords": SWE_KEYWORDS},
{"name": "Flextronics", "ats": "workday", "url": "[https://flextronics.wd1.myworkdayjobs.com/Careers](https://flextronics.wd1.myworkdayjobs.com/Careers)", "keywords": SWE_KEYWORDS}

]

# --- HELPER FUNCTIONS ---
def estimate_yoe(title):
    t = title.lower()
    if any(x in t for x in ["iii", "lead", "staff", "principal", "manager", "architect"]):
        return "Senior/5+"
    elif any(x in t for x in ["ii", "mid", "senior", "sr"]):
        return "Mid/2-5"
    elif any(x in t for x in ["i", "junior", "jr", "entry", "intern", "new grad", "fresher"]):
        return "Entry/0-2"
    return "NA"

def format_time_ist(raw_time):
    dt = datetime.now(timezone.utc)
    precision = "current"

    if raw_time:
        if isinstance(raw_time, (int, float)):
            val = raw_time / 1000.0 if raw_time > 20000000000 else raw_time
            dt = datetime.fromtimestamp(val, tz=timezone.utc)
            precision = "seconds"
        elif isinstance(raw_time, str):
            raw_str = raw_time.strip()

            if raw_str.lower().startswith("posted"):
                return raw_str.title(), "N/A"

            try:
                dt = datetime.fromisoformat(raw_str.replace("Z", "+00:00"))
                precision = "seconds"
            except ValueError:
                try:
                    dt = datetime.strptime(raw_str, "%Y-%m-%d %H:%M").replace(tzinfo=timezone.utc)
                    precision = "minutes"
                except ValueError:
                    try:
                        dt = datetime.strptime(raw_str, "%Y-%m-%d %H").replace(tzinfo=timezone.utc)
                        precision = "hours"
                    except ValueError:
                        try:
                            dt = datetime.strptime(raw_str, "%B %d, %Y").replace(tzinfo=timezone.utc)
                            precision = "date"
                        except ValueError:
                            try:
                                dt = datetime.strptime(raw_str, "%Y-%m-%d").replace(tzinfo=timezone.utc)
                                precision = "date"
                            except ValueError:
                                pass 

    tz_ist = timezone(timedelta(hours=5, minutes=30))
    dt_ist = dt.astimezone(tz_ist)
    day_formatted = dt_ist.strftime("%A")

    if precision == "seconds":
        time_formatted = dt_ist.strftime("%I:%M:%S %p %d %b")
    elif precision == "minutes":
        time_formatted = dt_ist.strftime("%I:%M %p %d %b")
    elif precision == "hours":
        time_formatted = dt_ist.strftime("%I %p %d %b")
    elif precision == "date":
        time_formatted = dt_ist.strftime("Date Only: %d %b")
    else:
        time_formatted = dt_ist.strftime("%I:%M:%S %p %d %b CUR")

    return time_formatted, day_formatted

# --- NOTIFICATION ENGINE ---
def send_telegram_alert(company, title, url, location, time_posted, day_posted, job_id, yoe):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print(f"🚨 [LOCAL ALERT] {company}: {title}")
        return

    header = f"🚨 **New Job : {company} | {title}**"
    body = (
        f"**🏢Company:** {company}\n"
        f"**💼Role:** {title}\n"
        f"**🕑Time posted:** {time_posted}\n"
        f"**-----------------------------**\n"
        f"**🌏Location:** {location}\n"
        f"**📅Day Posted:** {day_posted}\n"
        f"**Job Id:** {job_id}\n"
        f"**YOE:** {yoe}\n\n"
        f"**-----------------------------**\n"
        f"**Link:** [Apply Here]({url})"
    )

    message = f"{header}\n\n{body}"
    api_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "Markdown",
        "disable_web_page_preview": True,
    }

    try:
        requests.post(api_url, json=payload)
    except Exception as e:
        print(f"Failed to send Telegram alert: {e}")

# --- SCRAPER MODULES ---
def scrape_greenhouse(target):
    jobs = []
    url = f"https://boards-api.greenhouse.io/v1/boards/{target['id']}/jobs"
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            for j in response.json().get("jobs", []):
                jobs.append({
                    "id": str(j["id"]),
                    "title": j.get("title", "Unknown"),
                    "url": j.get("absolute_url", ""),
                    "location": j.get("location", {}).get("name", "Remote/Unspecified"),
                    "raw_time": j.get("updated_at", ""),
                })
    except Exception as e:
        print(f"Error scraping Greenhouse for {target['name']}: {e}")
    return jobs

def scrape_lever(target):
    jobs = []
    url = f"https://api.lever.co/v0/postings/{target['id']}"
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            for j in response.json():
                jobs.append({
                    "id": str(j["id"]),
                    "title": j.get("text", "Unknown"),
                    "url": j.get("hostedUrl", ""),
                    "location": j.get("categories", {}).get("location", "Remote/Unspecified"),
                    "raw_time": j.get("createdAt", ""),
                })
    except Exception as e:
        print(f"Error scraping Lever for {target['name']}: {e}")
    return jobs

def scrape_amazon(target):
    jobs = []
    url = "https://www.amazon.jobs/en/search.json"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    base_query = target["keywords"][0] if target["keywords"] else ""
    params = {"base_query": base_query, "country": target.get("country", "IND"), "result_limit": 10, "sort": "recent"}

    try:
        response = requests.get(url, params=params, headers=headers, timeout=10)
        if response.status_code == 200:
            for j in response.json().get("jobs", []):
                jobs.append({
                    "id": str(j.get("id_icims", j.get("id"))),
                    "title": j.get("title", "Unknown"),
                    "url": "https://www.amazon.jobs" + j.get("job_path", ""),
                    "location": j.get("normalized_location", "India"),
                    "raw_time": j.get("posted_date", ""),
                })
    except Exception as e:
        print(f"Error scraping Amazon: {e}")
    return jobs

def scrape_workday(target):
    """Hits the hidden Workday JSON API and parses exact URLs and IDs."""
    jobs = []
    parsed_uri = urlparse(target["url"])
    domain = f"{parsed_uri.scheme}://{parsed_uri.netloc}"
    tenant = parsed_uri.netloc.split(".")[0]
    
    # Robust portal extraction (handles URLs with or without /en-US/)
    path_parts = [p for p in parsed_uri.path.split("/") if p]
    if "en-US" in path_parts:
        path_parts.remove("en-US")
    portal = path_parts[0] if path_parts else ""

    api_url = f"{domain}/wday/cxs/{tenant}/{portal}/jobs"
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    }
    payload = {"appliedFacets": {}, "limit": 20, "offset": 0, "searchText": ""}

    try:
        response = requests.post(api_url, json=payload, headers=headers, timeout=10)
        if response.status_code == 200:
            for job in response.json().get("jobPostings", []):
                raw_href = job.get("externalPath", "")
                if raw_href:
                    # Strip query parameters (?locations=...)
                    clean_href = raw_href.split("?")[0]
                    
                    # Construct the exact URL structure Workday's UI expects
                    full_url = f"{domain}/en-US/{portal}{clean_href}"
                    
                    # Regex to extract clean Requisition ID (e.g., R-2435849 or REQ-123)
                    slug = clean_href.split("/")[-1]
                    req_match = re.search(r'((?:R|REQ)-?\d+.*)', slug, re.IGNORECASE)
                    job_id = req_match.group(1).upper() if req_match else slug

                    location = job.get("locationsText", "Remote/Unspecified")
                    raw_time = job.get("postedOn", "")

                    jobs.append({
                        "id": job_id,
                        "title": job.get("title", "Unknown"),
                        "url": full_url,
                        "location": location,
                        "raw_time": raw_time,
                    })
    except Exception as e:
        print(f"Error scraping Workday API for {target['name']}: {e}")

    return jobs

def scrape_eightfold(target):
    """Hits the standard Eightfold.ai JSON API."""
    jobs = []
    parsed_uri = urlparse(target["url"])
    domain = parsed_uri.netloc
    
    # Eightfold's standard public API endpoint
    api_url = f"https://{domain}/api/apply/v2/jobs"
    
    # Fetch the 20 most recent jobs
    params = {"domain": domain, "start": 0, "num": 20}
    
    try:
        response = requests.get(api_url, params=params, timeout=10)
        if response.status_code == 200:
            for job in response.json().get("positions", []):
                jobs.append({
                    "id": str(job.get("id", "")),
                    "title": job.get("name", "Unknown"),
                    "url": job.get("url", target["url"]),
                    "location": job.get("location", "Remote/Unspecified"),
                    "raw_time": job.get("t_update", "") # Eightfold uses epoch timestamps
                })
    except Exception as e:
        print(f"Error scraping Eightfold API for {target['name']}: {e}")
        
    return jobs

def scrape_ashby(target):
    """Hits the Ashby public posting API."""
    jobs = []
    url = f"https://api.ashbyhq.com/posting-api/job-board/{target['id']}"
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            for j in response.json().get("jobs", []):
                jobs.append({
                    "id": str(j.get("id", "")),
                    "title": j.get("title", "Unknown"),
                    "url": j.get("jobUrl", ""),
                    "location": j.get("location", "Remote/Unspecified"),
                    "raw_time": j.get("publishedAt", ""),
                })
    except Exception as e:
        print(f"Error scraping Ashby for {target['name']}: {e}")
    return jobs

# --- CORE LOGIC ---
def is_relevant(title, keywords, excluded_keywords):
    title_lower = title.lower()
    
    # 1. Check exclusions first (Fail Fast)
    if excluded_keywords:
        if any(ex.lower() in title_lower for ex in excluded_keywords):
            return False # Immediately reject the job
            
    # 2. Check inclusions
    if not keywords:
        return True
    return any(k.lower() in title_lower for k in keywords)

def main():
    print("Initiating scan...")
    state = {}
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r") as f:
            state = json.load(f)

    state_changed = False
    scrapers = {
        "greenhouse": scrape_greenhouse,
        "lever": scrape_lever,
        "amazon": scrape_amazon,
        "workday": scrape_workday,
        "eightfold": scrape_eightfold,
        "ashby": scrape_ashby,
    }

    for target in TARGETS:
        company_name = target["name"]
        ats_type = target["ats"]

        if ats_type not in scrapers:
            continue

        current_jobs = scrapers[ats_type](target)
        if company_name not in state:
            state[company_name] = []

        for job in current_jobs:
            if job["id"] not in state[company_name]:
                if is_relevant(job["title"], target.get("keywords", []), EXCLUDED_KEYWORDS) and is_india(job["location"]):
                    time_posted, day_posted = format_time_ist(job["raw_time"])
                    yoe = estimate_yoe(job["title"])

                    send_telegram_alert(
                        company=company_name,
                        title=job["title"],
                        url=job["url"],
                        location=job["location"],
                        time_posted=time_posted,
                        day_posted=day_posted,
                        job_id=job["id"],
                        yoe=yoe,
                    )

                state[company_name].append(job["id"])
                state_changed = True

        time.sleep(1)

    if state_changed:
        with open(STATE_FILE, "w") as f:
            json.dump(state, f, indent=4)
        print("State updated.")

if __name__ == "__main__":
    main()