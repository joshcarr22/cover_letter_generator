import os
import json
import logging
from datetime import datetime
from flask import Flask, request, jsonify
from flask_cors import CORS
from utils.job_scraper import scrape_job_details, interpret_job_details

# === Flask App ===
app = Flask(__name__)
CORS(app)

# === Logging ===
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# === Root Route ===
@app.route("/")
def index():
    return jsonify({"message": "Cover Letter Generator API is running"}), 200

# === Cover Letter Generator ===
def generate_cover_letter(job_data):
    try:
        job_title = job_data.get("job_title", "the position")
        company_name = job_data.get("company_name", "your company")
        job_description = job_data.get("job_description", "")
        experience_reqs = job_data.get("experience", [])
        skills_reqs = job_data.get("skills", [])
        software_reqs = job_data.get("software", [])
        additional_reqs = job_data.get("additional_requirements", "")

        # Your experience map
        relevant_experience = {
            "Mincham Aviation": "rebuilding and maintaining industrial equipment",
            "University of Glasgow": "designing and prototyping mechanical systems",
            "Buzz Drones": "manufacturing high-precision components"
        }

        # Flatten all requirements
        all_reqs = []
        for r in (experience_reqs, skills_reqs, software_reqs):
            if isinstance(r, list):
                all_reqs.extend(r)
        if isinstance(additional_reqs, str) and additional_reqs:
            all_reqs.append(additional_reqs)

        # Match & note unmatched
        matched_experience, unmatched_skills = [], []
        for req in all_reqs:
            match = next(
                (f"My time at {job} helped me develop {desc}" for job, desc in relevant_experience.items()
                 if req.lower() in desc.lower()),
                None
            )
            if match:
                matched_experience.append(match)
            else:
                unmatched_skills.append(req)

        # Simple keyword extraction from job description
        keyword_examples = ["rebuilding engines", "manufacturing precision components", "designing mechanical systems"]
        matched_keywords = [kw for kw in keyword_examples if kw in job_description.lower()]

        # Compose cover letter
        cover_letter = f"""
{datetime.today().strftime('%d %B %Y')}

{company_name}
RE: {job_title} Position

Dear Hiring Manager,

As a mechanical engineer with expertise in {matched_keywords[0] if matched_keywords else "industrial engineering"}, I am excited to apply for the {job_title} role at {company_name}. My experience at Mincham Aviation, University of Glasgow, and Buzz Drones has prepared me to contribute meaningfully to your team.

Highlights:
- At Mincham Aviation: {relevant_experience["Mincham Aviation"]}
- At University of Glasgow: {relevant_experience["University of Glasgow"]}
- At Buzz Drones: {relevant_experience["Buzz Drones"]}

I am enthusiastic about contributing my problem-solving and technical skills to your team. Thank you for your time and consideration.

Sincerely,  
Joshua Carr
"""

        if unmatched_skills:
            cover_letter += "\n\n### Skills I'm Eager to Learn:\n"
            for skill in unmatched_skills[:3]:
                cover_letter += f"- While I haven't worked with {skill}, I've developed adjacent skills in related domains.\n"

        return cover_letter.strip()

    except Exception as e:
        logger.error(f"Error generating cover letter: {e}")
        raise

# === Route: /process-cover-letter ===
@app.route("/process-cover-letter", methods=["POST"])
def process_cover_letter():
    logger.info("Request received at /process-cover-letter")
    data = request.get_json()
    job_url = data.get("job_url")

    if not job_url:
        return jsonify({"error": "No job URL provided"}), 400

    try:
        raw_text = scrape_job_details(job_url)
        job_data = interpret_job_details(raw_text)
        letter = generate_cover_letter(job_data)

        return jsonify({
            "job_data": job_data,
            "cover_letter": letter
        })

    except Exception as e:
        logger.error(f"Processing error: {e}")
        return jsonify({"error": str(e)}), 500

# === Route: /health ===
@app.route("/health")
def health_check():
    return jsonify({"status": "healthy"}), 200

# === App Entry Point ===
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port, debug=False)
