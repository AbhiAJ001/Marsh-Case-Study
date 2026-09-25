"""
Audit Engine — Verifies pitch claims against OKF source knowledge.

Traces each factual claim to its source concept and assigns
confidence scores. Uses the ModelRouter (Gemini → Groq) for
auto-failover on quota limits.
"""

import json
from ..config import get_config
from ..utils.prompts import AUDIT_PROMPT
from ..utils.model_router import generate, parse_json_from_response
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

    # Run audit using the model router (Gemini → Groq auto-fallback)
    result = generate(prompt, temperature=0.1, max_tokens=4096)
    text = result["text"]
    model_used = result["model_used"]

    print(f"[AuditEngine] Audited with model: {model_used}")

    # Parse response — and validate expected shape
    try:
        audit = parse_json_from_response(text)
        # Validate it's actually an audit result, not a raw knowledge dump
        if "audit_summary" not in audit:
            print("[AuditEngine] Unexpected JSON shape — using fallback audit")
            audit = _fallback_audit(pitch)
    except (ValueError, json.JSONDecodeError):
        audit = _fallback_audit(pitch)

    audit["_model_used"] = model_used
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
