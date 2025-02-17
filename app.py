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
    """Fetch the job posting page and extract the main job details."""
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

@app.route("/process-cover-letter", methods=["POST"])
def process_cover_letter():
    """API endpoint to process cover letter text."""
    data = request.json
    cover_letter_text = data.get('cover_letter_text')
    
    if not cover_letter_text:
        return jsonify({"error": "No cover letter text provided"}), 400

    # Call ChatGPT to process the cover letter
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a professional cover letter writer."},
                {"role": "user", "content": cover_letter_text}
            ]
        )
        processed_letter = response.choices[0].message.content
        return jsonify({"processed_letter": processed_letter})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/process-cover-letter-file", methods=["POST"])
def process_cover_letter_file():
    """Handles file uploads and returns a generated cover letter."""
    if 'file' not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files['file']
    if file.filename.endswith('.txt'):
        cover_letter_text = file.read().decode('utf-8')
    elif file.filename.endswith('.docx'):
        doc = docx.Document(file)
        cover_letter_text = "\n".join([para.text for para in doc.paragraphs])
    else:
        return jsonify({"error": "Unsupported file type"}), 400

    # Call ChatGPT to process the cover letter
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a professional cover letter writer."},
                {"role": "user", "content": cover_letter_text}
            ]
        )
        processed_letter = response.choices[0].message.content
        return jsonify({"processed_letter": processed_letter})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000, debug=True)
