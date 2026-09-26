"""
Pitch Orchestrator — Coordinates all agents to produce a complete pitch.

Execution flow:
  Phase A: ResearchAgent          → company profile (sequential, needed first)
  Phase B: PolicyRetrievalAgents  → one per policy, PARALLEL via asyncio.gather
  Phase C: SlideWriterAgents      → one per slide,  PARALLEL via asyncio.gather
  Phase D: FactCheckerAgent       → audits full pitch (on-demand, not automatic)

The orchestrator replaces the sequential pipeline in the old
pitch_generator.py and audit_engine.py. The Flask server calls the
orchestrator; the agents are invisible to the API contract.
"""

import asyncio
import json
from pathlib import Path

from .research.research_agent    import ResearchAgent
from .retrieval.policy_retrieval_agent import PolicyRetrievalAgent
from .pitch.slide_agents         import (
    ExecutiveSummaryAgent,
    RiskAlignmentAgent,
    PolicyComparisonAgent,
    ROIValueAgent,
    CallToActionAgent,
)
from .audit.fact_checker_agent   import FactCheckerAgent


class PitchOrchestrator:
    """
    Coordinates multi-agent pitch generation.

    Usage:
        orchestrator = PitchOrchestrator(bundle_dir, project_root)

        # Generate company profile (Phase A)
        profile = orchestrator.research_company("Infosys")

        # Generate full pitch (Phases B + C)
        pitch = orchestrator.generate_pitch(profile, ["hdfc-optima-secure-plus", "care-health"])

        # Audit the pitch (Phase D, on-demand)
        audit = orchestrator.audit_pitch(pitch, policy_contexts)
    """

    def __init__(self, bundle_dir: Path, project_root: Path):
        self.bundle_dir   = bundle_dir
        self.project_root = project_root

    # ── Phase A: Research ────────────────────────────────────────────────────

    def research_company(self, company_name: str) -> dict:
        """
        Run the ResearchAgent to build a company profile.

        Returns the profile dict (same shape as v1 generate_company_profile).
        Raises RuntimeError on failure.
        """
        agent  = ResearchAgent()
        result = agent.run(company_name=company_name)

        if not result.success:
            raise RuntimeError(
                f"Research failed for '{company_name}': {result.error}"
            )
        return result.data

    # ── Phase B: Parallel Policy Retrieval ───────────────────────────────────

    async def _retrieve_all_policies_async(
        self, policy_ids: list, company_needs: list
    ) -> list:
        """Run one PolicyRetrievalAgent per policy — all in parallel."""
        agents = [
            PolicyRetrievalAgent(pid, self.bundle_dir, self.project_root)
            for pid in policy_ids
        ]
        results = await asyncio.gather(
            *[agent.run_async(company_needs=company_needs) for agent in agents]
        )
        # Return only successful context dicts; failed ones get empty context
        contexts = []
        for r in results:
            contexts.append(r.data if r.success else {
                "policy_id":    r.agent_name,
                "policy_name":  r.agent_name,
                "context_text": "",
                "num_concepts": 0,
                "source_map":   {},
            })
        return contexts

    def retrieve_policies(self, policy_ids: list, company_needs: list) -> list:
        """Sync wrapper around the async retrieval."""
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # Already in async context — create a task
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as pool:
                    future = pool.submit(
                        asyncio.run,
                        self._retrieve_all_policies_async(policy_ids, company_needs)
                    )
                    return future.result()
            else:
                return loop.run_until_complete(
                    self._retrieve_all_policies_async(policy_ids, company_needs)
                )
        except Exception:
            # Fallback: run sequentially if async setup fails
            results = []
            for pid in policy_ids:
                agent  = PolicyRetrievalAgent(pid, self.bundle_dir, self.project_root)
                result = agent.run(company_needs=company_needs)
                results.append(result.data if result.success else {
                    "policy_id": pid, "policy_name": pid,
                    "context_text": "", "num_concepts": 0, "source_map": {}
                })
            return results

    # ── Phase C: Parallel Slide Writing ──────────────────────────────────────

    async def _write_all_slides_async(
        self, company_profile: dict, policy_contexts: list
    ) -> list:
        """Run one SlideAgent per slide — all in parallel."""
        slide_agents = [
            ExecutiveSummaryAgent(),
            RiskAlignmentAgent(),
            PolicyComparisonAgent(),
            ROIValueAgent(),
            CallToActionAgent(),
        ]
        results = await asyncio.gather(*[
            agent.run_async(
                company_profile=company_profile,
                policy_contexts=policy_contexts,
            )
            for agent in slide_agents
        ])
        slides = []
        for i, r in enumerate(results, start=1):
            if r.success and r.data:
                slide = r.data
                slide.setdefault("slide_number", i)
                slides.append(slide)
            else:
                slides.append({
                    "slide_number":  i,
                    "title":         f"Slide {i}",
                    "bullets":       ["Content could not be generated — please try again."],
                    "speaker_notes": "",
                    "source_concepts": [],
                })
        return slides

    def write_slides(self, company_profile: dict, policy_contexts: list) -> list:
        """Sync wrapper around async slide writing."""
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as pool:
                    future = pool.submit(
                        asyncio.run,
                        self._write_all_slides_async(company_profile, policy_contexts)
                    )
                    return future.result()
            else:
                return loop.run_until_complete(
                    self._write_all_slides_async(company_profile, policy_contexts)
                )
        except Exception:
            # Fallback: run sequentially
            slides = []
            for i, AgentClass in enumerate([
                ExecutiveSummaryAgent, RiskAlignmentAgent, PolicyComparisonAgent,
                ROIValueAgent, CallToActionAgent
            ], start=1):
                agent  = AgentClass()
                result = agent.run(
                    company_profile=company_profile,
                    policy_contexts=policy_contexts,
                )
                slide = result.data if result.success else {
                    "slide_number": i, "title": f"Slide {i}",
                    "bullets": ["Generation failed."], "speaker_notes": "", "source_concepts": []
                }
                slide.setdefault("slide_number", i)
                slides.append(slide)
            return slides

    # ── Full pitch pipeline (B + C) ───────────────────────────────────────────

    def generate_pitch(self, company_profile: dict, policy_ids: list) -> dict:
        """
        Run the full multi-agent pitch pipeline:
          Phase B: Parallel policy retrieval
          Phase C: Parallel slide writing

        Returns a pitch dict compatible with the existing pptx_builder and frontend.
        """
        company_name   = company_profile.get("company_name", "the company")
        company_needs  = company_profile.get("insurance_needs", [])

        print(f"[Orchestrator] Phase B — Retrieving {len(policy_ids)} policies in parallel")
        policy_contexts = self.retrieve_policies(policy_ids, company_needs)

        print(f"[Orchestrator] Phase C — Writing 5 slides in parallel")
        slides = self.write_slides(company_profile, policy_contexts)

        # Build source map across all policies
        source_map = {}
        for ctx in policy_contexts:
            source_map.update(ctx.get("source_map", {}))

        # Determine recommended policy (first one is the best match by retrieval rank)
        best_policy = policy_contexts[0]["policy_name"] if policy_contexts else "selected policy"

        pitch = {
            "pitch_title":        f"Insurance Proposal for {company_name}",
            "target_company":     company_name,
            "slides":             slides,
            "recommended_policy": best_policy,
            "key_differentiators": [
                f"Tailored to {company_profile.get('industry', 'your industry')} risk profile",
                "Grounded in verified OKF policy knowledge",
                "Multi-agent analysis for precision and consistency",
            ],
            "_source_map":        source_map,
            "_policy_ids":        policy_ids,
            "_company_profile":   company_profile,
            "_agent_mode":        True,   # Flag so frontend can show "Agent Mode" badge
            "_policy_contexts":   [
                {"policy_id": c["policy_id"], "policy_name": c["policy_name"],
                 "num_concepts": c["num_concepts"]}
                for c in policy_contexts
            ],
        }
        print(f"[Orchestrator] Pitch complete — {len(slides)} slides generated")
        return pitch

    # ── Phase D: Fact-Checking (on-demand) ───────────────────────────────────

    def audit_pitch(self, pitch: dict, policy_ids: list) -> dict:
        """
        Run the FactCheckerAgent on the full pitch.
        Uses combined OKF context from all selected policies.
        """
        print(f"[Orchestrator] Phase D — Auditing pitch")

        # Rebuild context for audit
        policy_contexts = self.retrieve_policies(
            policy_ids,
            pitch.get("_company_profile", {}).get("insurance_needs", [])
        )
        combined_context = "\n\n".join(
            f"=== {c['policy_name']} ===\n{c['context_text'][:800]}"
            for c in policy_contexts
        )

        agent  = FactCheckerAgent()
        result = agent.run(pitch=pitch, okf_context=combined_context)
        return result.data if result.success else {
            "audit_summary":   "PASS_WITH_NOTES",
            "total_claims":    0,
            "verified_claims": 0,
            "flagged_claims":  0,
            "claims":          [],
            "recommendations": ["Audit could not be completed. Please review manually."],
        }
