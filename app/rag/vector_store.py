"""
Vector Store — FAISS index management for OKF concept embeddings.

Builds a FAISS index from OKF concept documents for similarity search.
Used as a fallback when OKF graph traversal doesn't find enough context.
"""

import os
from pathlib import Path
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain.schema import Document


def _get_embeddings():
    """Create Google Generative AI embeddings."""
    api_key = os.getenv("GOOGLE_API_KEY", "")
    return GoogleGenerativeAIEmbeddings(
        model="models/embedding-001",
        google_api_key=api_key,
    )


def build_index_from_concepts(concepts: list, index_path: str | Path) -> FAISS:
    """Build a FAISS index from OKF concept objects.
    
    Args:
        concepts: List of OKFConcept objects from bundle_reader
        index_path: Path to save the FAISS index
    
    Returns:
        FAISS vector store
    """
    documents = []
    for concept in concepts:
        # Combine title, description, and body for embedding
        content = f"# {concept.title}\n\n{concept.description}\n\n{concept.body}"
        
        # Store metadata for retrieval
        metadata = {
            "concept_id": concept.id,
            "type": concept.concept_type,
            "title": concept.title,
            "tags": ", ".join(concept.tags),
            "filepath": concept.filepath,
        }
        
        # Add source references to metadata
        if concept.sources:
            source_refs = []
            for src in concept.sources:
                source_refs.append(src.get("resource", ""))
            metadata["sources"] = "; ".join(source_refs)
        
        documents.append(Document(page_content=content, metadata=metadata))

    embeddings = _get_embeddings()
    vectorstore = FAISS.from_documents(documents, embeddings)
    
    # Save to disk
    index_path = Path(index_path)
    index_path.parent.mkdir(parents=True, exist_ok=True)
    vectorstore.save_local(str(index_path))
    
    return vectorstore


def load_index(index_path: str | Path) -> FAISS:
    """Load an existing FAISS index from disk."""
    embeddings = _get_embeddings()
    return FAISS.load_local(
        str(index_path), embeddings, allow_dangerous_deserialization=True
    )


def search(vectorstore: FAISS, query: str, k: int = 5) -> list[Document]:
    """Search the vector store for similar documents.
    
    Returns list of Documents with content and metadata.
    """
    return vectorstore.similarity_search(query, k=k)
