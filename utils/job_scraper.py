import requests
from bs4 import BeautifulSoup
import logging

logger = logging.getLogger(__name__)

# === Bright Data Proxy Credentials ===
BRIGHT_DATA_HOST = "brd.superproxy.io"
BRIGHT_DATA_PORT = 33335
BRIGHT_DATA_USERNAME = "brd-customer-hl_9930b4f7-zone-residential_proxy1"
BRIGHT_DATA_PASSWORD = "t2fismzy95x8"

def scrape_job_details(job_url):
    """Scrape raw HTML job details from Seek using Bright Data proxy."""
    try:
        proxies = {
            "http": f"http://{BRIGHT_DATA_USERNAME}:{BRIGHT_DATA_PASSWORD}@{BRIGHT_DATA_HOST}:{BRIGHT_DATA_PORT}",
            "https": f"http://{BRIGHT_DATA_USERNAME}:{BRIGHT_DATA_PASSWORD}@{BRIGHT_DATA_HOST}:{BRIGHT_DATA_PORT}"
        }

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
            "Accept-Language": "en-US,en;q=0.9"
        }

        response = requests.get(job_url, headers=headers, proxies=proxies, timeout=20, verify=False)
        soup = BeautifulSoup(response.text, "html.parser")

        # Basic fallback: collect visible text
        return soup.get_text(separator="\n")

    except Exception as e:
        logger.error(f"Seek scraping failed: {e}")
        raise Exception(f"Seek scraping failed: {e}")
