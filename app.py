import os
import json
import requests
from flask import Flask, request, jsonify
from flask_cors import CORS
from bs4 import BeautifulSoup
from openai import OpenAI
from datetime import datetime

# Initialize Flask app
app = Flask(__name__)
CORS(app)  # Enable CORS for API calls

# Initialize OpenAI client with environment API key
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def scrape_job_details(url):
    """Fetch job details from Seek job posting."""
    try:
        response = requests.get(url)
        response.raise_for_status()
    except Exception as e:
        raise Exception(f"Error fetching URL '{url}': {e}")

    soup = BeautifulSoup(response.text, 'html.parser')

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
    
    return soup.get_text(separator="\n").strip()

def interpret_job_details(raw_text):
    """Use OpenAI API to interpret job posting and extract key details."""
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

def generate_cover_letter(job_data):
    """Generate a personalized cover letter based on extracted job details."""
    job_title = job_data.get("job_title", "the position")
    company_name = job_data.get("company_name", "your company")
    experience_reqs = job_data.get("experience", [])
    skills_reqs = job_data.get("skills", [])
    software_reqs = job_data.get("software", [])
    additional_reqs = job_data.get("additional_requirements", [])

    cover_letter = f"""
    {datetime.today().strftime('%d %B %Y')}

    {company_name}
    RE: {job_title} Position

    Dear Hiring Manager,

    I am excited to apply for the {job_title} role at {company_name}. My experience and skills align with your requirements, and I am confident that I can contribute meaningfully to your team.

    Thank you for considering my application. I look forward to the opportunity to discuss how my background, skills, and enthusiasm align with your needs.

    Kind regards,
    Joshua Carr
    """

    return cover_letter

@app.route("/process-cover-letter", methods=["POST"])
def process_cover_letter():
    """API endpoint to generate a cover letter from a job URL."""
    data = request.json
    job_url = data.get('job_url')

    if not job_url:
        return jsonify({"error": "No job URL provided"}), 400

    try:
        raw_text = scrape_job_details(job_url)
        job_data = interpret_job_details(raw_text)
        cover_letter = generate_cover_letter(job_data)
        return jsonify({"cover_letter": cover_letter})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000, debug=True)
