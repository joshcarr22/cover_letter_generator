import os
import openai
from datetime import datetime

# Initialize OpenAI client with API key from environment variable
client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def interpret_job_details(raw_text):
    """Use OpenAI API to interpret job posting and extract key details."""
    prompt = f"""
    Extract and format job details in structured JSON:
    - "job_title"
    - "company_name"
    - "job_description"
    - "experience"
    - "skills"
    - "software"
    - "additional_requirements"
    - "preferred_qualifications"
    - "other_notes"

    Job Posting:
    {raw_text}

    Return only a valid JSON object.
    """
    try:
        response = client.chat.completions.create(
            model="gpt-4-turbo",  # ✅ Using GPT-4 Turbo
            messages=[
                {"role": "system", "content": "You are an expert at extracting structured data from job descriptions."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=1000
        )
        job_details_str = response.choices[0].message.content.strip()
        return eval(job_details_str)  # Convert string JSON to dictionary
    except Exception as e:
        raise Exception(f"Error interpreting job details: {e}")

def generate_cover_letter(job_details, user_letter):
    """Use OpenAI GPT-4 Turbo to generate a tailored cover letter."""
    current_date = datetime.today().strftime("%d %B %Y")  # Today's date
    prompt = f"""
    Generate a personalized, well-structured cover letter based on these job details:

    Job Title: {job_details.get('job_title', 'Unknown Title')}
    Company Name: {job_details.get('company_name', 'Unknown Company')}
    Required Skills: {", ".join(job_details.get('skills', []))}
    Preferred Qualifications: {", ".join(job_details.get('preferred_qualifications', []))}

    - Ensure varied sentence structures to avoid repetition.
    - Use synonyms where appropriate and maintain a natural flow.
    - Match the company's terminology and job role as much as possible.
    - Keep the letter concise and engaging.
    - Use today's date ({current_date}) in the header.

    User's Existing Cover Letter:
    {user_letter}

    ---
    New Cover Letter:
    """

    try:
        response = client.chat.completions.create(
            model="gpt-4-turbo",  # ✅ Using GPT-4 Turbo
            messages=[
                {"role": "system", "content": "You are a professional cover letter writer."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=1000
        )

        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"Error generating cover letter: {e}"

if __name__ == "__main__":
    # Sample usage (for local testing)
    sample_job_text = "We are hiring an Aerospace Engineer with experience in jet engine design and testing."
    sample_user_letter = "Dear Hiring Manager, I am writing to express my interest in your engineering position."

    try:
        job_data = interpret_job_details(sample_job_text)
        cover_letter = generate_cover_letter(job_data, sample_user_letter)
        print("Generated Cover Letter:\n", cover_letter)
    except Exception as error:
        print("Error:", error)
