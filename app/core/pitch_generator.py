"""
Pitch Generator — Creates tailored marketing pitches using company profile
and OKF knowledge context, with LangChain fallback for additional context.
Uses the ModelRouter (Gemini → Groq) for auto-failover on quota limits.
"""

import json
from ..config import get_config
from ..utils.prompts import PITCH_GENERATION_PROMPT
from ..utils.model_router import generate, parse_json_from_response
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

    # 1. Retrieve policy knowledge from OKF bundle (PRIMARY)
    retriever = OKFRetriever(config["BUNDLE_DIR"])

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

    # 4. Generate using the model router (Gemini → Groq auto-fallback)
    result = generate(prompt, temperature=0.4, max_tokens=4096)
    text = result["text"]
    model_used = result["model_used"]

    print(f"[PitchGenerator] Generated with model: {model_used}")

    # 5. Parse response
    try:
        pitch = parse_json_from_response(text)
    except (ValueError, json.JSONDecodeError):
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

    # 6. Attach metadata for audit use
    pitch["_source_map"]       = okf_context.get_source_map()
    pitch["_policy_ids"]       = policy_ids
    pitch["_company_profile"]  = company_profile
    pitch["_model_used"]       = model_used

    return pitch
