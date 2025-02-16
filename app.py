import os
import openai
from flask import Flask, request, render_template
from utils.job_scraper import interpret_job_details

# ✅ Ensure OpenAI API key is retrieved from environment variables
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not OPENAI_API_KEY:
    raise ValueError("Missing OpenAI API key. Set it as an environment variable.")

client = openai.OpenAI(api_key=OPENAI_API_KEY)  # ✅ Initialize OpenAI client

# ✅ Explicitly define the templates folder
app = Flask(__name__, template_folder="templates")

@app.route("/", methods=["GET", "POST"])
def homepage():
    if request.method == "POST":
        job_url = request.form.get("job_url")
        user_letter = request.files.get("user_letter")

        if not job_url or not user_letter:
            return render_template("index.html", error="Both Job URL and cover letter are required.")

        # Read user’s uploaded letter
        user_letter_text = user_letter.read().decode("utf-8")

        # Scrape and process job details
        raw_text = scrape_job_details(job_url)
        job_details = interpret_job_details(raw_text)

        # Extract variables from JSON
        job_title = job_details.get("job_title", "Unknown Position")
        company_name = job_details.get("company_name", "Unknown Company")
        skills = ", ".join(job_details.get("skills_needed", []))
        location = job_details.get("location", "Not specified")
        application_deadline = job_details.get("application_deadline", "No deadline specified")

        # Include a summary before the cover letter
        job_summary = f"""
        Job Title: {job_title}
        Company: {company_name}
        Location: {location}
        Required Skills: {skills}
        Application Deadline: {application_deadline}
        """

        # Construct prompt for OpenAI with the **correct** details
        prompt = f"""
        Create a personalized cover letter based on this job posting:

        {job_summary}

        User’s existing cover letter:
        {user_letter_text}

        Make the letter concise, professional, and relevant.
        """

        try:
            cover_letter = interpret_job_details(prompt)  # ✅ Now using updated job details

            return render_template("result.html", job_summary=job_summary, cover_letter=cover_letter)

        except Exception as e:
            return render_template("index.html", error=f"Error generating cover letter: {e}")

    return render_template("index.html")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000, debug=True)
