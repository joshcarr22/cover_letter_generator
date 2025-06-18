import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse
import logging

logger = logging.getLogger(__name__)

# === Bright Data Proxy Configuration ===
BRIGHTDATA_USERNAME = "brd-customer-hl_9930b4f7-zone-residential_proxy1"
BRIGHTDATA_PASSWORD = "t2fismzy95x8"
BRIGHTDATA_HOST = "brd.superproxy.io"
BRIGHTDATA_PORT = "33335"

def get_brightdata_proxies():
    """Return proxy dictionary for Bright Data."""
    proxy_auth = f"{BRIGHTDATA_USERNAME}:{BRIGHTDATA_PASSWORD}@{BRIGHTDATA_HOST}:{BRIGHTDATA_PORT}"
    return {
        "http": f"http://{proxy_auth}",
        "https": f"http://{proxy_auth}",
    }

def clean_seek_url(raw_url):
    """Clean Seek job URL to avoid issues with query params or fragments."""
    parsed = urlparse(raw_url)
    return f"https://{parsed.netloc}{parsed.path}"

def scrape_job_details(url):
    """Scrape job description text from Seek using Bright Data proxy."""
    cleaned_url = clean_seek_url(url)
    proxies = get_brightdata_proxies()
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                      "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": "https://www.seek.com.au/"
    }

    try:
        response = requests.get(cleaned_url, headers=headers, proxies=proxies, timeout=30)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")

        # Try multiple possible containers for job description
        selectors = [
            {"tag": "div", "attrs": {"data-automation": "jobAdDetails"}},
            {"tag": "div", "attrs": {"class": "job-description"}},
            {"tag": "div", "attrs": {"class": "description"}},
        ]

        for sel in selectors:
            section = soup.find(sel["tag"], sel["attrs"])
            if section:
                return section.get_text(separator="\n", strip=True)

        # Fallback: return full text
        return soup.get_text(separator="\n", strip=True)

    except Exception as e:
        logger.error(f"Seek scraping failed: {e}")
        raise Exception(f"Seek scraping failed: {e}")
