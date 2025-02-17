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

# Initialize OpenAI client
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

def generate_cover_letter(job_data):
    """Generate a personalized cover letter based on extracted job details."""
    
    job_title = job_data.get("job_title", "the position")
    company_name = job_data.get("company_name", "your company")
    experience_reqs = job_data.get("experience", [])
    skills_reqs = job_data.get("skills", [])
    software_reqs = job_data.get("software", [])
    additional_reqs = job_data.get("additional_requirements", [])
    
    # Match your past jobs to new role requirements
    relevant_experience = {
        "Mincham Aviation": "regulated workshop environments",
        "University of Glasgow": "wind tunnel tests & structured procedures",
        "Buzz Drones": "manual milling & CNC machining skills"
    }
    
    # Find most relevant matches
    matched_experience = []
    unmatched_skills = []
    
    for req in experience_reqs + skills_reqs + software_reqs:
        match = next((f"My time at {job} helped me develop {desc}" 
                      for job, desc in relevant_experience.items() if req in desc), None)
        if match:
            matched_experience.append(match)
        else:
            unmatched_skills.append(req)  # Note unmatched skills
    
    # Generate cover letter content
    cover_letter = f"""
    {datetime.today().strftime('%d %B %Y')}
    
    {company_name}
    RE: {job_title} Position
    
    Dear Hiring Manager,
    
    I am writing to apply for the {job_title} position at {company_name} as advertised. With a robust background in aerospace engineering, specifically in turbojet design and build, combined with experience in high-precision manufacturing environments, I am confident in my ability to contribute effectively to your team.
    
    Throughout my career, I have developed expertise that aligns with the key competencies required for this role:
    
    - {matched_experience[0] if len(matched_experience) > 0 else ""}
    - {matched_experience[1] if len(matched_experience) > 1 else ""}
    - {matched_experience[2] if len(matched_experience) > 2 else ""}
    
    I am particularly enthusiastic about the opportunity to apply my technical expertise and problem-solving skills to {company_name}, where I am eager to contribute to the company’s ongoing success. 
    
    Thank you for considering my application. I look forward to the opportunity to discuss how my skills and experiences align with your needs.
    
    Warm regards,
    
    Joshua Carr
    """

    # Append missing experience notes
    if unmatched_skills:
        cover_letter += f"\n\n### Areas Where Experience May Not Fully Align\n"
        cover_letter += "If my experience does not fully meet a job requirement, I have leveraged:\n\n"
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
        # Scrape job details from Seek URL
        raw_text = scrape_job_details(job_url)
        job_data = interpret_job_details(raw_text)

        # Generate the cover letter based on extracted job details
        cover_letter = generate_cover_letter(job_data)
        
        return jsonify({"cover_letter": cover_letter})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000, debug=True)
