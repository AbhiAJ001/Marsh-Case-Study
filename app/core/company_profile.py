"""
Company Profile Generator — Researches a company using Gemini + web search
and creates a structured profile for insurance pitch targeting.
"""

import json
import google.generativeai as genai
from ..config import get_config
from ..utils.prompts import COMPANY_PROFILE_PROMPT


def generate_company_profile(company_name: str) -> dict:
    """Research a company and generate a structured profile.
    
    Uses Gemini with grounding (Google Search) for real-time company data.
    
    Args:
        company_name: Name of the company to research
    
    Returns:
        Dict with company profile fields (industry, size, risks, needs, etc.)
    """
    config = get_config()
    genai.configure(api_key=config["GOOGLE_API_KEY"])

    model = genai.GenerativeModel("gemini-3.8-flash")

    prompt = COMPANY_PROFILE_PROMPT.format(company_name=company_name)

    # Generate content
    response = model.generate_content(
        prompt,
        generation_config=genai.GenerationConfig(
            temperature=0.3,
            max_output_tokens=2048,
        ),
    )

    # Parse JSON from response
    text = response.text.strip()
    
    # Clean up common issues
    if text.startswith("```json"):
        text = text[7:]
    if text.startswith("```"):
        text = text[3:]
    if text.endswith("```"):
        text = text[:-3]
    text = text.strip()

    try:
        profile = json.loads(text)
    except json.JSONDecodeError:
        # Try to find JSON in the response
        start = text.find("{")
        end = text.rfind("}") + 1
        if start >= 0 and end > start:
            profile = json.loads(text[start:end])
        else:
            profile = {
                "company_name": company_name,
                "industry": "Unknown",
                "description": "Could not parse company profile. Please try again.",
                "assumptions": ["ASSUMED: Company data could not be retrieved"],
                "key_risks": [],
                "insurance_needs": [],
                "error": True,
            }

    return profile
