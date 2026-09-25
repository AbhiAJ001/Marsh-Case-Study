"""
Pitch Generator — Creates tailored marketing pitches using company profile
and OKF knowledge context, with LangChain fallback for additional context.
"""

import json
import google.generativeai as genai
from pathlib import Path
from ..config import get_config
from ..utils.prompts import PITCH_GENERATION_PROMPT
from ..okf.okf_retriever import OKFRetriever
from ..rag.langchain_fallback import LangChainFallback


def generate_marketing_pitch(company_profile: dict, policy_ids: list[str]) -> dict:
    """Generate a 3-5 slide marketing pitch grounded in OKF policy knowledge.
    
    Args:
        company_profile: Output from generate_company_profile()
        policy_ids: List of selected policy IDs (e.g. ["hdfc-optima-secure-plus"])
    
    Returns:
        Dict with pitch_title, slides, recommended_policy, key_differentiators
    """
    config = get_config()
    genai.configure(api_key=config["GOOGLE_API_KEY"])

    # 1. Retrieve policy knowledge from OKF bundle (PRIMARY)
    retriever = OKFRetriever(config["BUNDLE_DIR"])
    
    # Use company profile to inform retrieval
    company_needs = company_profile.get("insurance_needs", [])
    okf_context = retriever.retrieve_for_policies(policy_ids, company_needs)
    context_text = okf_context.to_llm_context()

    # 2. If OKF context is thin, supplement with LangChain fallback
    if okf_context.total_concepts < 5:
        fallback = LangChainFallback(config["PROJECT_ROOT"])
        if fallback.load():
            company_desc = company_profile.get("description", "")
            industry = company_profile.get("industry", "")
            fallback_text = fallback.search_for_context(
                f"{industry} insurance coverage benefits for {company_desc}",
                k=5
            )
            if fallback_text:
                context_text += "\n\n" + fallback_text

    # 3. Build the prompt
    policy_names = ", ".join(
        p["name"] for p in retriever.get_available_policies() 
        if p["id"] in policy_ids
    )

    prompt = PITCH_GENERATION_PROMPT.format(
        company_profile=json.dumps(company_profile, indent=2),
        okf_context=context_text,
        policy_names=policy_names,
    )

    # 4. Generate with Gemini
    model = genai.GenerativeModel("gemini-2.0-flash")
    response = model.generate_content(
        prompt,
        generation_config=genai.GenerationConfig(
            temperature=0.4,
            max_output_tokens=4096,
        ),
    )

    # 5. Parse response
    text = response.text.strip()
    if text.startswith("```json"):
        text = text[7:]
    if text.startswith("```"):
        text = text[3:]
    if text.endswith("```"):
        text = text[:-3]
    text = text.strip()

    try:
        pitch = json.loads(text)
    except json.JSONDecodeError:
        start = text.find("{")
        end = text.rfind("}") + 1
        if start >= 0 and end > start:
            pitch = json.loads(text[start:end])
        else:
            pitch = {
                "pitch_title": f"Insurance Proposal for {company_profile.get('company_name', 'Company')}",
                "target_company": company_profile.get("company_name", "Unknown"),
                "slides": [{
                    "slide_number": 1,
                    "title": "Error generating pitch",
                    "bullets": ["Please try again or adjust your inputs."],
                    "speaker_notes": "",
                    "source_concepts": [],
                }],
                "error": True,
            }

    # 6. Attach the source map for audit use
    pitch["_source_map"] = okf_context.get_source_map()
    pitch["_policy_ids"] = policy_ids
    pitch["_company_profile"] = company_profile

    return pitch
