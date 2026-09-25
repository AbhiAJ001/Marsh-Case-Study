"""
Company Profile Generator — Researches a company using the model router.
Tries Gemini first, auto-falls back to Groq on quota errors.
"""

from ..utils.prompts import COMPANY_PROFILE_PROMPT
from ..utils.model_router import generate, parse_json_from_response


def generate_company_profile(company_name: str) -> dict:
    """Research a company and generate a structured profile.

    Uses the ModelRouter (Gemini → Groq Llama → Groq Gemma) so the app
    never goes dark because of a single provider's quota limit.

    Args:
        company_name: Name of the company to research

    Returns:
        Dict with company profile fields (industry, size, risks, needs, etc.)
    """
    prompt = COMPANY_PROFILE_PROMPT.format(company_name=company_name)

    result = generate(prompt, temperature=0.3, max_tokens=2048)
    text = result["text"]
    model_used = result["model_used"]

    print(f"[CompanyProfile] Generated with model: {model_used}")

    try:
        profile = parse_json_from_response(text)
    except ValueError as e:
        raise ValueError(
            f"Could not parse a profile for '{company_name}'. "
            f"Model ({model_used}) returned non-JSON. Error: {e}"
        )

    profile["_model_used"] = model_used
    return profile
