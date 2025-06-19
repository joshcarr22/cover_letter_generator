import os
import json
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

# Initialize OpenAI client when needed (lazy load)
def get_openai_client():
    from openai import OpenAI
    return OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def interpret_job_details(raw_text):
    """Use OpenAI API to extract job details."""
    prompt = f"""
    Extract and format job details in structured JSON format. Return ONLY valid JSON, no other text.

    Required fields:
    - "job_title": string
    - "company_name": string  
    - "job_description": string
    - "experience": array of strings
    - "skills": array of strings
    - "software": array of strings
    - "additional_requirements": string
    - "preferred_qualifications": array of strings
    - "other_notes": string

    Job Posting:
    {raw_text[:3000]}

    Return only valid JSON:
    """

    client = get_openai_client()

    try:
        response = client.chat.completions.create(
            model="gpt-4-turbo",
            messages=[
                {"role": "system", "content": "You are an expert at extracting structured data from job descriptions. Return only valid JSON, no markdown or extra text."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=1000,
            temperature=0.1
        )

        job_details_str = response.choices[0].message.content.strip()
        logger.info(f"OpenAI job details response: {job_details_str[:200]}...")
        
        # Clean up response - remove markdown code blocks if present
        if job_details_str.startswith('```'):
            job_details_str = job_details_str.split('```')[1]
            if job_details_str.startswith('json'):
                job_details_str = job_details_str[4:]
        
        # Try to parse JSON
        job_data = json.loads(job_details_str)
        return job_data
        
    except json.JSONDecodeError as e:
        logger.error(f"JSON parsing failed. Raw response: {job_details_str}")
        # Return a default structure if JSON parsing fails
        return {
            "job_title": "Position",
            "company_name": "Company", 
            "job_description": "Job description from posting",
            "experience": ["Experience from posting"],
            "skills": ["Skills from posting"],
            "software": [],
            "additional_requirements": "",
            "preferred_qualifications": [],
            "other_notes": f"JSON parsing error: {e}"
        }
    except Exception as e:
        logger.error(f"Error interpreting job details: {e}")
        raise Exception(f"Error interpreting job details: {e}")

def generate_cover_letter(job_details, user_letter):
    """Generate a personalized cover letter using OpenAI."""
    current_date = datetime.today().strftime("%d %B %Y")
    prompt = f"""
    Generate a professional cover letter. Return only the cover letter text, no markdown or extra formatting.

    Job Title: {job_details.get('job_title', 'Unknown Title')}
    Company Name: {job_details.get('company_name', 'Unknown Company')}
    Required Skills: {", ".join(job_details.get('skills', []))}
    
    Base this cover letter on the user's existing letter below, but personalize it for the job above:
    
    {user_letter}
    
    Requirements:
    - Use today's date: {current_date}
    - Professional tone
    - Highlight relevant experience
    - Keep it concise (under 400 words)
    - Return only the cover letter text
    """

    client = get_openai_client()

    try:
        response = client.chat.completions.create(
            model="gpt-4-turbo",
            messages=[
                {"role": "system", "content": "You are a professional cover letter writer. Return only the cover letter text, no markdown formatting."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=800,
            temperature=0.3
        )
        
        cover_letter = response.choices[0].message.content.strip()
        logger.info(f"Generated cover letter length: {len(cover_letter)} characters")
        return cover_letter
        
    except Exception as e:
        logger.error(f"Error generating cover letter: {e}")
        return f"Error generating cover letter: {e}"
