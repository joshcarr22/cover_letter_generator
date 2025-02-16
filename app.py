import os
import json
import openai
import requests
from datetime import datetime
from flask import Flask, request, render_template, jsonify
from bs4 import BeautifulSoup

# ✅ Ensure OpenAI API key is retrieved from environment variables
openai.api_key = os.getenv("OPENAI_API_KEY")

app = Flask(__name__, template_folder="templates")

def scrape_job_details(url):
    """Fetch the job posting page and extract the main job details."""
    try:
        response = requests.get(url)
        response.raise_for_status()
    except Exception as e:
        raise Exception(f"Error fetching URL '{url}': {e}")

    soup = BeautifulSoup(response.text, 'html.parser')

    # Candidate selectors that might contain the job description.
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
    """Use OpenAI GPT-4o to extract structured job details in JSON format."""

    prompt = f"""
    Extract key job details from the text below and return **ONLY** a valid JSON object.

    Job Posting Text:
    {raw_text}

    **Format:**
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

    **Response Rules:**
    - Output **only JSON** (no extra text).
    - Ensure JSON is **properly formatted** with double quotes.
    - **No explanations, headers, or summaries.** Only return JSON.
    """

    try:
        client = openai.OpenAI()
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are an expert at extracting job details into structured JSON format."},
                {"role": "user", "content": prompt}
            ]
        )

        job_details_str = response.choices[0].message.content.strip()

        if not job_details_str:
            raise ValueError("Empty response from OpenAI.")

        try:
            job_details = json.loads(job_details_str)
            return job_details  
        except json.JSONDecodeError as e:
            print("🚨 Debugging: Invalid JSON Response from OpenAI 🚨")
            print(f"Raw Response:\n{job_details_str}")
            raise ValueError(f"Error parsing JSON: {e}")

    except Exception as e:
        raise Exception(f"Error interpreting job details: {e}")

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
        scraped_text = scrape_job_details(job_url)

        # Interpret job posting details
        job_details = interpret_job_details(scraped_text)

        # Extract key job details
        job_title = job_details.get("job_title", "Unknown Position")
        company_name = job_details.get("company_name", "Unknown Company")
        job_description = job_details.get("job_description", "")
        skills = ", ".join(job_details.get("skills", []))
        software = ", ".join(job_details.get("software", []))
        experience = ", ".join(job_details.get("experience", []))
        today_date = datetime.today().strftime("%d %B %Y")

        # Generate new cover letter with OpenAI GPT-4o
        prompt = f"""
        Based on the job details below, generate a professional, concise, and tailored cover letter.
        
        **Job Title:** {job_title}
        **Company Name:** {company_name}
        **Job Description:** {job_description}
        **Required Skills:** {skills}
        **Software Experience:** {software}
        **Experience Level:** {experience}

        **Existing Cover Letter from User:**
        {user_letter_text}

        **Cover Letter Guidelines:**
        - Use **professional language** and a **polished structure**.
        - Do **not** repeat words excessively.
        - Replace generic phrases with **specific, compelling details**.
        - Keep the tone **enthusiastic, but not overly formal**.
        - Use **exact job title** and **company name** where relevant.

        Return **only** the new cover letter text.
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
            cover_letter = f"Error: Cover letter generation failed. {e}"

        return render_template(
            "result.html",
            job_title=job_title,
            company_name=company_name,
            job_description=job_description,
            experience=experience,
            skills=skills,
            software=software,
            today_date=today_date,
            cover_letter=cover_letter
        )

    return render_template("index.html")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000, debug=True)
