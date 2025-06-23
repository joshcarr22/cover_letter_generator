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

    IMPORTANT: Filter out any irrelevant content such as:
    - Advertisements or marketing content
    - Website navigation elements
    - Proxy service mentions (like BrightData, Bright Data, etc.)
    - Cookie notices or privacy policies
    - Social media links or unrelated content
    
    Focus ONLY on the actual job posting content including:
    - Job title and company name
    - Job description and responsibilities
    - Required skills and experience
    - Qualifications and software requirements

    Required fields:
    - "job_title": string
    - "company_name": string  
    - "job_description": string (summary of main responsibilities)
    - "experience": array of strings (years required, specific experience)
    - "skills": array of strings (technical and soft skills)
    - "software": array of strings (specific software/tools mentioned)
    - "additional_requirements": string (education, certifications, etc.)
    - "preferred_qualifications": array of strings (nice-to-have qualifications)
    - "other_notes": string (location, work type, salary range if mentioned)

    Job Posting Text (may contain irrelevant content to filter out):
    {raw_text[:3000]}

    Return only valid JSON focusing on the actual job posting content:
    """

    client = get_openai_client()

    try:
        response = client.chat.completions.create(
            model="gpt-4-turbo",
            messages=[
                {"role": "system", "content": "You are an expert at extracting structured job data from web pages. Filter out irrelevant content like ads, navigation, and proxy service mentions. Focus only on actual job posting content. Return only valid JSON, no markdown or extra text."},
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
    Generate a professional, personalized cover letter. Return only the cover letter text, no markdown or extra formatting.

    Job Details:
    - Job Title: {job_details.get('job_title', 'Unknown Title')}
    - Company Name: {job_details.get('company_name', 'Unknown Company')}
    - Job Description: {job_details.get('job_description', '')}
    - Required Skills: {", ".join(job_details.get('skills', []))}
    - Required Experience: {", ".join(job_details.get('experience', []))}
    - Software/Tools: {", ".join(job_details.get('software', []))}
    
    Base this cover letter on the user's existing letter/profile below, but personalize it specifically for the job above:
    
    {user_letter}
    
    Requirements:
    - Use today's date: {current_date}
    - Professional, engaging tone
    - Highlight relevant experience from user's background that matches the job requirements
    - Address specific skills and requirements mentioned in the job posting
    - Keep it concise (under 400 words)
    - Use the exact company name and job title from the job posting
    - Return only the cover letter text, no additional formatting
    
    DO NOT mention irrelevant companies like BrightData or proxy services.
    Focus only on the actual job and company from the posting.
    """

    client = get_openai_client()

    try:
        response = client.chat.completions.create(
            model="gpt-4-turbo",
            messages=[
                {"role": "system", "content": "You are a professional cover letter writer. Create personalized, engaging cover letters that highlight relevant experience for specific job postings. Return only the cover letter text, no markdown formatting."},
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
