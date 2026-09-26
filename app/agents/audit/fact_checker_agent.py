"""
Fact-Checker Agent — Verifies pitch claims against OKF source knowledge.

Strategy: Instead of one massive audit prompt (which overflows Groq's TPM),
we audit SLIDE BY SLIDE. Each micro-audit is a small, focused LLM call
(~1,000 tokens input + 400 tokens output) that fits comfortably within limits.

Results are merged into a single audit report.
"""

import json
from ..base_agent import BaseAgent, AgentResult


# ── Compact micro-audit prompt (one slide at a time) ─────────────────────────

MICRO_AUDIT_PROMPT = """You are a compliance auditor. Check the slide bullets below against the policy knowledge.

POLICY KNOWLEDGE (ground truth):
{okf_context}

SLIDE TO AUDIT (Slide {slide_number} — {slide_title}):
{bullets}

Return ONLY this JSON (no markdown):
{{
  "slide_number": {slide_number},
  "claims": [
    {{
      "claim_text": "exact bullet text",
      "status": "VERIFIED",
      "confidence": 0.9,
      "notes": "brief note"
    }}
  ]
}}

Status values: VERIFIED (in source) | UNVERIFIED (not found) | INACCURATE (contradicts source) | ASSUMPTION (inferred)
Be brief. One object per bullet point.
"""


class FactCheckerAgent(BaseAgent):
    """
    Audits a pitch slide-by-slide with compact micro-prompts.
    Each slide is a separate LLM call so no single request overflows the TPM limit.
    """

    name        = "FactCheckerAgent"
    temperature = 0.1
    max_tokens  = 600     # Small — just claim objects for one slide

    def build_prompt(self, **inputs) -> str:
        # Not used — we use custom run() below
        return ""

    def parse_output(self, text: str, **_) -> dict:
        try:
            return self._parse_json(text)
        except Exception:
            return {"claims": []}

    def _audit_one_slide(self, slide: dict, okf_context: str) -> list:
        """Audit a single slide and return its claim list."""
        bullets = slide.get("bullets", [])
        if not bullets:
            return []

        bullets_text = "\n".join(f"- {b}" for b in bullets)
        prompt = MICRO_AUDIT_PROMPT.format(
            okf_context=okf_context[:1200],          # ~300 tokens
            slide_number=slide.get("slide_number", "?"),
            slide_title=slide.get("title", ""),
            bullets=bullets_text,
        )

        try:
            llm_out = self._call_llm(prompt)
            result  = self._parse_json(llm_out["text"])
            return result.get("claims", [])
        except Exception as e:
            self._log(f"Slide {slide.get('slide_number')} audit failed: {e}")
            # Return unverified claims for this slide so we don't lose them
            return [
                {
                    "claim_text": b,
                    "status":     "UNVERIFIED",
                    "confidence": 0.5,
                    "notes":      "Could not verify — review manually",
                }
                for b in bullets
            ]

    def run(self, pitch: dict, okf_context: str) -> "AgentResult":
        self._log("Starting slide-by-slide audit...")

        slides      = pitch.get("slides", [])
        all_claims  = []
        model_used  = "unknown"

        for slide in slides:
            self._log(f"Auditing slide {slide.get('slide_number', '?')}: {slide.get('title', '')}")
            claims = self._audit_one_slide(slide, okf_context)
            all_claims.extend(claims)

        # Aggregate statistics
        total     = len(all_claims)
        verified  = sum(1 for c in all_claims if c.get("status") == "VERIFIED")
        flagged   = sum(1 for c in all_claims if c.get("status") in ("INACCURATE", "UNVERIFIED"))

        if total == 0:
            summary = "PASS_WITH_NOTES"
        elif flagged == 0:
            summary = "PASS"
        elif flagged / total < 0.3:
            summary = "PASS_WITH_NOTES"
        else:
            summary = "FAIL"

        recommendations = []
        if any(c.get("status") == "INACCURATE" for c in all_claims):
            recommendations.append("Review INACCURATE claims — they contradict source policy documents.")
        if any(c.get("status") == "UNVERIFIED" for c in all_claims):
            recommendations.append("UNVERIFIED claims could not be confirmed in OKF sources — validate before presenting.")
        if not recommendations:
            recommendations.append("All audited claims align with source policy documents.")

        audit = {
            "audit_summary":   summary,
            "total_claims":    total,
            "verified_claims": verified,
            "flagged_claims":  flagged,
            "claims":          all_claims,
            "recommendations": recommendations,
            "_model_used":     model_used,
        }

        self._log(f"Audit complete: {total} claims, {verified} verified, {flagged} flagged. Summary: {summary}")
        return AgentResult(
            agent_name=self.name,
            data=audit,
            model_used=model_used,
        )
