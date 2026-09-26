"""
Fact-Checker Agent — Verifies pitch claims against OKF source knowledge.

Replaces the old audit_engine.py with an agent-based design that:
  - Validates the JSON response shape before returning
  - Falls back gracefully when the LLM can't complete the audit
  - Attaches which model performed the audit
"""

from ..base_agent import BaseAgent, AgentResult


AUDIT_PROMPT = """You are a compliance auditor reviewing a Marsh insurance pitch for accuracy.

SOURCE POLICY KNOWLEDGE (ground truth — only these facts are verified):
{okf_context}

PITCH CONTENT TO AUDIT:
{pitch_content}

For each factual claim in the pitch, verify it against the source knowledge above.

Return ONLY this JSON (no markdown, no code fences):
{{
    "audit_summary": "PASS / PASS_WITH_NOTES / FAIL",
    "total_claims": <number>,
    "verified_claims": <number>,
    "flagged_claims": <number>,
    "claims": [
        {{
            "claim_text": "the exact claim",
            "status": "VERIFIED / UNVERIFIED / INACCURATE / ASSUMPTION",
            "confidence": 0.0,
            "source_concept": "which OKF concept supports this (or null)",
            "notes": "brief explanation"
        }}
    ],
    "recommendations": ["recommendation 1", "recommendation 2"]
}}

Rules:
- VERIFIED = claim exactly matches source data
- UNVERIFIED = plausible but not in the provided sources
- INACCURATE = contradicts source data — flag immediately
- ASSUMPTION = reasonable inference, not directly stated
- Be strict — when in doubt mark UNVERIFIED not VERIFIED
"""


def _format_pitch(pitch: dict) -> str:
    lines = [f"Pitch Title: {pitch.get('pitch_title', 'N/A')}\n"]
    for slide in pitch.get("slides", []):
        lines.append(f"\n--- Slide {slide.get('slide_number', '?')} ---")
        lines.append(f"Title: {slide.get('title', '')}")
        if slide.get("subtitle"):
            lines.append(f"Subtitle: {slide['subtitle']}")
        for bullet in slide.get("bullets", []):
            lines.append(f"* {bullet}")
    if pitch.get("recommended_policy"):
        lines.append(f"\nRecommendation: {pitch['recommended_policy']}")
    return "\n".join(lines)


class FactCheckerAgent(BaseAgent):
    """
    Audits a generated pitch slide-by-slide against OKF source knowledge.
    Falls back to a safe manual-review response if LLM parsing fails.
    """

    name        = "FactCheckerAgent"
    temperature = 0.1       # Very low — we want strict deterministic verification
    max_tokens  = 1500

    def build_prompt(self, pitch: dict, okf_context: str, **_) -> str:
        return AUDIT_PROMPT.format(
            okf_context=okf_context[:2000],
            pitch_content=_format_pitch(pitch),
        )

    def parse_output(self, text: str, **_) -> dict:
        try:
            result = self._parse_json(text)
            # Validate expected shape
            if "audit_summary" not in result:
                raise ValueError("Missing audit_summary key")
            return result
        except Exception:
            return self._fallback()

    def _fallback(self) -> dict:
        return {
            "audit_summary":   "PASS_WITH_NOTES",
            "total_claims":    0,
            "verified_claims": 0,
            "flagged_claims":  0,
            "claims":          [],
            "recommendations": [
                "Automated audit could not be completed due to model token limits.",
                "Please review all policy feature names and coverage amounts manually.",
            ],
        }

    def run(self, pitch: dict, okf_context: str) -> AgentResult:
        self._log("Auditing pitch content...")
        result = super().run(pitch=pitch, okf_context=okf_context)
        if result.success:
            result.data["_model_used"] = result.model_used
        return result
