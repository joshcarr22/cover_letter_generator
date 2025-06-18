import os
import requests
from bs4 import BeautifulSoup
import openai
from urllib.parse import urlparse
import time
import logging
import json

# Configure logging
logger = logging.getLogger(__name__)

# ✅ Ensure OpenAI API key is retrieved from environment variables
openai.api_key = os.getenv("OPENAI_API_KEY")

def clean_seek_url(raw_url):
    """Clean the Seek URL by removing query parameters."""
    parsed = urlparse(raw_url)
    return f"https://{parsed.netloc}{parsed.path}"

def scrape_job_details(url):
    """Fetch the job posting page and extract the main job details."""
    try:
        # Clean the URL first
        clean_url = clean_seek_url(url)
        logger.info(f"Cleaned URL: {clean_url}")
        
        # Add comprehensive browser-like headers
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
            ),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Sec-Fetch-User": "?1",
            "Cache-Control": "max-age=0",
            "sec-ch-ua": '"Chromium";v="122", "Not(A:Brand";v="24", "Google Chrome";v="122"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"'
        }
        
        # Create a session to maintain cookies
        session = requests.Session()
        
        # Add a small delay to mimic human behavior
        time.sleep(1)
        
        logger.info("Making request to Seek with browser-like headers")
        # Make the request with the session
        response = session.get(clean_url, headers=headers, timeout=10)
        response.raise_for_status()
        logger.info("Successfully received response from Seek")
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching URL '{url}': {e}")
        raise

    soup = BeautifulSoup(response.text, 'html.parser')
    logger.info("Successfully parsed HTML content")

    # Candidate selectors that might contain the job description.
    selectors = [
        {"tag": "div", "attrs": {"data-automation": "jobAdDetails"}},
        {"tag": "div", "attrs": {"class": "job-description"}},
        {"tag": "div", "attrs": {"class": "description"}},
        {"tag": "div", "attrs": {"data-automation": "normalJob"}},
        {"tag": "div", "attrs": {"data-automation": "jobDescription"}}
    ]

    for sel in selectors:
        element = soup.find(sel["tag"], attrs=sel["attrs"])
        if element:
            text = element.get_text(separator="\n").strip()
            if len(text) > 100:
                logger.info(f"Found job details using selector: {sel}")
                return text

    # If no specific selectors found, try to get the main content
    main_content = soup.find("main") or soup.find("article") or soup.find("div", class_="content")
    if main_content:
        logger.info("Found job details in main content")
        return main_content.get_text(separator="\n").strip()

    logger.warning("No job details found using selectors. Returning full text.")
    return soup.get_text(separator="\n").strip()

def interpret_job_details(raw_text):
    """Extract job details in structured JSON format."""
    prompt = f"""
    Extract and format job details in structured JSON:
    - "job_title"
    - "company_name"
    - "job_description"
    - "experience"
    - "skills"
    - "software"
    - "additional_requirements"
    - "preferred_qualifications"
    - "other_notes"
    
    Job Posting:
    {raw_text}
    
    Return only a valid JSON object.
    """
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are an expert at extracting structured data from job descriptions."},
                {"role": "user", "content": prompt}
            ]
        )
        job_details_str = response.choices[0].message.content.strip()
        
        if not job_details_str:
            raise ValueError("OpenAI returned an empty response.")
        
        return json.loads(job_details_str)
    
    except json.JSONDecodeError as e:
        raise ValueError(f"Error parsing JSON: {e}")
    except Exception as e:
        raise Exception(f"Error interpreting job details: {e}")
