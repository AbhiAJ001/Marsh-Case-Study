"""
OKF Retriever — Graph-aware retrieval from OKF knowledge bundles.

This is the PRIMARY retrieval layer. It finds relevant concepts using:
1. Type-based filtering (get coverages, benefits, exclusions for a policy)
2. Tag-based matching (find concepts relevant to a company's needs)
3. Graph traversal (follow cross-links to pull in related concepts)
4. Keyword search (fallback text matching)

The retriever returns structured context that can be passed directly
to the LLM for pitch generation.
"""

from dataclasses import dataclass, field
from pathlib import Path
from .bundle_reader import BundleReader, OKFConcept


# Policy tag → display name mapping
POLICY_MAP = {
    "abhi-activ-one": {"tag": "abhi", "name": "ABHI Activ One"},
    "care-health": {"tag": "care-health", "name": "Care Health Insurance Plan"},
    "hdfc-optima-secure-plus": {"tag": "hdfc-ergo", "name": "HDFC ERGO Optima Secure+"},
    "niva-bupa-reassure": {"tag": "niva-bupa", "name": "Niva Bupa ReAssure 2.0"},
}


@dataclass
class RetrievalResult:
    """A single retrieval result with concept and relevance info."""
    concept: OKFConcept
    relevance: str          # Why this concept was retrieved
    score: float = 1.0      # Relevance score (higher = more relevant)

    def to_context_block(self) -> str:
        """Format as a context block for LLM consumption."""
        source_refs = self.concept.get_source_refs()
        sources_text = "\n".join(f"  - {ref}" for ref in source_refs) if source_refs else "  (no source attribution)"
        
        return f"""### {self.concept.title}
**Type:** {self.concept.concept_type}
**Sources:**
{sources_text}

{self.concept.body}
"""


@dataclass
class RetrievalContext:
    """Complete retrieval context for pitch generation."""
    policy_names: list[str]
    results: list[RetrievalResult] = field(default_factory=list)
    
    @property
    def total_concepts(self) -> int:
        return len(self.results)

    def to_llm_context(self) -> str:
        """Format all results as a single text block for LLM context window."""
        sections = [
            f"# Insurance Policy Knowledge — Retrieved from OKF Bundle\n",
            f"**Policies:** {', '.join(self.policy_names)}\n",
            f"**Total concepts retrieved:** {self.total_concepts}\n\n",
            "---\n\n",
        ]
        
        for result in self.results:
            sections.append(result.to_context_block())
            sections.append("\n---\n\n")
        
        return "".join(sections)

    def get_source_map(self) -> dict[str, list[str]]:
        """Build a map of concept title → source references for audit."""
        source_map = {}
        for result in self.results:
            refs = result.concept.get_source_refs()
            if refs:
                source_map[result.concept.title] = refs
        return source_map


class OKFRetriever:
    """Graph-aware retriever for OKF knowledge bundles."""

    def __init__(self, bundle_dir: str | Path):
        self.reader = BundleReader(bundle_dir)
        self.reader.load()

    def retrieve_for_policies(self, policy_ids: list[str], 
                               company_needs: list[str] = None) -> RetrievalContext:
        """Retrieve all relevant concepts for the given policies.
        
        Args:
            policy_ids: List of policy identifiers (e.g. ["hdfc-optima-secure-plus", "care-health"])
            company_needs: Optional list of keywords describing company needs
                          (e.g. ["young workforce", "chronic conditions", "cost-sensitive"])
        
        Returns:
            RetrievalContext with all relevant concepts
        """
        results = []
        policy_names = []
        seen_ids = set()

        for policy_id in policy_ids:
            policy_info = POLICY_MAP.get(policy_id)
            if not policy_info:
                continue
            
            policy_names.append(policy_info["name"])
            tag = policy_info["tag"]

            # 1. Get the master policy document
            policy_concepts = self.reader.get_by_type("Insurance Policy")
            for pc in policy_concepts:
                if tag in pc.tags and pc.id not in seen_ids:
                    results.append(RetrievalResult(
                        concept=pc, relevance="Primary policy document", score=10.0
                    ))
                    seen_ids.add(pc.id)

                    # 2. Follow links from the policy doc (graph traversal)
                    linked = self.reader.get_linked_concepts(pc)
                    for linked_concept in linked:
                        if linked_concept.id not in seen_ids:
                            results.append(RetrievalResult(
                                concept=linked_concept,
                                relevance=f"Linked from {pc.title}",
                                score=8.0,
                            ))
                            seen_ids.add(linked_concept.id)

            # 3. Get all concepts tagged with this policy
            tagged = self.reader.get_by_tag(tag)
            for tc in tagged:
                if tc.id not in seen_ids:
                    results.append(RetrievalResult(
                        concept=tc, relevance=f"Tagged with '{tag}'", score=6.0
                    ))
                    seen_ids.add(tc.id)

        # 4. Add cross-policy concepts (coverages, exclusions, pricing comparisons)
        for shared_type in ["Policy Coverage", "Policy Exclusion", "Pricing"]:
            for concept in self.reader.get_by_type(shared_type):
                if concept.id not in seen_ids:
                    # Check if this concept mentions any of the selected policies
                    body_lower = concept.body.lower()
                    if any(POLICY_MAP[pid]["name"].lower() in body_lower 
                           for pid in policy_ids if pid in POLICY_MAP):
                        results.append(RetrievalResult(
                            concept=concept,
                            relevance=f"Cross-policy {shared_type.lower()}",
                            score=5.0,
                        ))
                        seen_ids.add(concept.id)

        # 5. If company_needs provided, boost/add concepts matching those needs
        if company_needs:
            for need in company_needs:
                search_results = self.reader.search(need)
                for concept in search_results[:3]:  # Top 3 per need
                    if concept.id not in seen_ids:
                        results.append(RetrievalResult(
                            concept=concept,
                            relevance=f"Matches company need: '{need}'",
                            score=4.0,
                        ))
                        seen_ids.add(concept.id)

        # Sort by score (highest first)
        results.sort(key=lambda r: r.score, reverse=True)

        return RetrievalContext(policy_names=policy_names, results=results)

    def get_available_policies(self) -> list[dict]:
        """Return list of available policies for the frontend."""
        policies = []
        for pid, info in POLICY_MAP.items():
            policies.append({
                "id": pid,
                "name": info["name"],
                "tag": info["tag"],
            })
        return policies


if __name__ == "__main__":
    # Test the retriever
    project_root = Path(__file__).resolve().parent.parent.parent
    retriever = OKFRetriever(project_root / "knowledge_bundle")
    
    print("Available policies:")
    for p in retriever.get_available_policies():
        print(f"  - {p['id']}: {p['name']}")
    
    print("\nRetrieving for HDFC + Care Health:")
    ctx = retriever.retrieve_for_policies(
        ["hdfc-optima-secure-plus", "care-health"],
        company_needs=["wellness", "chronic conditions"]
    )
    print(f"  Retrieved {ctx.total_concepts} concepts")
    for r in ctx.results[:5]:
        print(f"  [{r.score}] {r.concept.title} — {r.relevance}")
