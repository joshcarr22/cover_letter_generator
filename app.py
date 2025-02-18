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
CORS(app)  # Enable CORS for API calls from WordPress

# Load OpenAI API key
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise ValueError("Missing OpenAI API key. Set it as an environment variable: OPENAI_API_KEY")
client = OpenAI(api_key=api_key)


def scrape_job_details(url):
    """Fetch job details from Seek job posting."""
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
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
    Extract job details into JSON format:
    {{
      "job_title": "",
      "company_name": "",
      "job_description": "",
      "experience": [],
      "skills": [],
      "software": [],
      "additional_requirements": [],
      "preferred_qualifications": [],
      "other_notes": []
    }}

    Job Posting:
    {raw_text}
    
    Ensure JSON is well-structured and complete.
    """
    try:
        response = client.chat.completions.create(
            model="gpt-4-turbo",
            messages=[
                {"role": "system", "content": "You are an expert in structuring job descriptions."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=1000
        )
        job_details_str = response.choices[0].message.content.strip()
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

    relevant_experience = {
        "Mincham Aviation": "regulated workshop environments",
        "University of Glasgow": "wind tunnel tests & structured procedures",
        "Buzz Drones": "manual milling & CNC machining skills"
    }

    matched_experience = []
    unmatched_skills = []

    for req in experience_reqs + skills_reqs + software_reqs:
        match = next((f"My time at {job} helped me develop {desc}"
                      for job, desc in relevant_experience.items() if req in desc), None)
        if match:
            matched_experience.append(match)
        else:
            unmatched_skills.append(req)

    cover_letter = f"""
    {datetime.today().strftime('%d %B %Y')}
    
    {company_name}
    RE: {job_title} Position
    
    Dear Hiring Manager,
    
    I am excited to apply for the {job_title} position at {company_name}. With a strong background in aerospace engineering and precision manufacturing, I am confident in my ability to contribute effectively to your team.
    
    Key experiences that align with the job requirements:
    
    - {matched_experience[0] if len(matched_experience) > 0 else ""}
    - {matched_experience[1] if len(matched_experience) > 1 else ""}
    - {matched_experience[2] if len(matched_experience) > 2 else ""}
    
    I am eager to bring my expertise in problem-solving and innovation to {company_name}. I look forward to the opportunity to further discuss how my skills align with your needs.
    
    Best regards,
    
    Joshua Carr
    """

    if unmatched_skills:
        cover_letter += "\n\n### Areas Where Experience May Not Fully Align\n"
        for skill in unmatched_skills:
            cover_letter += f"- While I have not worked directly with {skill}, I have developed comparable expertise through related projects.\n"

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
