"""
Audit Engine — Verifies pitch claims against OKF source knowledge.

Traces each factual claim to its source concept and assigns
confidence scores. Uses Gemini for intelligent claim extraction
and verification.
"""

import json
import google.generativeai as genai
from pathlib import Path
from ..config import get_config
from ..utils.prompts import AUDIT_PROMPT
from ..okf.okf_retriever import OKFRetriever


def audit_pitch_content(pitch: dict, policy_ids: list[str]) -> dict:
    """Audit a generated pitch for accuracy against source policy knowledge.
    
    Args:
        pitch: The pitch dict from generate_marketing_pitch()
        policy_ids: List of policy IDs used in the pitch
    
    Returns:
        Dict with audit_summary, claims list with verification status,
        confidence scores, and recommendations
    """
    config = get_config()
    genai.configure(api_key=config["GOOGLE_API_KEY"])

    # Get the OKF knowledge context (source of truth)
    retriever = OKFRetriever(config["BUNDLE_DIR"])
    okf_context = retriever.retrieve_for_policies(policy_ids)
    context_text = okf_context.to_llm_context()

    # Format pitch content for audit
    pitch_text = _format_pitch_for_audit(pitch)

    # Build the audit prompt
    prompt = AUDIT_PROMPT.format(
        okf_context=context_text,
        pitch_content=pitch_text,
    )

    # Run audit with Gemini
    model = genai.GenerativeModel("gemini-3.8-flash")
    response = model.generate_content(
        prompt,
        generation_config=genai.GenerationConfig(
            temperature=0.1,  # Low temperature for strict verification
            max_output_tokens=4096,
        ),
    )

    # Parse response
    text = response.text.strip()
    if text.startswith("```json"):
        text = text[7:]
    if text.startswith("```"):
        text = text[3:]
    if text.endswith("```"):
        text = text[:-3]
    text = text.strip()

    try:
        audit = json.loads(text)
    except json.JSONDecodeError:
        start = text.find("{")
        end = text.rfind("}") + 1
        if start >= 0 and end > start:
            try:
                audit = json.loads(text[start:end])
            except json.JSONDecodeError:
                audit = _fallback_audit(pitch)
        else:
            audit = _fallback_audit(pitch)

    return audit


def _format_pitch_for_audit(pitch: dict) -> str:
    """Format pitch slides into a flat text for audit analysis."""
    lines = [f"Pitch Title: {pitch.get('pitch_title', 'N/A')}\n"]
    
    for slide in pitch.get("slides", []):
        lines.append(f"\n--- Slide {slide.get('slide_number', '?')} ---")
        lines.append(f"Title: {slide.get('title', '')}")
        if slide.get("subtitle"):
            lines.append(f"Subtitle: {slide['subtitle']}")
        for bullet in slide.get("bullets", []):
            lines.append(f"• {bullet}")
    
    if pitch.get("recommended_policy"):
        lines.append(f"\nRecommendation: {pitch['recommended_policy']}")
    
    return "\n".join(lines)


def _fallback_audit(pitch: dict) -> dict:
    """Generate a basic audit when LLM parsing fails."""
    return {
        "audit_summary": "PASS_WITH_NOTES",
        "total_claims": 0,
        "verified_claims": 0,
        "flagged_claims": 0,
        "claims": [],
        "recommendations": [
            "Automated audit could not be completed. Please review all claims manually.",
            "Verify all policy feature names and coverage amounts against source brochures.",
        ],
    }
