import os
import openai  # ✅ Correct import
from flask import Flask, request, render_template, jsonify
from utils.job_scraper import scrape_job_details, interpret_job_details

app = Flask(__name__)

# ✅ Ensure OpenAI API key is retrieved from environment variables
openai.api_key = os.getenv("OPENAI_API_KEY")

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        job_url = request.form.get("job_url")
        user_letter = request.files.get("user_letter")

        if not job_url or not user_letter:
            return render_template("index.html", error="Both Job URL and cover letter are required.")

        # Read user’s uploaded letter
        user_letter_text = user_letter.read().decode("utf-8")

        # Scrape job details
        scraped_text = scrape_job_details(job_url)

        # Interpret job posting
        job_details = interpret_job_details(scraped_text)

        # Generate new cover letter using OpenAI
        prompt = f"""
        Create a personalized cover letter based on this job posting:

        Job Details:
        {job_details}

        User’s existing cover letter:
        {user_letter_text}

        Make the letter concise, professional, and relevant.
        """
        response = openai.ChatCompletion.create(
            model="gpt-4-turbo",
            messages=[
                {"role": "system", "content": "You are a professional cover letter writer."},
                {"role": "user", "content": prompt}
            ]
        )

        cover_letter = response["choices"][0]["message"]["content"]

        return render_template("result.html", cover_letter=cover_letter, job_details=job_details)

    return render_template("index.html")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000, debug=True)  # ✅ Ensure correct port for Render
