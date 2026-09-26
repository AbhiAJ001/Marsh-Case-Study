"""
Research Agent — Generates a structured company profile using the LLM.

In future iterations this agent can be augmented with:
  - DuckDuckGo web search (pip install duckduckgo-search)
  - Wikipedia API lookup
  - LinkedIn scraper

For now it uses the ModelRouter (Gemini → Groq) to produce a detailed
profile from the LLM's training knowledge, while being explicit about
what is assumed vs. confirmed.
"""

import json
from ..base_agent import BaseAgent, AgentResult


RESEARCH_PROMPT = """You are an expert insurance industry research analyst at Marsh, one of the world's largest insurance brokers.

Research the company below and build a detailed profile for an insurance pitch.
Be specific and practical. Prefix any uncertain data with "ASSUMED:".

Company: {company_name}

Return ONLY this JSON (no markdown, no code fences):
{{
    "company_name": "{company_name}",
    "industry": "specific industry/sector",
    "sub_industry": "more specific sub-category",
    "estimated_size": "startup / small / mid-size / large / enterprise",
    "estimated_employees": "number range e.g. 50-200",
    "headquarters": "city, country",
    "description": "2-3 sentence company description",
    "key_risks": ["risk 1", "risk 2", "risk 3", "risk 4", "risk 5"],
    "insurance_needs": ["need 1", "need 2", "need 3", "need 4"],
    "employee_demographics": "brief description of likely workforce age and health profile",
    "pitch_angle": "1-2 sentences on the best angle to pitch insurance to this company",
    "assumptions": ["ASSUMED: item 1", "ASSUMED: item 2"]
}}
"""


class ResearchAgent(BaseAgent):
    """
    Researches a company and produces a structured profile dict.

    Replaces the old generate_company_profile() function but with the
    same output contract — so the rest of the pipeline is unchanged.
    """

    name        = "ResearchAgent"
    temperature = 0.3
    max_tokens  = 1200

    def build_prompt(self, company_name: str, **_) -> str:
        return RESEARCH_PROMPT.format(company_name=company_name)

    def parse_output(self, text: str, company_name: str = "", **_) -> dict:
        try:
            profile = self._parse_json(text)
        except (ValueError, Exception) as e:
            raise ValueError(
                f"Could not parse company profile for '{company_name}'. "
                f"The model returned non-JSON. Error: {e}"
            )

        # Guarantee required keys exist
        profile.setdefault("company_name",         company_name)
        profile.setdefault("industry",             "General Business")
        profile.setdefault("key_risks",            [])
        profile.setdefault("insurance_needs",      [])
        profile.setdefault("employee_demographics","General workforce")
        profile.setdefault("pitch_angle",          "Comprehensive health coverage for employees")
        profile.setdefault("assumptions",          [])
        return profile

    def run(self, company_name: str) -> AgentResult:
        self._log(f"Researching: {company_name}")
        result = super().run(company_name=company_name)
        if result.success:
            result.data["_model_used"] = result.model_used
        return result
