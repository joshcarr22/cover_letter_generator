import os
import json
from datetime import datetime

# Initialize OpenAI client when needed (lazy load)
def get_openai_client():
    from openai import OpenAI
    return OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def interpret_job_details(raw_text):
    """Use OpenAI API to extract job details."""
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

    client = get_openai_client()

    try:
        response = client.chat.completions.create(
            model="gpt-4-turbo",
            messages=[
                {"role": "system", "content": "You are an expert at extracting structured data from job descriptions."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=1000
        )

        job_details_str = response.choices[0].message.content.strip()
        return json.loads(job_details_str)
    except json.JSONDecodeError as e:
        raise ValueError(f"Error parsing JSON from OpenAI: {e}")
    except Exception as e:
        raise Exception(f"Error interpreting job details: {e}")

def generate_cover_letter(job_details, user_letter):
    """Generate a personalized cover letter using OpenAI."""
    current_date = datetime.today().strftime("%d %B %Y")
    prompt = f"""
    Generate a personalized, well-structured cover letter based on these job details:

    Job Title: {job_details.get('job_title', 'Unknown Title')}
    Company Name: {job_details.get('company_name', 'Unknown Company')}
    Required Skills: {", ".join(job_details.get('skills', []))}
    Preferred Qualifications: {", ".join(job_details.get('preferred_qualifications', []))}

    - Use varied sentence structures to avoid repetition.
    - Maintain a natural flow and professional tone.
    - Match company language and role expectations.
    - Keep it concise and tailored.
    - Use today's date ({current_date}) in the header.

    User's Existing Cover Letter:
    {user_letter}

    ---
    New Cover Letter:
    """

    client = get_openai_client()

    try:
        response = client.chat.completions.create(
            model="gpt-4-turbo",
            messages=[
                {"role": "system", "content": "You are a professional cover letter writer."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=1000
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"Error generating cover letter: {e}"
