"""
OKF Bundle Reader — Parses the knowledge bundle, reads concept files,
and provides structured access to the OKF data.

Reads YAML frontmatter + markdown body from concept files,
traverses index files, and supports filtering by type and tags.
"""

import re
import yaml
from pathlib import Path
from dataclasses import dataclass, field


@dataclass
class OKFConcept:
    """A single OKF concept document."""
    filepath: str                    # Relative path within bundle
    concept_type: str                # e.g. "Insurance Policy", "Policy Coverage"
    title: str
    description: str
    tags: list[str] = field(default_factory=list)
    sources: list[dict] = field(default_factory=list)
    status: str = "stable"
    body: str = ""                   # Markdown content after frontmatter
    frontmatter: dict = field(default_factory=dict)  # Raw YAML dict

    @property
    def id(self) -> str:
        """Slug-based ID from filepath."""
        return self.filepath.replace("\\", "/").replace(".md", "")

    def get_links(self) -> list[str]:
        """Extract all internal markdown links from the body.
        
        Returns list of relative paths (e.g. "../policies/hdfc-optima-secure-plus.md")
        """
        pattern = r'\[([^\]]+)\]\((\.\./[^)]+\.md)\)'
        return [match[1] for match in re.findall(pattern, self.body)]

    def get_source_refs(self) -> list[str]:
        """Get human-readable source references."""
        refs = []
        for src in self.sources:
            resource = src.get("resource", "")
            title = src.get("title", "")
            refs.append(f"{title} — {resource}")
        return refs


def parse_concept_file(filepath: Path, bundle_root: Path) -> OKFConcept:
    """Parse a single OKF markdown file into an OKFConcept.
    
    Args:
        filepath: Absolute path to the .md file
        bundle_root: Absolute path to the bundle root directory
    
    Returns:
        OKFConcept with parsed frontmatter and body
    """
    content = filepath.read_text(encoding='utf-8')
    
    # Split YAML frontmatter from markdown body
    frontmatter = {}
    body = content
    
    if content.startswith('---'):
        parts = content.split('---', 2)
        if len(parts) >= 3:
            try:
                frontmatter = yaml.safe_load(parts[1]) or {}
            except yaml.YAMLError:
                frontmatter = {}
            body = parts[2].strip()

    relative_path = str(filepath.relative_to(bundle_root))

    return OKFConcept(
        filepath=relative_path,
        concept_type=frontmatter.get("type", "Unknown"),
        title=frontmatter.get("title", filepath.stem.replace("-", " ").title()),
        description=frontmatter.get("description", ""),
        tags=frontmatter.get("tags", []),
        sources=frontmatter.get("sources", []),
        status=frontmatter.get("status", "stable"),
        body=body,
        frontmatter=frontmatter,
    )


class BundleReader:
    """Reads and indexes an OKF knowledge bundle."""

    def __init__(self, bundle_dir: str | Path):
        self.bundle_dir = Path(bundle_dir)
        self._concepts: dict[str, OKFConcept] = {}
        self._loaded = False

    def load(self) -> int:
        """Load all concept files from the bundle.
        
        Returns the number of concepts loaded.
        """
        self._concepts.clear()

        for md_file in self.bundle_dir.rglob("*.md"):
            # Skip index and log files
            if md_file.name in ("index.md", "log.md"):
                continue
            
            concept = parse_concept_file(md_file, self.bundle_dir)
            self._concepts[concept.id] = concept

        self._loaded = True
        return len(self._concepts)

    def _ensure_loaded(self):
        if not self._loaded:
            self.load()

    def get_all(self) -> list[OKFConcept]:
        """Return all concepts."""
        self._ensure_loaded()
        return list(self._concepts.values())

    def get_by_id(self, concept_id: str) -> OKFConcept | None:
        """Get a concept by its ID (relative path without .md)."""
        self._ensure_loaded()
        return self._concepts.get(concept_id)

    def get_by_type(self, concept_type: str) -> list[OKFConcept]:
        """Get all concepts of a specific type."""
        self._ensure_loaded()
        return [c for c in self._concepts.values() 
                if c.concept_type.lower() == concept_type.lower()]

    def get_by_tag(self, tag: str) -> list[OKFConcept]:
        """Get all concepts that have a specific tag."""
        self._ensure_loaded()
        return [c for c in self._concepts.values() if tag in c.tags]

    def get_by_tags(self, tags: list[str], match_all: bool = False) -> list[OKFConcept]:
        """Get concepts matching tags.
        
        Args:
            tags: List of tags to match
            match_all: If True, concept must have ALL tags. If False, ANY tag matches.
        """
        self._ensure_loaded()
        results = []
        for concept in self._concepts.values():
            if match_all:
                if all(t in concept.tags for t in tags):
                    results.append(concept)
            else:
                if any(t in concept.tags for t in tags):
                    results.append(concept)
        return results

    def get_policies(self) -> list[OKFConcept]:
        """Shortcut: get all Insurance Policy concepts."""
        return self.get_by_type("Insurance Policy")

    def get_linked_concepts(self, concept: OKFConcept) -> list[OKFConcept]:
        """Follow all internal links from a concept and return the linked concepts."""
        self._ensure_loaded()
        linked = []
        
        for link_path in concept.get_links():
            # Resolve relative path from the concept's directory
            concept_dir = (self.bundle_dir / concept.filepath).parent
            resolved = (concept_dir / link_path).resolve()
            
            try:
                relative = str(resolved.relative_to(self.bundle_dir))
                concept_id = relative.replace("\\", "/").replace(".md", "")
                linked_concept = self._concepts.get(concept_id)
                if linked_concept:
                    linked.append(linked_concept)
            except ValueError:
                continue
        
        return linked

    def search(self, query: str) -> list[OKFConcept]:
        """Simple text search across title, description, tags, and body."""
        self._ensure_loaded()
        query_lower = query.lower()
        results = []
        
        for concept in self._concepts.values():
            score = 0
            if query_lower in concept.title.lower():
                score += 10
            if query_lower in concept.description.lower():
                score += 5
            if any(query_lower in tag for tag in concept.tags):
                score += 8
            if query_lower in concept.body.lower():
                score += 2
            
            if score > 0:
                results.append((score, concept))
        
        results.sort(key=lambda x: x[0], reverse=True)
        return [c for _, c in results]

    def get_context_for_policy(self, policy_tag: str) -> str:
        """Build a rich text context for a specific policy by following links.
        
        Args:
            policy_tag: Tag identifying the policy (e.g. "hdfc-ergo", "care-health")
        
        Returns:
            Concatenated markdown string with all relevant concepts.
        """
        self._ensure_loaded()
        concepts = self.get_by_tag(policy_tag)
        
        if not concepts:
            return ""
        
        sections = []
        for concept in concepts:
            sections.append(f"## {concept.title}\n")
            sections.append(f"*Type: {concept.concept_type}*\n\n")
            sections.append(concept.body)
            sections.append("\n\n---\n\n")
        
        return "".join(sections)

    def summary(self) -> dict:
        """Return a summary of the bundle contents."""
        self._ensure_loaded()
        type_counts = {}
        for concept in self._concepts.values():
            t = concept.concept_type
            type_counts[t] = type_counts.get(t, 0) + 1
        
        return {
            "total_concepts": len(self._concepts),
            "by_type": type_counts,
            "types": list(type_counts.keys()),
        }


if __name__ == "__main__":
    # Test the reader
    project_root = Path(__file__).resolve().parent.parent.parent
    reader = BundleReader(project_root / "knowledge_bundle")
    count = reader.load()
    
    print(f"Loaded {count} concepts")
    print(f"Summary: {reader.summary()}")
    print(f"\nPolicies:")
    for p in reader.get_policies():
        print(f"  - {p.title}: {p.description[:80]}...")
    
    print(f"\nSearch 'unlimited':")
    for c in reader.search("unlimited")[:5]:
        print(f"  - [{c.concept_type}] {c.title}")
