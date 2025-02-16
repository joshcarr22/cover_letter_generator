import os
import openai
import requests
import json
from flask import Flask, request, render_template
from bs4 import BeautifulSoup
from datetime import datetime

# Initialize Flask app
app = Flask(__name__, template_folder="templates")

# Ensure OpenAI API key is retrieved
openai.api_key = os.getenv("OPENAI_API_KEY")

# Function to scrape job details
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

# Function to interpret job details using OpenAI GPT-4o
def interpret_job_details(raw_text):
    """Use OpenAI GPT-4o to structure job details into JSON format."""
    prompt = f"""
    Extract key job details and return a structured JSON object. The response must be strictly formatted as valid JSON.

    Job Posting Text:
    {raw_text}

    Format:
    {{
        "job_title": "...",
        "company_name": "...",
        "job_description": "...",
        "experience": ["..."],
        "skills": ["..."],
        "software": ["..."],
        "additional_requirements": ["..."],
        "preferred_qualifications": ["..."],
        "other_notes": ["..."]
    }}
    """

    try:
        client = openai.OpenAI()
        response = client.chat.completions.create(
            model="gpt-4o",  # ✅ Using GPT-4o
            messages=[
                {"role": "system", "content": "You are an expert at analyzing job descriptions and extracting structured details."},
                {"role": "user", "content": prompt}
            ]
        )

        job_details_str = response.choices[0].message.content.strip()
        
        # Ensure valid JSON response
        job_details = json.loads(job_details_str)  # ✅ Use json.loads() instead of eval()
        return job_details  
    except json.JSONDecodeError as e:
        raise Exception(f"Error parsing job details as JSON: {e}")
    except Exception as e:
        raise Exception(f"Error interpreting job details: {e}")

# Function to generate cover letter using GPT-4o
def generate_cover_letter(job_details, user_letter):
    """Use OpenAI GPT-4o to generate a tailored cover letter."""
    current_date = datetime.today().strftime("%d %B %Y")  # Get today's date
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
        client = openai.OpenAI()
        response = client.chat.completions.create(
            model="gpt-4o",  # ✅ Using GPT-4o
            messages=[
                {"role": "system", "content": "You are a professional cover letter writer."},
                {"role": "user", "content": prompt}
            ]
        )

        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"Error generating cover letter: {e}"

# Flask route for homepage
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

# Run the Flask app
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000, debug=True)
