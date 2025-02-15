import os
import logging
from openai import OpenAI
from utils.job_scraper import scrape_job_details, interpret_job_details

# =============================================================================
# Configuration – Secure API Key Handling
# =============================================================================
JOB_URL = "https://www.seek.com.au/job/81408443?type=standard&ref=search-standalone&origin=cardTitle#sol=669480783bf9c91a72aaefe0ebf722b9c7269ee9"
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")  # Securely load API key from environment

# =============================================================================
# Initialize OpenAI Client
# =============================================================================
if not OPENAI_API_KEY:
    raise ValueError("Missing OpenAI API key. Set it as an environment variable: OPENAI_API_KEY")

client = OpenAI()  # OpenAI auto-detects the API key from env variables

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def generate_cover_letter(job_details, user_cover_letter):
    """
    Generates a personalized cover letter based on job details and the user's existing cover letter.
    """
    prompt = f"""
Generate a new, highly relevant cover letter for the following job posting using the structured details provided.

Job Details:
{job_details}

Here is the user's existing cover letter, which includes their relevant skills and experiences:
{user_cover_letter}

The new letter should:
- Keep a professional tone
- Match the job details as closely as possible
- Use the user's past experiences in the most relevant way
- Improve clarity and conciseness

Output only the cover letter, without additional text.
"""
    try:
        response = client.chat.completions.create(
            model="gpt-4-turbo",  # Use the best available model
            messages=[
                {"role": "system", "content": "You are a professional cover letter writer."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=1000
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        logging.error(f"OpenAI API call failed: {e}")
        raise Exception(f"OpenAI API call failed: {e}")

def main():
    """
    Main script function to scrape job details, interpret them, and generate a cover letter.
    """
    try:
        raw_text = scrape_job_details(JOB_URL)
    except Exception as e:
        logging.error(f"Error scraping job details: {e}")
        raise Exception(f"Error scraping job details: {e}")

    try:
        job_details = interpret_job_details(raw_text)
    except Exception as e:
        logging.error(f"Error interpreting job details: {e}")
        raise Exception(f"Error interpreting job details: {e}")

    # Load the user's existing cover letter template
    template_path = os.path.join(os.getcwd(), "templates", "old_cover_letter_template.txt")
    if not os.path.exists(template_path):
        raise FileNotFoundError(f"Template file not found: {template_path}")
    
    try:
        with open(template_path, 'r') as file:
            user_cover_letter = file.read()
    except Exception as e:
        logging.error(f"Error reading the template file: {e}")
        raise Exception(f"Error reading the template file: {e}")

    logging.info("Generating new cover letter based on job details and user template...")
    new_cover_letter = generate_cover_letter(job_details, user_cover_letter)

    # Save the new cover letter
    output_path = os.path.join(os.getcwd(), "output", "new_cover_letter.txt")
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    try:
        with open(output_path, 'w') as file:
            file.write(new_cover_letter)
    except Exception as e:
        logging.error(f"Error writing new cover letter to file: {e}")
        raise Exception(f"Error writing new cover letter to file: {e}")

    logging.info(f"New cover letter has been generated and saved to '{output_path}'")

if __name__ == "__main__":
    main()
