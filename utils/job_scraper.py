import os
import requests
from bs4 import BeautifulSoup
from openai import OpenAI
from urllib.parse import urlparse
import time
import logging
import json
import random
from fake_useragent import UserAgent
import cloudscraper

# Configure logging
logger = logging.getLogger(__name__)

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def get_random_user_agent():
    """Return a random modern browser user agent using fake-useragent."""
    try:
        ua = UserAgent()
        return ua.random
    except Exception as e:
        logger.warning(f"Error getting random user agent: {e}")
        # Fallback user agents if fake-useragent fails
        user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2.1 Safari/605.1.15",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:123.0) Gecko/20100101 Firefox/123.0",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36 Edg/122.0.0.0",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        ]
        return random.choice(user_agents)

def get_random_headers():
    """Generate random browser-like headers."""
    user_agent = get_random_user_agent()
    return {
        "User-Agent": user_agent,
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
        "sec-ch-ua-platform": '"Windows"',
        "DNT": "1",
        "Referer": "https://www.seek.com.au/",
        "Origin": "https://www.seek.com.au",
        "Pragma": "no-cache",
        "Sec-GPC": "1",
        "Cookie": f"seek_rbp={random.randint(1000000, 9999999)}; seek_visitor={random.randint(1000000, 9999999)}"
    }

def clean_seek_url(raw_url):
    """Clean the Seek URL by removing query parameters."""
    try:
        parsed = urlparse(raw_url)
        if not parsed.netloc or not parsed.path:
            raise ValueError("Invalid URL format")
        return f"https://{parsed.netloc}{parsed.path}"
    except Exception as e:
        logger.error(f"Error cleaning URL: {e}")
        raise ValueError(f"Invalid URL format: {str(e)}")

def simulate_human_behavior(session, url):
    """Simulate human-like browsing behavior."""
    try:
        # Visit homepage first
        logger.info("Visiting Seek homepage")
        session.get("https://www.seek.com.au/", timeout=10)
        time.sleep(random.uniform(2, 4))

        # Visit search page
        logger.info("Visiting search page")
        session.get("https://www.seek.com.au/jobs", timeout=10)
        time.sleep(random.uniform(1, 3))

        # Visit the actual job page
        logger.info(f"Visiting job page: {url}")
        response = session.get(url, timeout=15)
        return response
    except Exception as e:
        logger.error(f"Error in human behavior simulation: {e}")
        raise

def scrape_job_details(url):
    """Fetch the job posting page and extract the main job details."""
    try:
        # Clean the URL first
        clean_url = clean_seek_url(url)
        logger.info(f"Cleaned URL: {clean_url}")
        
        # Create a cloudscraper session to bypass Cloudflare
        scraper = cloudscraper.create_scraper(
            browser={
                'browser': 'chrome',
                'platform': 'windows',
                'desktop': True
            }
        )
        
        # Add a random delay between 1-3 seconds to mimic human behavior
        time.sleep(random.uniform(1, 3))
        
        # Get random headers
        headers = get_random_headers()
        
        # Simulate human behavior
        response = simulate_human_behavior(scraper, clean_url)
        
        # Check if we got a 403
        if response.status_code == 403:
            logger.error("Received 403 Forbidden. Seek is blocking our request.")
            raise Exception("Seek is blocking automated access. Please try again later or use a different job URL.")
        
        # Check for other error status codes
        if response.status_code != 200:
            logger.error(f"Received unexpected status code: {response.status_code}")
            raise Exception(f"Unexpected response from Seek (status code: {response.status_code})")
            
        response.raise_for_status()
        logger.info("Successfully received response from Seek")
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching URL '{url}': {e}")
        raise Exception(f"Failed to fetch job details: {str(e)}")

    try:
        soup = BeautifulSoup(response.text, 'html.parser')
        logger.info("Successfully parsed HTML content")
    except Exception as e:
        logger.error(f"Error parsing HTML: {e}")
        raise Exception(f"Failed to parse job page: {str(e)}")

    # Candidate selectors that might contain the job description.
    selectors = [
        {"tag": "div", "attrs": {"data-automation": "jobAdDetails"}},
        {"tag": "div", "attrs": {"class": "job-description"}},
        {"tag": "div", "attrs": {"class": "description"}},
        {"tag": "div", "attrs": {"data-automation": "normalJob"}},
        {"tag": "div", "attrs": {"data-automation": "jobDescription"}},
        {"tag": "div", "attrs": {"data-automation": "jobDescriptionContent"}},
        {"tag": "div", "attrs": {"class": "job-info"}},
        {"tag": "div", "attrs": {"class": "job-info-content"}},
        {"tag": "div", "attrs": {"data-automation": "jobDescriptionContent"}},
        {"tag": "div", "attrs": {"class": "yvsb870"}},  # New Seek class
        {"tag": "div", "attrs": {"class": "yvsb870 yvsb871"}},  # New Seek class
        {"tag": "div", "attrs": {"class": "job-description__content"}},  # Another Seek class
        {"tag": "div", "attrs": {"class": "job-description__content__content"}}  # Another Seek class
    ]

    for sel in selectors:
        try:
            element = soup.find(sel["tag"], attrs=sel["attrs"])
            if element:
                text = element.get_text(separator="\n").strip()
                if len(text) > 100:
                    logger.info(f"Found job details using selector: {sel}")
                    return text
        except Exception as e:
            logger.warning(f"Error with selector {sel}: {e}")
            continue

    # If no specific selectors found, try to get the main content
    try:
        main_content = soup.find("main") or soup.find("article") or soup.find("div", class_="content")
        if main_content:
            logger.info("Found job details in main content")
            return main_content.get_text(separator="\n").strip()
    except Exception as e:
        logger.warning(f"Error finding main content: {e}")

    logger.warning("No job details found using selectors. Returning full text.")
    return soup.get_text(separator="\n").strip()

def interpret_job_details(raw_text):
    """Extract job details in structured JSON format."""
    if not raw_text or len(raw_text.strip()) < 50:
        raise ValueError("Job description text is too short or empty")
        
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
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are an expert at extracting structured data from job descriptions."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3  # Lower temperature for more consistent output
        )
        job_details_str = response.choices[0].message.content.strip()
        
        if not job_details_str:
            raise ValueError("OpenAI returned an empty response.")
        
        try:
            job_details = json.loads(job_details_str)
            # Validate required fields
            required_fields = ["job_title", "company_name", "job_description"]
            missing_fields = [field for field in required_fields if field not in job_details]
            if missing_fields:
                raise ValueError(f"Missing required fields: {', '.join(missing_fields)}")
            return job_details
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON response: {job_details_str}")
            raise ValueError(f"Error parsing JSON: {e}")
            
    except Exception as e:
        logger.error(f"Error in OpenAI API call: {e}")
        raise Exception(f"Error interpreting job details: {e}")
