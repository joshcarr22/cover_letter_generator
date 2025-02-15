from flask import Flask, render_template, request
import os
from utils.job_scraper import scrape_job_details, interpret_job_details
from cover_letter_generator import generate_cover_letter

app = Flask(__name__)

# Get your OpenAI API key from an environment variable
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")  # Securely load API key from environment

# =============================================================================
# Initialize OpenAI Client
# =============================================================================
if not OPENAI_API_KEY:
    raise ValueError("Missing OpenAI API key. Set it as an environment variable: OPENAI_API_KEY")

client = OpenAI()  # OpenAI auto-detects the API key from env variables

# Set the path to your cover letter template
TEMPLATE_PATH = os.path.join(os.getcwd(), "templates", "old_cover_letter_template.txt")

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        job_url = request.form.get("job_url")
        # 1. Scrape the job posting
        try:
            scraped_text = scrape_job_details(job_url)
        except Exception as e:
            return render_template("index.html", error="Error scraping job details: " + str(e))
        
        # 2. Interpret the job details using your OpenAI logic
        try:
            job_details = interpret_job_details(OPENAI_API_KEY, scraped_text)
        except Exception as e:
            return render_template("index.html", error="Error interpreting job details: " + str(e))
        
        # 3. Read your existing cover letter template
        try:
            with open(TEMPLATE_PATH, "r") as f:
                cover_letter_template = f.read()
        except Exception as e:
            return render_template("index.html", error="Error reading cover letter template: " + str(e))
        
        # 4. Generate a new cover letter
        try:
            cover_letter = generate_cover_letter(OPENAI_API_KEY, job_details, cover_letter_template)
        except Exception as e:
            return render_template("index.html", error="Error generating cover letter: " + str(e))
        
        # Render the results page with the generated content.
        return render_template("result.html",
                               cover_letter=cover_letter,
                               job_details=job_details,
                               scraped_text=scraped_text)
    return render_template("index.html")

if __name__ == "__main__":
    app.run(debug=True)
