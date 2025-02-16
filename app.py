import os
import json
import requests
from flask import Flask, request, render_template, jsonify
from bs4 import BeautifulSoup
import openai
from datetime import datetime

# Initialize Flask app
app = Flask(__name__, template_folder="templates")

# Ensure OpenAI API key is retrieved from environment variables
openai.api_key = os.getenv("OPENAI_API_KEY")

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
    Extract job details as a **valid JSON object**.
    
    Ensure the response follows this format exactly:
    {{
        "job_title": "Mechanical Engineer",
        "company_name": "XYZ Corp",
        "job_description": "Responsible for mechanical design.",
        "experience": "3+ years required",
        "skills": ["3D CAD", "AutoCAD", "MATLAB"],
        "software": ["SolidWorks"],
        "additional_requirements": ["Bachelor’s degree"],
        "preferred_qualifications": ["FEA experience"],
        "other_notes": ["Hybrid work available"]
    }}

    **Rules:**
    - Respond **ONLY** with valid JSON. No additional text.
    - Do **NOT** include explanations or headers.

    **Job Posting Text:**
    {raw_text}
    """
    try:
        client = openai.OpenAI()
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are an AI that extracts structured job details."},
                {"role": "user", "content": prompt}
            ]
        )

        job_details_str = response.choices[0].message.content.strip()

        if not job_details_str:
            print("🚨 OpenAI returned an empty response. Retrying...")
            raise ValueError("OpenAI returned an empty response.")

        print(f"🚀 Raw API Response:\n{job_details_str}")

        # Ensure JSON is properly formatted
        try:
            job_details = json.loads(job_details_str)
            return job_details
        except json.JSONDecodeError as e:
            print("🚨 Debugging: Invalid JSON Response from OpenAI")
            raise ValueError(f"Error parsing JSON: {e}")

    except Exception as e:
        print(f"🚨 Error: {e}")
        raise Exception(f"Error interpreting job details: {e}")

@app.route("/", methods=["GET", "POST"])
def homepage():
    if request.method == "POST":
        job_url = request.form.get("job_url")
        user_letter = request.files.get("user_letter")
        
        if not job_url or not user_letter:
            return render_template("index.html", error="Both Job URL and cover letter are required.")
        
        user_letter_text = user_letter.read().decode("utf-8")
        scraped_text = scrape_job_details(job_url)
        
        try:
            job_details = interpret_job_details(scraped_text)
        except Exception as e:
            return render_template("index.html", error=str(e))
        
        prompt = f"""
        Generate a professional, concise cover letter based on the following details:
        
        Company: {job_details.get('company_name', 'Unknown Company')}
        Job Title: {job_details.get('job_title', 'Job Title')}
        Skills Required: {', '.join(job_details.get('skills', []))}
        Experience: {job_details.get('experience', 'Not specified')}
        
        Candidate’s Existing Letter:
        {user_letter_text}
        
        Ensure the letter is well-structured, engaging, and reflects the job description requirements.
        """
        
        try:
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are a professional cover letter writer."},
                    {"role": "user", "content": prompt}
                ]
            )
            cover_letter = response.choices[0].message.content.strip()
        except Exception as e:
            return render_template("result.html", job_details=job_details, cover_letter=f"Error: {e}")
        
        return render_template(
            "result.html",
            job_details=job_details,
            cover_letter=cover_letter,
            company_name=job_details.get('company_name', 'Unknown Company'),
            job_title=job_details.get('job_title', 'Job Title'),
            today_date=datetime.today().strftime('%d %B %Y')
        )
    return render_template("index.html")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000, debug=True)
