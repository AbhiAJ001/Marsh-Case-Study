"""
LangChain Fallback — Secondary retrieval using FAISS similarity search.

Used when OKF graph traversal doesn't return enough context for the
pitch generator. Embeds all OKF concept documents and provides
semantic similarity search.
"""

from pathlib import Path
from .vector_store import build_index_from_concepts, load_index, search


FAISS_INDEX_DIR = ".faiss_index"


class LangChainFallback:
    """Fallback retrieval using FAISS vector search over OKF concepts."""

    def __init__(self, project_root: str | Path):
        self.project_root = Path(project_root)
        self.index_path = self.project_root / FAISS_INDEX_DIR
        self._vectorstore = None

    def build_index(self, concepts: list) -> int:
        """Build FAISS index from OKF concepts.
        
        Args:
            concepts: List of OKFConcept objects
        
        Returns:
            Number of concepts indexed
        """
        self._vectorstore = build_index_from_concepts(concepts, self.index_path)
        return len(concepts)

    def load(self) -> bool:
        """Load existing FAISS index. Returns True if successful."""
        if self.index_path.exists():
            try:
                self._vectorstore = load_index(self.index_path)
                return True
            except Exception:
                return False
        return False

    def is_ready(self) -> bool:
        """Check if the index is loaded and ready for search."""
        return self._vectorstore is not None

    def search(self, query: str, k: int = 5) -> list[dict]:
        """Search for relevant concepts by semantic similarity.
        
        Returns list of dicts with: content, concept_id, type, title, sources, score
        """
        if not self.is_ready():
            return []

        docs = search(self._vectorstore, query, k=k)
        
        results = []
        for doc in docs:
            results.append({
                "content": doc.page_content,
                "concept_id": doc.metadata.get("concept_id", ""),
                "type": doc.metadata.get("type", ""),
                "title": doc.metadata.get("title", ""),
                "tags": doc.metadata.get("tags", ""),
                "sources": doc.metadata.get("sources", ""),
                "filepath": doc.metadata.get("filepath", ""),
            })
        
        return results

    def search_for_context(self, query: str, k: int = 5) -> str:
        """Search and return formatted context string for LLM."""
        results = self.search(query, k=k)
        
        if not results:
            return ""
        
        sections = ["# Additional Context (Fallback Retrieval)\n\n"]
        for r in results:
            sections.append(f"### {r['title']}\n")
            sections.append(f"**Type:** {r['type']}\n")
            if r['sources']:
                sections.append(f"**Sources:** {r['sources']}\n")
            sections.append(f"\n{r['content']}\n\n---\n\n")
        
        return "".join(sections)
