"""
Slide Writer Agents — Specialised agents, one per slide type.

Each agent writes exactly ONE slide of the pitch deck with its own
focused prompt and only the context it needs. No more truncation.

Slide types:
  1. ExecutiveSummaryAgent   — who the company is + why insurance now
  2. RiskAlignmentAgent      — company risks mapped to policy coverage
  3. PolicyComparisonAgent   — comparing selected policies side by side
  4. ROIValueAgent           — cost/benefit and value proposition
  5. CallToActionAgent       — next steps and recommended policy
"""

import json
from ..base_agent import BaseAgent, AgentResult


# ── Shared prompt template ────────────────────────────────────────────────────

_SLIDE_SYSTEM = """You are a senior insurance advisor at Marsh writing one slide of a pitch deck.
Write ONLY the JSON for this single slide. No markdown, no code fences, no extra text.

Company: {company_name} | Industry: {industry}
Selected Policies: {policy_names}

Policy Knowledge:
{context}

Respond in EXACTLY this JSON format:
{{
    "slide_number": {slide_number},
    "title": "slide title — specific to this company, not generic",
    "subtitle": "optional one-line subtitle",
    "bullets": ["bullet 1 with specific detail", "bullet 2", "bullet 3"],
    "speaker_notes": "what the advisor says presenting this slide (2-3 sentences)",
    "source_concepts": ["concept names used for this slide"]
}}
"""


# ── 1. Executive Summary Slide ───────────────────────────────────────────────

class ExecutiveSummaryAgent(BaseAgent):
    """Slide 1 — Who the company is and why they need insurance today."""

    name        = "ExecutiveSummaryAgent"
    temperature = 0.3
    max_tokens  = 600
    task_type   = "pitch"   # → OpenRouter/NVIDIA first (best creative JSON)

    def build_prompt(self, company_profile: dict, policy_contexts: list, **_) -> str:
        company_name  = company_profile.get("company_name", "the company")
        industry      = company_profile.get("industry", "")
        description   = company_profile.get("description", "")
        key_risks     = company_profile.get("key_risks", [])
        policy_names  = ", ".join(c["policy_name"] for c in policy_contexts)
        context       = "\n".join(c["context_text"][:400] for c in policy_contexts[:2])

        return _SLIDE_SYSTEM.format(
            company_name=company_name, industry=industry,
            policy_names=policy_names, context=context, slide_number=1
        ) + f"""
Focus for this slide:
- Introduce {company_name}: {description}
- State the core risk landscape: {'; '.join(key_risks[:3])}
- Opening hook — why this meeting matters for {company_name} right now.
"""

    def parse_output(self, text: str, **_) -> dict:
        try:
            return self._parse_json(text)
        except Exception:
            return {"slide_number": 1, "title": "Executive Summary",
                    "bullets": ["Company overview and insurance need"], "speaker_notes": "", "source_concepts": []}


# ── 2. Risk Alignment Slide ───────────────────────────────────────────────────

class RiskAlignmentAgent(BaseAgent):
    """Slide 2 — Maps company-specific risks to policy coverage features."""

    name        = "RiskAlignmentAgent"
    temperature = 0.25
    max_tokens  = 700
    task_type   = "pitch"   # → OpenRouter/NVIDIA first (best structured JSON)

    def build_prompt(self, company_profile: dict, policy_contexts: list, **_) -> str:
        company_name = company_profile.get("company_name", "the company")
        industry     = company_profile.get("industry", "")
        key_risks    = company_profile.get("key_risks", [])
        ins_needs    = company_profile.get("insurance_needs", [])
        policy_names = ", ".join(c["policy_name"] for c in policy_contexts)
        context      = "\n".join(c["context_text"][:500] for c in policy_contexts[:3])

        return _SLIDE_SYSTEM.format(
            company_name=company_name, industry=industry,
            policy_names=policy_names, context=context, slide_number=2
        ) + f"""
Focus for this slide:
- For each of these company risks, name the exact policy feature that covers it:
  Risks: {json.dumps(key_risks)}
  Needs: {json.dumps(ins_needs)}
- Each bullet = "Risk X → Covered by [Policy Feature Name]"
- Use ONLY features mentioned in the Policy Knowledge above.
"""

    def parse_output(self, text: str, **_) -> dict:
        try:
            return self._parse_json(text)
        except Exception:
            return {"slide_number": 2, "title": "Risk Coverage Alignment",
                    "bullets": ["Key risks addressed by selected policies"], "speaker_notes": "", "source_concepts": []}


# ── 3. Policy Comparison Slide ────────────────────────────────────────────────

class PolicyComparisonAgent(BaseAgent):
    """Slide 3 — Side-by-side comparison of selected policies."""

    name        = "PolicyComparisonAgent"
    temperature = 0.2
    max_tokens  = 700
    task_type   = "pitch"   # → OpenRouter/NVIDIA first (best structured JSON)

    def build_prompt(self, company_profile: dict, policy_contexts: list, **_) -> str:
        company_name = company_profile.get("company_name", "the company")
        industry     = company_profile.get("industry", "")
        policy_names = ", ".join(c["policy_name"] for c in policy_contexts)
        context      = "\n".join(
            f"=== {c['policy_name']} ===\n{c['context_text'][:350]}"
            for c in policy_contexts
        )

        return _SLIDE_SYSTEM.format(
            company_name=company_name, industry=industry,
            policy_names=policy_names, context=context, slide_number=3
        ) + """
Focus for this slide:
- Compare the selected policies on 3-4 key dimensions
  (e.g. sum insured range, unique feature, ideal company type, pricing tier)
- Each bullet = one differentiating dimension across policies
- End with which policy best fits this company and why (one bullet)
- Use ONLY data from the Policy Knowledge provided.
"""

    def parse_output(self, text: str, **_) -> dict:
        try:
            return self._parse_json(text)
        except Exception:
            return {"slide_number": 3, "title": "Policy Comparison",
                    "bullets": ["Comparison of selected policies"], "speaker_notes": "", "source_concepts": []}


# ── 4. ROI & Value Slide ──────────────────────────────────────────────────────

class ROIValueAgent(BaseAgent):
    """Slide 4 — Return on investment and business value of coverage."""

    name        = "ROIValueAgent"
    temperature = 0.3
    max_tokens  = 600
    task_type   = "pitch"   # → OpenRouter/NVIDIA first (best structured JSON)

    def build_prompt(self, company_profile: dict, policy_contexts: list, **_) -> str:
        company_name = company_profile.get("company_name", "the company")
        industry     = company_profile.get("industry", "")
        size         = company_profile.get("estimated_size", "mid-size")
        employees    = company_profile.get("estimated_employees", "100-500")
        policy_names = ", ".join(c["policy_name"] for c in policy_contexts)
        context      = "\n".join(c["context_text"][:400] for c in policy_contexts[:2])

        return _SLIDE_SYSTEM.format(
            company_name=company_name, industry=industry,
            policy_names=policy_names, context=context, slide_number=4
        ) + f"""
Focus for this slide:
- Company size: {size} | Employees: {employees}
- Quantify the value: employee retention, reduced absenteeism, tax benefits
- Mention specific policy perks that deliver financial ROI
  (e.g. wellness rewards, cashless hospitalisation, claim protect)
- Keep language business-focused, not medical/clinical
"""

    def parse_output(self, text: str, **_) -> dict:
        try:
            return self._parse_json(text)
        except Exception:
            return {"slide_number": 4, "title": "Business Value",
                    "bullets": ["ROI and value proposition"], "speaker_notes": "", "source_concepts": []}


# ── 5. Call to Action Slide ───────────────────────────────────────────────────

class CallToActionAgent(BaseAgent):
    """Slide 5 — Recommended policy and next steps."""

    name        = "CallToActionAgent"
    temperature = 0.35
    max_tokens  = 500
    task_type   = "pitch"   # → OpenRouter/NVIDIA first (best structured JSON)

    def build_prompt(self, company_profile: dict, policy_contexts: list, **_) -> str:
        company_name  = company_profile.get("company_name", "the company")
        industry      = company_profile.get("industry", "")
        pitch_angle   = company_profile.get("pitch_angle", "")
        policy_names  = ", ".join(c["policy_name"] for c in policy_contexts)
        best_policy   = policy_contexts[0]["policy_name"] if policy_contexts else "recommended policy"
        context       = policy_contexts[0]["context_text"][:300] if policy_contexts else ""

        return _SLIDE_SYSTEM.format(
            company_name=company_name, industry=industry,
            policy_names=policy_names, context=context, slide_number=5
        ) + f"""
Focus for this slide:
- Recommend: {best_policy} as the primary choice for {company_name}
- Pitch angle: {pitch_angle}
- Bullets: 1) recommended policy + one-line rationale, 2) next step (quote/meeting),
           3) Marsh's support commitment, 4) urgency or timing hook
- Closing must feel confident and action-oriented.
"""

    def parse_output(self, text: str, **_) -> dict:
        try:
            return self._parse_json(text)
        except Exception:
            return {"slide_number": 5, "title": "Next Steps",
                    "bullets": ["Contact Marsh to get started"], "speaker_notes": "", "source_concepts": []}
