import os
import logging
from flask import Flask, request, jsonify
from flask_cors import CORS
from utils.job_scraper import scrape_job_details
from utils.openai_cover_letter import interpret_job_details, generate_cover_letter

app = Flask(__name__)
CORS(app)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@app.route("/process-cover-letter", methods=["POST"])
def process_cover_letter():
    """Main endpoint to process job URL and generate cover letter."""
    logger.info("Request received at /process-cover-letter")
    data = request.get_json()
    job_url = data.get("job_url")

    if not job_url:
        return jsonify({"error": "No job URL provided"}), 400

    try:
        # Step 1: Scrape raw job text using Bright Data proxy
        raw_text = scrape_job_details(job_url)
        
        # Step 2: Use GPT-4 to extract structured job information
        job_data = interpret_job_details(raw_text)
        
        # Step 3: Generate personalized cover letter using GPT-4
        # For now, we'll use a basic user profile - this could be enhanced later
        user_profile = """
        Joshua Carr - Mechanical Engineer
        Experience:
        - Mincham Aviation: rebuilding and maintaining industrial equipment
        - University of Glasgow: designing and prototyping mechanical systems  
        - Buzz Drones: manufacturing high-precision components
        """
        
        cover_letter = generate_cover_letter(job_data, user_profile)

        return jsonify({
            "job_data": job_data,
            "cover_letter": cover_letter
        })

    except Exception as e:
        logger.error(f"Processing error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/health")
def health_check():
    """Health check endpoint."""
    return jsonify({"status": "healthy"}), 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
