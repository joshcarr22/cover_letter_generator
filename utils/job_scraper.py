import requests
from bs4 import BeautifulSoup
import logging
import re

try:
    import cloudscraper
except Exception:  # cloudscraper is optional but recommended
    cloudscraper = None

logger = logging.getLogger(__name__)

# === Bright Data Proxy Credentials ===
BRIGHT_DATA_HOST = "brd.superproxy.io"
BRIGHT_DATA_PORT = 33335
BRIGHT_DATA_USERNAME = "brd-customer-hl_9930b4f7-zone-residential_proxy1"
BRIGHT_DATA_PASSWORD = "t2fismzy95x8"

BLOCK_PATTERNS = [
    r"residential\s*failed",
    r"requested\s*site\s*is\s*not\s*available",
    r"robots\.txt",
    r"access\s*denied",
    r"forbidden",
    r"webpage\s*not\s*available",
    r"help\s*us\s*keep\s*seek\s*secure",
    r"confirm\s*you\s*are\s*human",
    r"bright\s*data",
    r"captcha",
]


def _looks_blocked(html_text: str) -> bool:
    if not html_text:
        return True
    lowered = html_text.lower()
    for pattern in BLOCK_PATTERNS:
        if re.search(pattern, lowered):
            return True
    return False


def _extract_visible_text(html_text: str) -> str:
    soup = BeautifulSoup(html_text, "html.parser")
    text = soup.get_text(separator="\n")
    return text.strip()


def _fetch_direct(job_url: str, headers: dict, timeout: int = 20) -> str:
    # Try with cloudscraper first (handles Cloudflare and some bot checks)
    if cloudscraper is not None:
        scraper = cloudscraper.create_scraper(
            browser={"browser": "chrome", "platform": "windows", "mobile": False}
        )
        response = scraper.get(job_url, headers=headers, timeout=timeout)
        response.raise_for_status()
        return response.text

    # Fallback to plain requests
    response = requests.get(job_url, headers=headers, timeout=timeout)
    response.raise_for_status()
    return response.text


def _fetch_brightdata(job_url: str, headers: dict, timeout: int = 20) -> str:
    proxies = {
        "http": f"http://{BRIGHT_DATA_USERNAME}:{BRIGHT_DATA_PASSWORD}@{BRIGHT_DATA_HOST}:{BRIGHT_DATA_PORT}",
        "https": f"http://{BRIGHT_DATA_USERNAME}:{BRIGHT_DATA_PASSWORD}@{BRIGHT_DATA_HOST}:{BRIGHT_DATA_PORT}",
    }
    # Use default certificate verification; the target may enforce TLS
    response = requests.get(job_url, headers=headers, proxies=proxies, timeout=timeout, verify=True)
    response.raise_for_status()
    return response.text


def scrape_job_details(job_url):
    """Fetch job page content and return visible text.

    Strategy:
    1) Try a direct fetch (with cloudscraper if available) without proxies.
    2) If that appears blocked or fails, try Bright Data proxy as a fallback.
    3) If still blocked, raise a user-friendly error so the UI can guide the user.
    """
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Referer": "https://www.seek.com.au/",
    }

    # Attempt 1: direct
    try:
        html = _fetch_direct(job_url, headers=headers, timeout=25)
        if not _looks_blocked(html):
            visible = _extract_visible_text(html)
            if len(visible) > 200:
                return visible
            # Too short to be a real job ad; continue to proxy fallback
            logger.warning("Direct fetch returned unusually short content; trying proxy fallback")
        else:
            logger.warning("Direct fetch appears blocked; trying proxy fallback")
    except Exception as direct_err:
        logger.warning(f"Direct fetch failed: {direct_err}; trying proxy fallback")

    # Attempt 2: Bright Data proxy
    try:
        html = _fetch_brightdata(job_url, headers=headers, timeout=25)
        if _looks_blocked(html):
            raise Exception("Target site returned a block page via proxy")
        visible = _extract_visible_text(html)
        if len(visible) > 200:
            return visible
        raise Exception("Fetched content is too short to extract job details")
    except Exception as proxy_err:
        logger.error(f"Seek scraping failed after proxy fallback: {proxy_err}")
        raise Exception(
            "The job page could not be fetched due to site restrictions (robots/proxy blocks). "
            "Please open the job ad in your browser and copy/paste the text into the form, or upload a TXT/DOCX file."
        )
