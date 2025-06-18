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
import asyncio
from pyppeteer import launch

# Configure logging
logger = logging.getLogger(__name__)

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

async def _scrape_with_browser(url):
    """Internal function to scrape using pyppeteer."""
    browser = await launch(
        headless=True,
        args=['--no-sandbox', '--disable-setuid-sandbox']
    )
    try:
        page = await browser.newPage()
        await page.setUserAgent(get_random_user_agent())
        await page.goto(url, {'waitUntil': 'networkidle0', 'timeout': 30000})
        
        # Get the content
        title = await page.evaluate('() => document.querySelector("h1")?.innerText || ""')
        company = await page.evaluate('() => document.querySelector(\'[data-automation="advertiser-name"]\')?.innerText || ""')
        location = await page.evaluate('() => document.querySelector(\'[data-automation="job-detail-location"]\')?.innerText || ""')
        description = await page.evaluate('() => document.querySelector(\'[data-automation="jobAdDetails"]\')?.innerText || ""')
        
        return f"{title}\n\n{company}\n{location}\n\n{description}"
    finally:
        await browser.close()

def scrape_job_details(url):
    """Fetch the job posting page and extract the main job details using pyppeteer."""
    try:
        clean_url = clean_seek_url(url)
        logger.info(f"Scraping URL: {clean_url}")
        
        # Run the async function
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(_scrape_with_browser(clean_url))
        loop.close()
        
        return result
    except Exception as e:
        logger.error(f"Error scraping job details: {e}")
        raise Exception(f"Seek scraping failed: {e}")

def interpret_job_details(raw_text):
    """Extract job details in structured JSON format."""
    if not raw_text or len(raw_text.strip()) < 50:
        raise ValueError("Job description text is too short or empty")
    
    # Initialize OpenAI client only when needed
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    
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
