import os
import json
from datetime import datetime
from openai import OpenAI

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def interpret_job_details(raw_text):
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
            model="gpt-4-turbo",
            messages=[
                {"role": "system", "content": "You are an expert at extracting structured data from job descriptions."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=1000
        )
        return json.loads(response.choices[0].message.content.strip())
    except json.JSONDecodeError as e:
        raise ValueError(f"JSON parsing error: {e}")
    except Exception as e:
        raise Exception(f"OpenAI error: {e}")

def generate_cover_letter(job_details, user_letter):
    current_date = datetime.today().strftime("%d %B %Y")
    prompt = f"""
    Generate a personalized, professional cover letter:

    Job Title: {job_details.get('job_title', 'Unknown')}
    Company Name: {job_details.get('company_name', 'Unknown')}
    Required Skills: {', '.join(job_details.get('skills', []))}
    Preferred Qualifications: {', '.join(job_details.get('preferred_qualifications', []))}

    Existing User Letter:
    {user_letter}

    Today's Date: {current_date}
    Return only the full cover letter text.
    """
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
        raise Exception(f"OpenAI error: {e}") 