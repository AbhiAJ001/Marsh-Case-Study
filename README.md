# Marsh AI Pitch Generator

An AI-powered application that generates client-specific insurance marketing pitches for Marsh Client Advisors — grounded in real policy documents, with built-in content auditing to prevent hallucination.

Built for the NMIMS 2026 Internship Case Study.

---

## What It Does

A Marsh Client Advisor enters a company name, selects insurance policies, and gets:

1. **Company profile** — industry, size, key risks, and insurance needs (with clearly-labelled assumptions when data is uncertain)
2. **3–5 slide marketing pitch** — tailored to the company, with every claim grounded in the selected policy documents
3. **Downloadable PowerPoint** — clean, professional slide deck ready for client meetings
4. **Audit report** — every factual claim traced back to the source policy text, with confidence scoring and flags for human review

---

## Architecture

The system follows a clean layered architecture with four distinct concerns:

```
UI Layer (Streamlit + Custom CSS)
    ↓
Core Logic (Company Research → Pitch Generation)
    ↓
RAG Pipeline (PDF Ingestion → FAISS Vector Search → Semantic Retrieval)
    ↓
Audit Engine (Claim Extraction → Source Matching → Confidence Scoring)
```

Open [`architecture.html`](architecture.html) for the full interactive system diagram.

---

## Project Structure

```
├── app/
│   ├── main.py                 # Application entry point
│   ├── config.py               # Environment and API configuration
│   ├── styles.css              # Custom UI styling
│   ├── components/             # UI building blocks
│   ├── core/                   # Business logic
│   │   ├── company_profile.py  # generateCompanyProfile()
│   │   ├── pitch_generator.py  # generateMarketingPitch()
│   │   ├── audit_engine.py     # auditPitchContent()
│   │   └── pptx_builder.py     # PowerPoint file creation
│   ├── rag/                    # Retrieval-Augmented Generation
│   │   ├── document_loader.py  # PDF processing and chunking
│   │   ├── vector_store.py     # FAISS index management
│   │   └── retriever.py        # Semantic search interface
│   └── utils/                  # Shared utilities and prompts
├── Policy Documents/           # 4 source insurance policy PDFs
├── output/                     # Generated pitch decks and reports
├── docs/                       # Case study and documentation
└── write_up/                   # Final submission write-up
```

See [`map.md`](map.md) for the complete file-by-file reference with function signatures and data models.

---

## Tech Stack

| Layer | Technology | Why |
|-------|-----------|-----|
| UI | Streamlit + custom CSS | Rapid development, Python-native, fully customizable |
| LLM | Google Gemini | Strong reasoning, good grounding capability, free tier |
| RAG | LangChain + FAISS | Lightweight vector search, no external server needed |
| PDF | PyPDF2 | Reliable text extraction from policy brochures |
| PPT | python-pptx | Programmatic PowerPoint generation |
| Config | python-dotenv | Secure environment variable management |

---

## Setup

```bash
# Clone the repository
git clone https://github.com/AbhiAJ001/Marsh-Case-Study.git
cd Marsh-Case-Study

# Install dependencies
pip install -r requirements.txt

# Configure API key
cp .env.example .env
# Edit .env and add your Google Gemini API key

# Run the application
streamlit run app/main.py
```

---

## AI Usage Practices

This project demonstrates responsible AI development:

- **RAG grounding** — every pitch claim is generated from retrieved policy document chunks, not from the LLM's general knowledge
- **Hallucination detection** — a dedicated audit engine cross-references each claim against source text and assigns confidence scores
- **Assumption labelling** — when the LLM cannot verify company data, assumptions are explicitly marked as `[Assumed]`
- **Human-in-the-loop** — advisors must review and approve/edit/reject every generated pitch before use
- **Centralized prompts** — all LLM prompts are versioned in a single file for auditability and consistency
- **Source attribution** — every retrieval result carries metadata: source document, page number, and section type

---

## Agentic Development Practices

This project was built using structured agentic development workflows:

| File | Purpose |
|------|---------|
| [`mind.md`](mind.md) | Persistent project memory — context, design rules, and tech decisions that agents reference across sessions |
| [`log.md`](log.md) | Living work tracker — task status, phase progress, decision log, and blockers |
| [`map.md`](map.md) | System blueprint — complete file manifest, function signatures, data models, and dependency graph |
| [`architecture.html`](architecture.html) | Visual system architecture with component relationships and data flows |

Key practices:
- Modular architecture with clear separation of concerns (UI, logic, RAG, audit)
- Structured data models using Python dataclasses for all internal interfaces
- Decision logging with rationale for every technology and design choice
- Phase-gated execution with defined inputs, outputs, and verification for each task

---

## Policy Documents

The system works with four medical insurance policy brochures:

| Insurer | Product | Coverage Range |
|---------|---------|---------------|
| Aditya Birla Health Insurance | Activ One | ₹5 Lacs – ₹6 Crores |
| Care Health Insurance | Care Health Plan | ₹5 Lacs – ₹1 Crore |
| HDFC ERGO | Optima Secure+ | ₹10 Lacs – ₹2 Crores |
| Niva Bupa | ReAssure 2.0 | ₹5 Lacs – ₹1 Crore |

---

## Deliverables

1. Working application — UI + backend implementing the pitch generator and audit layer
2. Sample pitch deck — generated PowerPoint for a chosen company
3. Audit results — report showing traceability of claims to source policy documents
4. Write-up — approach, tools/libraries used, and key design decisions

---

## License

This project is an academic case study submission for NMIMS 2026.
