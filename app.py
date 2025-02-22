import os
import json
import requests
from flask import Flask, request, jsonify
from flask_cors import CORS
from bs4 import BeautifulSoup
from openai import OpenAI
from datetime import datetime
import logging

# Initialize Flask app
app = Flask(__name__)
CORS(app)  # Enable CORS for API calls from WordPress

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def scrape_job_details(url):
    """Fetch job details from Seek job posting."""
    try:
        response = requests.get(url)
        response.raise_for_status()
    except Exception as e:
        logger.error(f"Error fetching URL '{url}': {e}")
        raise

    soup = BeautifulSoup(response.text, 'html.parser')
    logger.info(f"Fetched HTML content from {url}")

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
                logger.info(f"Extracted job details: {text[:100]}...")  # Log first 100 chars
                return text
    
    logger.warning("No job details found using selectors. Returning full text.")
    return soup.get_text(separator="\n").strip()

def interpret_job_details(raw_text):
    """Use OpenAI API to interpret job posting and extract key details."""
    try:
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
        response = client.chat.completions.create(
            model="gpt-4-turbo",
            messages=[
                {"role": "system", "content": "You are an expert at extracting structured data from job descriptions."},
                {"role": "user", "content": prompt}
            ]
        )
        job_details_str = response.choices[0].message.content.strip()
        logger.info(f"OpenAI response: {job_details_str}")
        return json.loads(job_details_str)
    except json.JSONDecodeError as e:
        logger.error(f"Error parsing JSON: {e}")
        raise
    except Exception as e:
        logger.error(f"Error interpreting job details: {e}")
        raise

def generate_cover_letter(job_data):
    """Generate a personalized cover letter based on extracted job details."""
    try:
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

        logger.info(f"Generated cover letter: {cover_letter[:100]}...")  # Log first 100 chars
        return cover_letter
    except Exception as e:
        logger.error(f"Error generating cover letter: {e}")
        raise

@app.route("/process-cover-letter", methods=["POST"])
def process_cover_letter():
    """API endpoint to generate a cover letter from a job URL."""
    logger.info("Received request to /process-cover-letter")
    data = request.json
    job_url = data.get('job_url')

    if not job_url:
        logger.error("No job URL provided")
        return jsonify({"error": "No job URL provided"}), 400

    try:
        logger.info(f"Scraping job details from URL: {job_url}")
        raw_text = scrape_job_details(job_url)
        logger.info(f"Extracted job details: {raw_text[:100]}...")  # Log first 100 chars

        logger.info("Interpreting job details using OpenAI")
        job_data = interpret_job_details(raw_text)
        logger.info(f"Interpreted job data: {job_data}")

        logger.info("Generating cover letter")
        cover_letter = generate_cover_letter(job_data)
        logger.info(f"Generated cover letter: {cover_letter[:100]}...")  # Log first 100 chars
        
        return jsonify({"cover_letter": cover_letter})

    except Exception as e:
        logger.error(f"Error processing cover letter: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000, debug=True)
