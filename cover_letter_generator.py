import os
import openai  # ✅ Correct import
import logging
from utils.job_scraper import scrape_job_details, interpret_job_details

# ✅ Ensure OpenAI API key is retrieved from environment variables
openai.api_key = os.getenv("OPENAI_API_KEY")

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def generate_cover_letter(job_details, user_cover_letter):
    """Generates a personalized cover letter based on job details and the user's existing cover letter."""
    prompt = f"""
    Generate a professional, highly relevant cover letter for the job posting below.

    Job Details:
    {job_details}

    Here is the user's existing cover letter, which includes their relevant skills and experiences:
    {user_cover_letter}

    The new letter should:
    - Maintain a professional tone
    - Match the job details as closely as possible
    - Use the user's past experiences in the most relevant way
    - Improve clarity and conciseness

    Output only the cover letter, with no additional text.
    """
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4-turbo",
            messages=[
                {"role": "system", "content": "You are a professional cover letter writer."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=1000
        )
        return response["choices"][0]["message"]["content"].strip()
    except Exception as e:
        logging.error(f"OpenAI API call failed: {e}")
        return f"Error: {str(e)}"

def main():
    """Main function to generate a cover letter."""
    # Prompt the user for a job URL and existing cover letter
    job_url = input("Enter the job posting URL: ")
    cover_letter_path = input("Enter the path to your existing cover letter text file: ")

    # Scrape the job posting details using the URL
    try:
        raw_text = scrape_job_details(job_url)
    except Exception as e:
        logging.error(f"Error scraping job details: {e}")
        return

    # Use OpenAI to extract structured job details from the scraped text
    try:
        job_details = interpret_job_details(raw_text)
    except Exception as e:
        logging.error(f"Error interpreting job details: {e}")
        return

    # Read the existing cover letter from a text file
    if not os.path.exists(cover_letter_path):
        logging.error(f"Cover letter file not found: {cover_letter_path}")
        return

    try:
        with open(cover_letter_path, 'r') as file:
            user_cover_letter = file.read()
    except Exception as e:
        logging.error(f"Error reading the cover letter file: {e}")
        return

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
        return

    logging.info(f"New cover letter has been generated and saved to '{output_path}'")
    print(f"\nGenerated Cover Letter:\n{'-'*40}\n{new_cover_letter}\n{'-'*40}")

if __name__ == "__main__":
    main()
