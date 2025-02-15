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

        # Construct prompt for OpenAI
        prompt = f"""
        Create a personalized cover letter based on this job posting:

        Job Details:
        {job_url}  # Instead of scraping, we pass the raw job URL

        User’s existing cover letter:
        {user_letter_text}

        Make the letter concise, professional, and relevant.
        """

        try:
            cover_letter = interpret_job_details(prompt)  # ✅ Using the fixed function

            return render_template("result.html", cover_letter=cover_letter, job_url=job_url)
        except Exception as e:
            return render_template("index.html", error=f"Error generating cover letter: {e}")

    return render_template("index.html")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000, debug=True)
