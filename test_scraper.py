from utils.job_scraper import scrape_job_details
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_scraper():
    url = "https://www.seek.com.au/job/84825118"
    try:
        logger.info(f"Testing scraper with URL: {url}")
        
        # Step 1: Scrape the job details
        logger.info("Step 1: Scraping job details...")
        raw_text = scrape_job_details(url)
        logger.info(f"Successfully scraped job details. Length: {len(raw_text)} characters")
        logger.info(f"First 200 characters: {raw_text[:200]}")
        
    except Exception as e:
        logger.error(f"Error during testing: {e}")
        raise

if __name__ == "__main__":
    test_scraper() 