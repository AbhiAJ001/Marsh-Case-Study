"""
Policy Retrieval Agent — Dedicated retrieval for a single insurance policy.

In the multi-agent architecture, one PolicyRetrievalAgent is created per
selected policy. All agents run in parallel via asyncio.gather(), giving
each policy its own full context budget — no more shared truncation.

Returns structured knowledge ready for the Pitch Writer Agents.
"""

from pathlib import Path
from ..base_agent import BaseAgent, AgentResult
from ...okf.okf_retriever import OKFRetriever, POLICY_MAP
from ...rag.langchain_fallback import LangChainFallback


class PolicyRetrievalAgent(BaseAgent):
    """
    Retrieves rich, focused context for ONE insurance policy.

    Unlike the old single retriever that merged all policies into one
    bloated context blob, this agent is entirely dedicated to one policy,
    so it can return deeper, more precise knowledge.
    """

    name = "PolicyRetrievalAgent"

    def __init__(self, policy_id: str, bundle_dir: Path, project_root: Path):
        self.policy_id    = policy_id
        self.bundle_dir   = bundle_dir
        self.project_root = project_root

        policy_info = POLICY_MAP.get(policy_id, {})
        self.policy_name = policy_info.get("name", policy_id)
        self.name        = f"PolicyRetrievalAgent[{self.policy_name}]"

    def build_prompt(self, **inputs) -> str:
        # Retrieval agents don't need an LLM — they use symbolic retrieval.
        # This method is required by the abstract base but unused here.
        return ""

    def parse_output(self, text: str, **inputs) -> dict:
        return {}

    def run(self, company_needs: list = None) -> AgentResult:
        """
        Run OKF retrieval + optional LangChain fallback for this policy.

        Args:
            company_needs: List of need strings from company profile
                           (e.g. ["young workforce", "chronic conditions"])

        Returns:
            AgentResult with data = {
                "policy_id":    str,
                "policy_name":  str,
                "context_text": str,   # formatted for LLM
                "num_concepts": int,
                "source_map":   dict,
            }
        """
        self._log(f"Retrieving for policy: {self.policy_name}")
        try:
            retriever   = OKFRetriever(self.bundle_dir)
            okf_context = retriever.retrieve_for_policies(
                [self.policy_id], company_needs or []
            )
            context_text = okf_context.to_llm_context()

            # Supplement with LangChain fallback if OKF is thin
            if okf_context.total_concepts < 4:
                self._log("OKF context thin — running LangChain fallback")
                fallback = LangChainFallback(self.project_root)
                if fallback.load():
                    extra = fallback.search_for_context(
                        f"{self.policy_name} insurance coverage benefits features",
                        k=4
                    )
                    if extra:
                        context_text += "\n\n" + extra

            # Cap at 2000 chars per policy to stay within Groq TPM limits
            if len(context_text) > 2000:
                context_text = context_text[:2000] + "\n[...context capped for token budget...]"

            self._log(f"Retrieved {okf_context.total_concepts} concepts")
            return AgentResult(
                agent_name=self.name,
                data={
                    "policy_id":    self.policy_id,
                    "policy_name":  self.policy_name,
                    "context_text": context_text,
                    "num_concepts": okf_context.total_concepts,
                    "source_map":   okf_context.get_source_map(),
                },
                model_used="okf+faiss",   # symbolic retrieval, no LLM used
            )

        except Exception as e:
            self._log(f"Retrieval failed: {e}")
            return AgentResult(
                agent_name=self.name,
                data={
                    "policy_id":    self.policy_id,
                    "policy_name":  self.policy_name,
                    "context_text": f"No context available for {self.policy_name}.",
                    "num_concepts": 0,
                    "source_map":   {},
                },
                error=str(e),
            )
