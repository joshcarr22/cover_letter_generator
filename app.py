import os
import json
import logging
from datetime import datetime
from flask import Flask, request, jsonify
from flask_cors import CORS
from utils.job_scraper import scrape_job_details
from utils.openai_cover_letter import interpret_job_details, generate_cover_letter

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

# === Route: /process-cover-letter ===
@app.route("/process-cover-letter", methods=["POST"])
def process_cover_letter():
    logger.info("Request received at /process-cover-letter")
    data = request.get_json()
    job_url = data.get("job_url")
    user_letter = data.get("user_letter", "")

    if not job_url:
        return jsonify({"error": "No job URL provided"}), 400

    try:
        raw_text = scrape_job_details(job_url)
        job_data = interpret_job_details(raw_text)
        letter = generate_cover_letter(job_data, user_letter)

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
    app.run(host="0.0.0.0", port=port)
