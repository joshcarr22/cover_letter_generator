import os
import openai
import requests
from flask import Flask, request, render_template, jsonify
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
        raise Exception(f"Error fetching URL '{url}': {e}")

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

# Function to interpret job details using OpenAI
def interpret_job_details(raw_text):
    """Use OpenAI to structure job details into JSON format."""
    prompt = f"""
    Extract and return job details in structured JSON format with these fields:
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
        client = openai.OpenAI()
        response = client.chat.completions.create(
            model="gpt-4-turbo",
            messages=[
                {"role": "system", "content": "You are an expert at analyzing job descriptions."},
                {"role": "user", "content": prompt}
            ]
        )

        job_details = response.choices[0].message.content.strip()
        return eval(job_details)  # Convert string JSON to dictionary
    except Exception as e:
        raise Exception(f"Error interpreting job details: {e}")

# Function to generate cover letter
def generate_cover_letter(job_details, user_letter):
    """Use OpenAI to generate a customized cover letter."""
    current_date = datetime.today().strftime("%d %B %Y")  # Get today's date
    prompt = f"""
    Generate a professional and well-structured cover letter based on the following job details:

    Job Title: {job_details['job_title']}
    Company Name: {job_details['company_name']}
    Required Skills: {", ".join(job_details['skills'])}
    Preferred Qualifications: {", ".join(job_details['preferred_qualifications'])}

    - Keep language varied and avoid repetition.
    - Use synonyms where appropriate.
    - Match the company's terminology and job role as much as possible.
    - Ensure the cover letter remains concise and engaging.
    - Use today's date ({current_date}) in the header.

    User's Existing Cover Letter:
    {user_letter}

    ---
    New Cover Letter:
    """

    try:
        client = openai.OpenAI()
        response = client.chat.completions.create(
            model="gpt-4-turbo",
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
