"""
Google Gemini AI Service for Mansa Jobs Backend
Provides secure AI-powered features with rate limiting and caching
"""

import os
import json
import logging
import google.generativeai as genai
from typing import Dict, List, Optional, Any
from django.core.cache import cache

logger = logging.getLogger(__name__)

# Configure Gemini API
GOOGLE_AI_API_KEY = os.getenv('GOOGLE_AI_API_KEY', '')

if not GOOGLE_AI_API_KEY:
    logger.error('GOOGLE_AI_API_KEY environment variable is not set')
else:
    genai.configure(api_key=GOOGLE_AI_API_KEY)
    logger.info('Gemini AI service configured successfully')

# Model configuration
GENERATION_CONFIG = {
    "temperature": 0.7,
    "top_p": 0.8,
    "top_k": 40,
    "max_output_tokens": 2048,
}

# Cache timeouts (in seconds)
CACHE_TIMEOUT_SHORT = 3600  # 1 hour for dynamic content
CACHE_TIMEOUT_LONG = 86400  # 24 hours for static content


def _extract_json(text: str) -> Optional[Dict]:
    """Extract JSON object from AI response text"""
    try:
        # Try to find JSON in markdown code blocks
        if '```json' in text:
            start = text.find('```json') + 7
            end = text.find('```', start)
            text = text[start:end].strip()
        elif '```' in text:
            start = text.find('```') + 3
            end = text.find('```', start)
            text = text[start:end].strip()
        
        # Try to extract JSON object or array
        if text.startswith('{'):
            end = text.rfind('}') + 1
            text = text[:end]
        elif text.startswith('['):
            end = text.rfind(']') + 1
            text = text[:end]
        
        return json.loads(text)
    except (json.JSONDecodeError, ValueError, AttributeError) as e:
        logger.error(f'Failed to extract JSON: {e}')
        return None


def _generate_content(prompt: str) -> str:
    """
    Generate content using Gemini AI
    
    Args:
        prompt: The prompt to send to Gemini
        
    Returns:
        Generated text response
        
    Raises:
        Exception: If AI generation fails
    """
    try:
        model = genai.GenerativeModel('gemini-pro')
        response = model.generate_content(
            prompt,
            generation_config=GENERATION_CONFIG
        )
        return response.text
    except Exception as e:
        logger.error(f'Gemini AI generation error: {e}')
        raise Exception(f'AI generation failed: {str(e)}')


def parse_resume(resume_text: str) -> Dict[str, Any]:
    """
    Parse resume text and extract structured data
    
    Args:
        resume_text: Raw resume text content
        
    Returns:
        Structured resume data dictionary
        
    Raises:
        Exception: If parsing fails
    """
    if not resume_text or len(resume_text.strip()) < 50:
        raise ValueError('Resume text is too short or empty')
    
    # Check cache first
    cache_key = f'resume_parse_{hash(resume_text)}'
    cached_result = cache.get(cache_key)
    if cached_result:
        logger.info('Returning cached resume parse result')
        return cached_result
    
    prompt = f"""Parse the following resume and extract structured data. Return ONLY valid JSON with no markdown formatting.

Resume:
{resume_text}

Return JSON in this exact format:
{{
  "name": "Full Name",
  "email": "email@example.com",
  "phone": "+1234567890",
  "location": "City, Country",
  "headline": "Professional Title",
  "summary": "Brief professional summary",
  "skills": ["skill1", "skill2"],
  "experience": [
    {{
      "company": "Company Name",
      "role": "Job Title",
      "startDate": "2020-01",
      "endDate": "2023-12",
      "description": "Job description"
    }}
  ],
  "education": [
    {{
      "institution": "University Name",
      "degree": "Degree Name",
      "field": "Field of Study",
      "year": "2020"
    }}
  ]
}}"""

    result = _generate_content(prompt)
    parsed_data = _extract_json(result)
    
    if not parsed_data:
        raise Exception('Could not parse resume data from AI response')
    
    # Validate required fields
    required_fields = ['name', 'email', 'skills']
    for field in required_fields:
        if field not in parsed_data:
            parsed_data[field] = '' if field != 'skills' else []
    
    # Cache the result
    cache.set(cache_key, parsed_data, CACHE_TIMEOUT_SHORT)
    
    return parsed_data


def calculate_job_match(candidate_profile: Dict[str, Any], job_requirements: Dict[str, Any]) -> Dict[str, Any]:
    """
    Calculate match score between candidate and job
    
    Args:
        candidate_profile: Dictionary with candidate info (skills, experience, location, salary)
        job_requirements: Dictionary with job info (title, skills, experience, location, salary)
        
    Returns:
        Match analysis dictionary with score, matched skills, gaps, and recommendations
        
    Raises:
        Exception: If calculation fails
    """
    # Validate inputs
    if not candidate_profile.get('skills') or not job_requirements.get('skills'):
        raise ValueError('Both candidate and job must have skills defined')
    
    # Create cache key from both profiles
    cache_key = f'job_match_{hash(str(candidate_profile))}_{hash(str(job_requirements))}'
    cached_result = cache.get(cache_key)
    if cached_result:
        logger.info('Returning cached job match result')
        return cached_result
    
    prompt = f"""Analyze the match between this candidate and job. Return ONLY valid JSON.

CANDIDATE:
Skills: {', '.join(candidate_profile.get('skills', []))}
Experience: {candidate_profile.get('yearsExperience', 0)} years
Location: {candidate_profile.get('location', 'Not specified')}
Desired Salary: {candidate_profile.get('desiredSalary', 'Not specified')}

JOB REQUIREMENTS:
Title: {job_requirements.get('title', 'Not specified')}
Required Skills: {', '.join(job_requirements.get('skills', []))}
Experience: {job_requirements.get('experienceLevel', 'Not specified')}
Location: {job_requirements.get('location', 'Not specified')}
Salary Range: {job_requirements.get('salaryRange', 'Not specified')}

Return JSON:
{{
  "matchScore": 85,
  "skillsMatch": ["matched skill 1", "matched skill 2"],
  "missingSkills": ["missing skill 1"],
  "recommendation": "Brief recommendation",
  "strengths": ["strength 1", "strength 2"],
  "gaps": ["gap 1"]
}}"""

    result = _generate_content(prompt)
    match_data = _extract_json(result)
    
    if not match_data:
        raise Exception('Could not calculate job match from AI response')
    
    # Ensure matchScore is present and valid
    if 'matchScore' not in match_data:
        match_data['matchScore'] = 50
    
    # Cache the result
    cache.set(cache_key, match_data, CACHE_TIMEOUT_SHORT)
    
    return match_data


def generate_job_description(job_info: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate professional job description from basic info
    
    Args:
        job_info: Dictionary with title, company, location, type, requirements
        
    Returns:
        Generated job description dictionary
        
    Raises:
        Exception: If generation fails
    """
    if not job_info.get('title'):
        raise ValueError('Job title is required')
    
    # Check cache
    cache_key = f'job_desc_{hash(str(job_info))}'
    cached_result = cache.get(cache_key)
    if cached_result:
        logger.info('Returning cached job description')
        return cached_result
    
    prompt = f"""Generate a professional job description. Return ONLY valid JSON.

JOB INFO:
Title: {job_info.get('title', '')}
Company: {job_info.get('company', 'Our Company')}
Location: {job_info.get('location', 'Remote')}
Type: {job_info.get('type', 'Full-time')}
Key Requirements: {', '.join(job_info.get('requirements', []))}

Return JSON:
{{
  "title": "Job Title",
  "description": "2-3 paragraph job description",
  "responsibilities": ["responsibility 1", "responsibility 2", "responsibility 3", "responsibility 4", "responsibility 5"],
  "requirements": ["requirement 1", "requirement 2", "requirement 3", "requirement 4", "requirement 5"],
  "benefits": ["benefit 1", "benefit 2", "benefit 3", "benefit 4"],
  "skills": ["skill 1", "skill 2", "skill 3"]
}}"""

    result = _generate_content(prompt)
    job_desc = _extract_json(result)
    
    if not job_desc:
        raise Exception('Could not generate job description from AI response')
    
    # Cache the result
    cache.set(cache_key, job_desc, CACHE_TIMEOUT_LONG)
    
    return job_desc


def parse_search_query(query: str) -> Dict[str, Any]:
    """
    Parse natural language search query into structured filters
    
    Args:
        query: Natural language search string
        
    Returns:
        Dictionary of search filters
        
    Raises:
        Exception: If parsing fails
    """
    if not query or len(query.strip()) < 2:
        raise ValueError('Search query is too short')
    
    # Check cache
    cache_key = f'search_parse_{hash(query)}'
    cached_result = cache.get(cache_key)
    if cached_result:
        logger.info('Returning cached search parse result')
        return cached_result
    
    prompt = f"""Parse this job search query and extract filters. Return ONLY valid JSON.

Query: "{query}"

Return JSON:
{{
  "keywords": ["keyword1", "keyword2"],
  "location": "City or Remote",
  "jobType": "full_time or part_time or contract or remote",
  "experienceLevel": "entry or mid or senior",
  "salaryMin": 50000,
  "salaryMax": 100000,
  "skills": ["skill1", "skill2"]
}}

Use null for fields that cannot be determined from the query."""

    result = _generate_content(prompt)
    filters = _extract_json(result)
    
    if not filters:
        # Fallback to basic keyword parsing
        filters = {
            'keywords': query.split(),
            'location': None,
            'jobType': None,
            'experienceLevel': None,
            'salaryMin': None,
            'salaryMax': None,
            'skills': []
        }
    
    # Cache the result
    cache.set(cache_key, filters, CACHE_TIMEOUT_LONG)
    
    return filters


def generate_interview_questions(role: str, skills: List[str], experience_level: str) -> List[Dict[str, str]]:
    """
    Generate interview questions for a specific role
    
    Args:
        role: Job role/title
        skills: List of required skills
        experience_level: Entry, mid, senior, etc.
        
    Returns:
        List of interview question dictionaries
        
    Raises:
        Exception: If generation fails
    """
    if not role:
        raise ValueError('Role is required')
    
    # Check cache
    cache_key = f'interview_{hash(role)}_{hash(str(skills))}_{experience_level}'
    cached_result = cache.get(cache_key)
    if cached_result:
        logger.info('Returning cached interview questions')
        return cached_result
    
    prompt = f"""Generate 10 interview questions for this role. Return ONLY valid JSON array.

Role: {role}
Skills: {', '.join(skills)}
Experience Level: {experience_level}

Return JSON array:
[
  {{
    "question": "Question text",
    "type": "technical or behavioral or situational",
    "difficulty": "easy or medium or hard",
    "tips": "Answer tips"
  }}
]"""

    result = _generate_content(prompt)
    
    # Extract JSON array
    try:
        if '[' in result:
            start = result.find('[')
            end = result.rfind(']') + 1
            json_str = result[start:end]
            questions = json.loads(json_str)
        else:
            questions = []
    except (json.JSONDecodeError, ValueError):
        logger.error('Failed to parse interview questions')
        questions = []
    
    # Cache the result
    cache.set(cache_key, questions, CACHE_TIMEOUT_LONG)
    
    return questions


def get_salary_insights(role: str, location: str, experience_level: str) -> Dict[str, Any]:
    """
    Get salary insights for a role in a specific location
    
    Args:
        role: Job role/title
        location: Geographic location
        experience_level: Experience level
        
    Returns:
        Salary insight dictionary with ranges and trends
        
    Raises:
        Exception: If generation fails
    """
    if not role:
        raise ValueError('Role is required')
    
    # Check cache
    cache_key = f'salary_{hash(role)}_{hash(location)}_{experience_level}'
    cached_result = cache.get(cache_key)
    if cached_result:
        logger.info('Returning cached salary insights')
        return cached_result
    
    prompt = f"""Provide salary insights for this role in Africa. Return ONLY valid JSON.

Role: {role}
Location: {location}
Experience: {experience_level}

Return JSON (amounts in USD):
{{
  "role": "Role Name",
  "location": "Location",
  "currency": "USD",
  "salaryRange": {{
    "min": 40000,
    "median": 60000,
    "max": 90000
  }},
  "factors": ["factor affecting salary 1", "factor 2"],
  "marketTrend": "growing or stable or declining",
  "demandLevel": "high or medium or low"
}}"""

    result = _generate_content(prompt)
    insights = _extract_json(result)
    
    if not insights:
        raise Exception('Could not get salary insights from AI response')
    
    # Cache the result (longer timeout for salary data)
    cache.set(cache_key, insights, CACHE_TIMEOUT_LONG)
    
    return insights
