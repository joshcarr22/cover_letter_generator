import os
import json
import requests
from flask import Flask, request, jsonify
from flask_cors import CORS
from bs4 import BeautifulSoup
from openai import OpenAI
from datetime import datetime
import docx  # Required for .docx file handling

# Initialize Flask app
app = Flask(__name__)
CORS(app)  # Enable CORS for API calls

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def scrape_job_details(url):
    """Fetch the job posting page and extract job details."""
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
    """Use OpenAI API to extract structured job details."""
    prompt = f"""
    Extract structured job details from the text:
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
    
    Return ONLY valid JSON output.
    """
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are an expert at extracting job details into structured JSON."},
                {"role": "user", "content": prompt}
            ]
        )
        job_details_str = response.choices[0].message.content.strip()
        return json.loads(job_details_str)
    except json.JSONDecodeError as e:
        raise ValueError(f"Error parsing JSON: {e}")
    except Exception as e:
        raise Exception(f"Error interpreting job details: {e}")

@app.route("/process-cover-letter", methods=["POST"])
def process_cover_letter():
    """Generates a structured cover letter following the old template."""
    data = request.json
    cover_letter_text = data.get('cover_letter_text')
    job_url = data.get('job_url')
    
    if not cover_letter_text:
        return jsonify({"error": "No cover letter text provided"}), 400
    
    job_details = scrape_job_details(job_url) if job_url else ""
    structured_details = interpret_job_details(job_details) if job_details else {}
    
    prompt = f"""
    Create a cover letter in the following structure:
    
    1. **Introduction**: Mention job title, company, and why the candidate is a fit.
    2. **Experience Mappings**: Three bullet points linking past jobs to new job requirements.
    3. **Closing Paragraph**: Enthusiasm for the role, thanking them, and requesting an interview.
    
    Use synonyms if words repeat too often.
    Job Details:
    {structured_details}
    
    Candidate Experience:
    {cover_letter_text}
    """
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a professional cover letter writer."},
                {"role": "user", "content": prompt}
            ]
        )
        processed_letter = response.choices[0].message.content
        
        # Identify gaps between experience and job requirements
        missing_skills = [skill for skill in structured_details.get('skills', []) if skill.lower() not in cover_letter_text.lower()]
        missing_experience = [exp for exp in structured_details.get('experience', []) if exp.lower() not in cover_letter_text.lower()]
        
        notes = {
            "missing_skills": missing_skills,
            "missing_experience": missing_experience,
            "suggestions": "Consider highlighting adjacent or transferable experience if direct experience is missing."
        }
        
        return jsonify({"processed_letter": processed_letter, "notes": notes})
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000, debug=True)
