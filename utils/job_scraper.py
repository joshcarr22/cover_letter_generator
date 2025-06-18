import os
import requests
import time
import json
import logging
from bs4 import BeautifulSoup
from urllib.parse import urlparse
from openai import OpenAI

# Setup logging
logger = logging.getLogger(__name__)

def clean_seek_url(raw_url):
    """Remove query parameters from Seek URL."""
    try:
        parsed = urlparse(raw_url)
        return f"https://{parsed.netloc}{parsed.path}"
    except Exception as e:
        logger.error(f"Failed to clean URL: {e}")
        raise

def get_browser_headers():
    """Return strong browser-like headers to bypass basic bot protection."""
    return {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        ),
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": "https://www.seek.com.au/",
    }

def scrape_job_details(url):
    """Scrape the Seek job ad HTML and extract the main content block."""
    clean_url = clean_seek_url(url)
    headers = get_browser_headers()

    try:
        logger.info(f"Fetching Seek job: {clean_url}")
        response = requests.get(clean_url, headers=headers, timeout=15)

        if response.status_code == 403:
            logger.warning("403 Forbidden – Seek may be blocking the scraper.")
            raise Exception("Seek is blocking access. Please try a different job URL.")

        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
    except Exception as e:
        logger.error(f"Error fetching/parsing job: {e}")
        raise

    selectors = [
        {"tag": "div", "attrs": {"data-automation": "jobAdDetails"}},
        {"tag": "div", "attrs": {"class": "job-description"}},
        {"tag": "div", "attrs": {"class": "yvsb870 yvsb871"}}
    ]

    for sel in selectors:
        try:
            node = soup.find(sel["tag"], sel["attrs"])
            if node:
                text = node.get_text(separator="\n").strip()
                if len(text) > 100:
                    return text
        except Exception as e:
            logger.debug(f"Failed selector {sel}: {e}")
            continue

    # Fallback: return main body text
    try:
        main = soup.find("main") or soup.find("article")
        return main.get_text(separator="\n").strip() if main else soup.get_text(separator="\n").strip()
    except Exception as e:
        logger.error(f"Error extracting fallback content: {e}")
        return soup.get_text(separator="\n").strip()

def interpret_job_details(raw_text):
    """Use OpenAI to extract structured job fields."""
    if not raw_text or len(raw_text.strip()) < 50:
        raise ValueError("Job description text is too short to interpret.")

    prompt = f"""
    Extract and format the following job fields in JSON:
    - job_title
    - company_name
    - job_description
    - experience
    - skills
    - software
    - additional_requirements
    - preferred_qualifications
    - other_notes

    Job Posting:
    {raw_text}

    Return only a valid JSON object.
    """

    try:
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You extract clean, structured JSON from job descriptions."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3
        )
        content = response.choices[0].message.content.strip()
        job_data = json.loads(content)

        # Validate
        for field in ["job_title", "company_name", "job_description"]:
            if field not in job_data:
                raise ValueError(f"Missing required field: {field}")

        return job_data

    except Exception as e:
        logger.error(f"OpenAI parsing error: {e}")
        raise Exception(f"Failed to extract job details: {e}")
