import os
import json
import requests
from flask import Flask, request, jsonify
from flask_cors import CORS
from bs4 import BeautifulSoup
from openai import OpenAI
from datetime import datetime
import logging
from utils.job_scraper import scrape_job_details, interpret_job_details

# Initialize Flask app
app = Flask(__name__)
CORS(app)  # Enable CORS for API calls from WordPress

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def generate_cover_letter(job_data):
    """Generate a personalized cover letter based on extracted job details."""
    try:
        job_title = job_data.get("job_title", "the position")
        company_name = job_data.get("company_name", "your company")
        experience_reqs = job_data.get("experience", [])
        skills_reqs = job_data.get("skills", [])
        software_reqs = job_data.get("software", [])
        additional_reqs = job_data.get("additional_requirements", "")
        
        # Match your past jobs to new role requirements
        relevant_experience = {
            "Mincham Aviation": "rebuilding and maintaining industrial equipment",
            "University of Glasgow": "designing and prototyping mechanical systems",
            "Buzz Drones": "manufacturing high-precision components"
        }
        
        # Find most relevant matches
        matched_experience = []
        unmatched_skills = []
        
        # Combine all requirements into a single list
        all_requirements = []
        if isinstance(experience_reqs, list):
            all_requirements.extend(experience_reqs)
        if isinstance(skills_reqs, list):
            all_requirements.extend(skills_reqs)
        if isinstance(software_reqs, list):
            all_requirements.extend(software_reqs)
        if isinstance(additional_reqs, str) and additional_reqs:
            all_requirements.append(additional_reqs)
        
        for req in all_requirements:
            match = next((f"My time at {job} helped me develop {desc}" 
                          for job, desc in relevant_experience.items() if req.lower() in desc.lower()), None)
            if match:
                matched_experience.append(match)
            else:
                unmatched_skills.append(req)  # Note unmatched skills
        
        # Extract main job description keywords
        job_description = job_data.get("job_description", "")
        main_keywords = ["rebuilding engines", "manufacturing precision components", "designing mechanical systems"]
        if job_description:
            main_keywords = [word for word in main_keywords if word in job_description.lower()]
        
        # Generate cover letter content
        cover_letter = f"""
        {datetime.today().strftime('%d %B %Y')}
        
        {company_name}
        RE: {job_title} Position
        
        Dear Hiring Manager,
        
        As a mechanical engineer with expertise in {main_keywords[0] if main_keywords else "industrial equipment"}, I am excited to apply for the {job_title} role at {company_name}. My background in {relevant_experience["Mincham Aviation"]}, {relevant_experience["University of Glasgow"]}, and {relevant_experience["Buzz Drones"]}, along with my passion for innovation, positions me as a strong candidate for this opportunity.
        
        As you are seeking an engineer who can {experience_reqs[0] if experience_reqs else "deliver results in fast-paced environments"}, I bring a proven track record in {relevant_experience["Mincham Aviation"]}, {relevant_experience["University of Glasgow"]}, and {relevant_experience["Buzz Drones"]}. Below, I have highlighted how my background aligns with {company_name}'s needs:
        
        - My experience in {relevant_experience["Mincham Aviation"]} equips me to {main_keywords[0] if main_keywords else "rebuild and optimize industrial machinery"}.
        - My work in {relevant_experience["University of Glasgow"]} has honed my ability to {main_keywords[1] if len(main_keywords) > 1 else "design and prototype mechanical systems"}.
        - My role at {relevant_experience["Buzz Drones"]} ensures I can {main_keywords[2] if len(main_keywords) > 2 else "manufacture high-precision components"}.
        
        I am eager to bring my technical expertise and problem-solving skills to {company_name}, contributing to your ongoing success. 
        
        Thank you for considering my application. I look forward to the opportunity to discuss how my skills and experiences align with your needs.
        
        Warm regards,
        
        Joshua Carr
        """

        # Append missing experience notes (limit to 3 key skills)
        if unmatched_skills:
            cover_letter += f"\n\n### Areas Where Experience May Not Fully Align\n"
            cover_letter += "If my experience does not fully meet a job requirement, I have leveraged:\n\n"
            for skill in unmatched_skills[:3]:  # Limit to 3 unmatched skills
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
        logger.info("Successfully generated cover letter")

        return jsonify({
            "job_data": job_data,
            "cover_letter": cover_letter
        })

    except Exception as e:
        logger.error(f"Error processing cover letter: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/health")
def health_check():
    """Health check endpoint for Render."""
    return jsonify({"status": "healthy"}), 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port, debug=False)  # Set debug=False for production
