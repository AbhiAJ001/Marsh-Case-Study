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

    # Generate content (with retry for rate limits)
    import time
    from google.api_core.exceptions import ResourceExhausted

    max_retries = 3
    response = None
    for attempt in range(max_retries):
        try:
            response = model.generate_content(
                prompt,
                generation_config=genai.GenerationConfig(
                    temperature=0.3,
                    max_output_tokens=2048,
                ),
            )
            break
        except ResourceExhausted:
            if attempt == max_retries - 1:
                raise RuntimeError(
                    "Gemini API rate limit reached. The free tier allows 20 requests/day. "
                    "Please wait a few minutes and try again."
                )
            wait = 35
            print(f"Rate limit hit in profile gen, waiting {wait}s... (Attempt {attempt+1}/{max_retries})")
            time.sleep(wait)

    # Parse JSON from response
    text = response.text.strip()

    # Clean up common markdown code fences
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
        # Try to extract JSON object from surrounding text
        start = text.find("{")
        end = text.rfind("}") + 1
        if start >= 0 and end > start:
            profile = json.loads(text[start:end])
        else:
            raise ValueError(
                f"Could not parse a profile for '{company_name}'. "
                "The model returned a non-JSON response. Please check the company name and try again."
            )

    return profile
