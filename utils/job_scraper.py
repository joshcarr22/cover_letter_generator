import os
import requests
from bs4 import BeautifulSoup
from openai import OpenAI

# =============================================================================
# Configuration – Environment variables for security
# =============================================================================
JOB_URL = "https://www.seek.com.au/job/81408443?type=standard&ref=search-standalone&origin=cardTitle#sol=669480783bf9c91a72aaefe0ebf722b9c7269ee9"
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# =============================================================================
# Initialize OpenAI client (API key is auto-detected from environment)
# =============================================================================
client = OpenAI()

def scrape_job_details(url):
    """
    Fetch the job posting page and extract the main job details.
    
    This function attempts to target specific HTML elements that likely contain
    the job description to reduce extra navigation and unrelated text.
    It tries several candidate selectors and falls back to returning all visible text.
    """
    try:
        response = requests.get(url)
        response.raise_for_status()  # Ensure request was successful
    except requests.RequestException as e:
        raise Exception(f"Error fetching URL '{url}': {e}")

    soup = BeautifulSoup(response.text, 'html.parser')

    # Candidate selectors that might contain the job description.
    selectors = [
        {"tag": "div", "attrs": {"data-automation": "jobAdDetails"}},
        {"tag": "div", "attrs": {"class": "job-description"}},
        {"tag": "div", "attrs": {"class": "description"}},
    ]
    
    for sel in selectors:
        element = soup.find(sel["tag"], attrs=sel["attrs"])
        if element:
            text = element.get_text(separator="\n").strip()
            if len(text) > 100:
                return text

    # Fallback: return all visible text.
    return soup.get_text(separator="\n").strip()

def interpret_job_details(raw_text):
    """
    Use OpenAI's API to interpret the job posting text and extract structured details.
    
    The function sends the raw text along with a prompt instructing the model to return
    a JSON structure with job details.
    
    Returns JSON output.
    """
    prompt = f"""
You are an expert in job posting analysis. Given the job posting text below, extract and summarize the key details in a structured JSON format.
The JSON should have the following keys:
- "job_title": The title of the job.
- "job_description": A brief summary of the job description.
- "experience": The level or type of experience required.
- "skills": A list of key skills required for the job.
- "software": A list of software or technical tools mentioned, if any.
- "additional_requirements": Any other requirements mentioned (e.g., certifications, personal attributes).
- "preferred_qualifications": Any preferred qualifications or extra skills that are desirable.
- "other_notes": Any additional relevant notes.

Job Posting Text:
{raw_text}

Return only the JSON output.
"""
    try:
        response = client.chat.completions.create(
            model="gpt-4-turbo",  # Use the best available model
            messages=[
                {"role": "system", "content": "You are an expert in job posting analysis."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=500
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        raise Exception(f"Error interpreting job details: {e}")

# =============================================================================
# Main execution for standalone testing
# =============================================================================
if __name__ == "__main__":
    try:
        raw_text = scrape_job_details(JOB_URL)
        print("Scraped Job Details (first 1000 characters):")
        print(raw_text[:1000])
        
        structured_details = interpret_job_details(raw_text)
        print("\nStructured Job Details:")
        print(structured_details)
    except Exception as e:
        print(f"Error: {e}")
