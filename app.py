import os
import openai
import json
import requests
from flask import Flask, request, render_template, jsonify
from flask_cors import CORS
from bs4 import BeautifulSoup
from datetime import datetime

# Initialize Flask app
app = Flask(__name__, template_folder="templates")
CORS(app)  # Enable CORS for API calls from WordPress or other frontends

# Ensure OpenAI API key is retrieved
openai.api_key = os.getenv("OPENAI_API_KEY")

# Function to scrape job details from Seek URL
def scrape_job_details(url):
    """Fetch job posting details and extract key information."""
    try:
        response = requests.get(url)
        response.raise_for_status()
    except Exception as e:
        raise Exception(f"Error fetching job URL '{url}': {e}")

    soup = BeautifulSoup(response.text, 'html.parser')

    # Selectors for different job posting structures
    selectors = [
        {"tag": "div", "attrs": {"data-automation": "jobAdDetails"}},
        {"tag": "div", "attrs": {"class": "job-description"}},
        {"tag": "div", "attrs": {"class": "description"}},
    ]

    job_text = None
    for sel in selectors:
        element = soup.find(sel["tag"], attrs=sel["attrs"])
        if element:
            job_text = element.get_text(separator="\n").strip()
            if len(job_text) > 100:
                break

    if not job_text:
        job_text = soup.get_text(separator="\n").strip()

    # Extract company name (if available)
    company_name_tag = soup.find("div", {"class": "company-name"})
    company_name = company_name_tag.get_text().strip() if company_name_tag else "Unknown Company"

    return job_text, company_name

# Function to interpret job details using OpenAI GPT
def interpret_job_details(raw_text):
    """Use OpenAI GPT to structure job details into JSON format."""
    prompt = f"""
    Extract key job details and return a structured JSON object with these fields:
    - "job_title"
    - "company_name"
    - "job_description"
    - "experience"
    - "skills"
    - "software"
    - "additional_requirements"
    - "preferred_qualifications"
    - "other_notes"

    Job Posting Text:
    {raw_text}

    Return only the JSON output.
    """

    try:
        response = openai.ChatCompletion.create(
            model="gpt-4o",  # ✅ Using GPT-4o
            messages=[
                {"role": "system", "content": "You are an expert at analyzing job descriptions and extracting structured details."},
                {"role": "user", "content": prompt}
            ]
        )

        job_details = response.choices[0].message.content.strip()

        # Try to parse as JSON first
        try:
            return json.loads(job_details)
        except json.JSONDecodeError:
            # Fallback to eval if GPT response is not strict JSON
            return eval(job_details)

    except Exception as e:
        raise Exception(f"Error interpreting job details: {e}")

# Function to generate a cover letter using GPT
def generate_cover_letter(job_details, user_letter):
    """Use OpenAI GPT to generate a tailored cover letter."""
    current_date = datetime.today().strftime("%d %B %Y")
    prompt = f"""
    Generate a personalized, well-structured cover letter based on these job details:

    Job Title: {job_details.get('job_title', 'Unknown Title')}
    Company Name: {job_details.get('company_name', 'Unknown Company')}
    Required Skills: {", ".join(job_details.get('skills', []))}
    Preferred Qualifications: {", ".join(job_details.get('preferred_qualifications', []))}

    - Ensure varied sentence structures to avoid repetition.
    - Use synonyms where appropriate and maintain a natural flow.
    - Match the company's terminology and job role as much as possible.
    - Keep the letter concise and engaging.
    - Use today's date ({current_date}) in the header.

    User's Existing Cover Letter:
    {user_letter}

    ---
    New Cover Letter:
    """

    try:
        response = openai.ChatCompletion.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a professional cover letter writer."},
                {"role": "user", "content": prompt}
            ]
        )

        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"Error generating cover letter: {e}"

# Route for form submission via browser (HTML Form)
@app.route("/", methods=["GET", "POST"])
def homepage():
    if request.method == "POST":
        job_url = request.form.get("job_url")
        user_letter = request.files.get("user_letter")

        if not job_url or not user_letter:
            return render_template("index.html", error="Both Job URL and cover letter are required.")

        # Read user's uploaded cover letter
        user_letter_text = user_letter.read().decode("utf-8")

        # Scrape job details
        try:
            scraped_text, company_name = scrape_job_details(job_url)
        except Exception as e:
            return render_template("index.html", error=str(e))

        # Interpret job details using AI
        try:
            job_details = interpret_job_details(scraped_text)
            job_details["company_name"] = company_name  # Ensure company name is included
        except Exception as e:
            return render_template("index.html", error=str(e))

        # Generate new cover letter
        cover_letter = generate_cover_letter(job_details, user_letter_text)

        return render_template("result.html", cover_letter=cover_letter, job_details=job_details)

    return render_template("index.html")

# API route for JSON-based requests (e.g., Postman, curl)
@app.route("/process-cover-letter", methods=["POST"])
def process_cover_letter():
    """API endpoint to generate a cover letter from a job URL and user cover letter."""
    data = request.get_json()

    job_url = data.get("job_url")
    user_letter = data.get("user_letter", "")

    if not job_url:
        return jsonify({"error": "No job URL provided"}), 400

    try:
        # Scrape job details
        scraped_text, company_name = scrape_job_details(job_url)
        job_details = interpret_job_details(scraped_text)
        job_details["company_name"] = company_name

        # Generate the cover letter
        cover_letter = generate_cover_letter(job_details, user_letter)

        return jsonify({"cover_letter": cover_letter, "job_details": job_details})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Run the Flask app
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000, debug=True)
