import os
import logging
from flask import Flask, request, jsonify
from flask_cors import CORS
from werkzeug.utils import secure_filename
import docx
from utils.job_scraper import scrape_job_details
from utils.openai_cover_letter import interpret_job_details, generate_cover_letter

app = Flask(__name__)
CORS(app)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def extract_text_from_file(file):
    """Extract text from uploaded TXT or DOCX file."""
    filename = secure_filename(file.filename)
    
    if filename.endswith('.txt'):
        return file.read().decode('utf-8')
    elif filename.endswith('.docx'):
        doc = docx.Document(file)
        return '\n'.join([paragraph.text for paragraph in doc.paragraphs])
    else:
        raise ValueError("Unsupported file format. Please use TXT or DOCX files.")

@app.route("/process-cover-letter", methods=["POST"])
def process_cover_letter():
    """Main endpoint to process job URL and generate cover letter."""
    logger.info("Request received at /process-cover-letter")
    
    # Handle both JSON and form data
    if request.is_json:
        data = request.get_json()
        job_url = data.get("job_url")
        user_cover_letter = data.get("cover_letter_text", "")
    else:
        # Handle form data
        job_url = request.form.get("job-url")
        user_cover_letter = request.form.get("cover-letter-text", "")
        
        # Handle file upload
        if 'file-upload' in request.files:
            file = request.files['file-upload']
            if file and file.filename:
                try:
                    file_content = extract_text_from_file(file)
                    user_cover_letter = file_content if file_content else user_cover_letter
                except Exception as e:
                    return jsonify({"error": f"File processing error: {str(e)}"}), 400

    if not job_url:
        return jsonify({"error": "No job URL provided"}), 400

    # Use default profile if no cover letter provided
    if not user_cover_letter.strip():
        user_cover_letter = """
        Joshua Carr - Mechanical Engineer
        Experience:
        - Mincham Aviation: rebuilding and maintaining industrial equipment
        - University of Glasgow: designing and prototyping mechanical systems  
        - Buzz Drones: manufacturing high-precision components
        """

    try:
        # Step 1: Scrape raw job text using Bright Data proxy
        raw_text = scrape_job_details(job_url)
        
        # Step 2: Use GPT-4 to extract structured job information
        job_data = interpret_job_details(raw_text)
        
        # Step 3: Generate personalized cover letter using GPT-4
        cover_letter = generate_cover_letter(job_data, user_cover_letter)

        return jsonify({
            "job_data": job_data,
            "cover_letter": cover_letter,
            "success": True
        })

    except Exception as e:
        logger.error(f"Processing error: {e}")
        return jsonify({"error": str(e), "success": False}), 500

@app.route("/health")
def health_check():
    """Health check endpoint."""
    return jsonify({"status": "healthy"}), 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
