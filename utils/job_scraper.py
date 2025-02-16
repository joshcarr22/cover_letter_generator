import os
import requests
from bs4 import BeautifulSoup
import openai

# ✅ Ensure OpenAI API key is retrieved from environment variables
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not OPENAI_API_KEY:
    raise ValueError("Missing OpenAI API key. Set it as an environment variable.")

client = openai.OpenAI(api_key=OPENAI_API_KEY)  # ✅ Initialize OpenAI client

def scrape_job_details(url):
    """Fetch the job posting page and extract the main job details."""
    try:
        response = requests.get(url)
        response.raise_for_status()
    except Exception as e:
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
    """Use OpenAI API to interpret job posting and extract key details."""
    prompt = f"""
    Analyze the job posting text below and return a structured JSON format with these keys:
    - "job_title"
    - "company_name"
    - "job_description"
    - "experience_required"
    - "skills_needed"
    - "software_requirements"
    - "additional_requirements"
    - "preferred_qualifications"
    - "location"
    - "application_deadline"

    Job Posting Text:
    {raw_text}

    Return only the JSON output, no extra text.
    """
    
    try:
        response = client.chat.completions.create(
            model="gpt-4-turbo",
            messages=[{"role": "user", "content": prompt}]
        )

        job_details = response.choices[0].message.content  # Extract the structured JSON
        return job_details

    except Exception as e:
        raise Exception(f"Error interpreting job details: {e}")

