import os
import openai
from flask import Flask, request, render_template, jsonify
from utils.job_scraper import scrape_job_details, interpret_job_details

# ✅ Ensure OpenAI API key is retrieved from environment variables
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError("Missing OpenAI API key. Set it as an environment variable: OPENAI_API_KEY")

openai.api_key = OPENAI_API_KEY

# ✅ Initialize Flask app
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

        # Scrape job details
        scraped_text = scrape_job_details(job_url)

        if not scraped_text or len(scraped_text) < 50:
            return render_template("result.html", job_summary="No job details available.", cover_letter="Error: Could not scrape job details.")

        # Interpret job posting
        job_summary = interpret_job_details(scraped_text)

        # Generate new cover letter using OpenAI
        client = openai.OpenAI()  # ✅ Correct OpenAI initialization
        prompt = f"""
        Create a personalized cover letter based on this job posting:

        Job Details (Summarized):
        {job_summary}

        User’s existing cover letter:
        {user_letter_text}

        Make the letter concise, professional, and relevant.
        """

        try:
            response = client.chat.completions.create(
                model="gpt-4-turbo",
                messages=[
                    {"role": "system", "content": "You are a professional cover letter writer."},
                    {"role": "user", "content": prompt}
                ]
            )

            cover_letter = response.choices[0].message.content
        except Exception as e:
            return render_template("result.html", job_summary=job_summary, cover_letter=f"Error: {e}")

        return render_template("result.html", job_summary=job_summary, cover_letter=cover_letter)

    return render_template("index.html")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000, debug=True)  # ✅ Ensure correct port for Render
