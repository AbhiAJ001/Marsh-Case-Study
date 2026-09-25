# Marsh AI Pitch Generator

An AI-powered application that generates client-specific insurance marketing pitches for Marsh Client Advisors — grounded in structured policy knowledge (OKF), with built-in content auditing to prevent hallucination.

Built for the NMIMS 2026 Internship Case Study.

---

## What It Does

A Marsh Client Advisor enters a company name, selects insurance policies, and gets:

1. **Company profile** — industry, size, key risks, and insurance needs (researched via Gemini + web search, with clearly-labelled assumptions when data is uncertain)
2. **3–5 slide marketing pitch** — tailored to the company, with every claim grounded in OKF knowledge concepts from the selected policy documents
3. **Downloadable PowerPoint** — clean, professional slide deck ready for client meetings
4. **Audit report** — every factual claim traced back to the source policy text (with PDF page/section provenance), confidence scoring, and flags for human review

---

## Architecture

```
Frontend (HTML/CSS/JS)              Flask API (Python)
┌──────────────────────┐           ┌────────────────────────────────┐
│ index.html           │           │ server.py                      │
│ css/styles.css       │──────────→│ POST /api/profile              │
│ js/app.js            │   REST    │ POST /api/pitch                │
│                      │←──────────│ POST /api/audit                │
│ No framework.        │   JSON    │ GET  /api/download-pptx        │
│ Handcrafted HTML.    │           │                                │
└──────────────────────┘           │ ┌──────────────────────────┐   │
                                   │ │ OKF Knowledge Bundle     │   │
                                   │ │ (Primary Retrieval)      │   │
                                   │ │ Structured concept files  │   │
                                   │ │ with YAML metadata +     │   │
                                   │ │ cross-links              │   │
                                   │ └──────────────────────────┘   │
                                   │ ┌──────────────────────────┐   │
                                   │ │ LangChain + FAISS        │   │
                                   │ │ (Fallback Retrieval)     │   │
                                   │ └──────────────────────────┘   │
                                   └────────────────────────────────┘
```

Open [`architecture.html`](architecture.html) for the full interactive system diagram.

---

## Project Structure

```
├── frontend/                       # Pure HTML/CSS/JS (no framework)
│   ├── index.html                  # Single-page application
│   ├── css/styles.css              # Custom design (human-crafted aesthetic)
│   └── js/app.js                   # Client logic, API calls, DOM updates
├── app/                            # Python backend (Flask)
│   ├── server.py                   # Flask API — serves frontend + REST
│   ├── config.py                   # API key handling (prompts on first run)
│   ├── core/                       # Business logic
│   │   ├── company_profile.py      # generateCompanyProfile()
│   │   ├── pitch_generator.py      # generateMarketingPitch()
│   │   ├── audit_engine.py         # auditPitchContent()
│   │   └── pptx_builder.py         # PowerPoint file builder
│   ├── okf/                        # OKF knowledge layer (primary)
│   │   ├── bundle_builder.py       # PDF → OKF concept files
│   │   ├── bundle_reader.py        # Parse and traverse OKF bundle
│   │   └── okf_retriever.py        # Graph-aware retrieval
│   ├── rag/                        # LangChain fallback (secondary)
│   │   ├── langchain_fallback.py   # Embed concepts → FAISS search
│   │   └── vector_store.py         # FAISS index management
│   └── utils/                      # Prompts and shared utilities
├── knowledge_bundle/               # OKF bundle (structured policy knowledge)
│   ├── index.md                    # Root catalog
│   ├── policies/                   # Insurance Policy concepts
│   ├── coverages/                  # Coverage concepts
│   ├── benefits/                   # Benefit concepts
│   ├── exclusions/                 # Exclusion concepts
│   ├── pricing/                    # Pricing and discount concepts
│   └── references/                 # Supporting references
├── Policy Documents/               # 4 source insurance policy PDFs
├── docs/                           # Case study documentation
├── output/                         # Generated pitch decks and reports
└── write_up/                       # Final submission write-up
```

See [`map.md`](map.md) for the complete file-by-file reference with data models and API schemas.

---

## Tech Stack

| Layer | Technology | Why |
|-------|-----------|-----|
| Frontend | HTML + CSS + vanilla JS | Full design control, no framework — looks human-crafted |
| Backend | Flask (Python) | Simple, serves static files natively, REST API |
| Knowledge | OKF (Open Knowledge Format) | Structured concepts with YAML metadata, cross-links, provenance |
| LLM | Google Gemini | Strong reasoning, good grounding, free tier |
| RAG Fallback | LangChain + FAISS | Similarity search when OKF graph traversal needs more context |
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

# Run the application (will prompt for Gemini API key on first run)
python -m app.server
```

The app opens at `http://localhost:5000`. On first run, if no `.env` file exists, you'll be prompted to enter your [Gemini API key](https://aistudio.google.com/apikey).

---

## What is OKF?

[Open Knowledge Format (OKF)](https://github.com/GoogleCloudPlatform/knowledge-catalog) is Google's vendor-neutral format for representing knowledge as plain markdown files with YAML frontmatter.

Instead of naively chunking PDFs into a vector store, we **decompose each policy into structured concept files**:

- Each coverage, benefit, exclusion, and pricing detail is its own file
- YAML frontmatter carries `type`, `tags`, `sources` (citing exact PDF page), `status`, and `stale_after`
- Concepts cross-link to each other (a coverage links to its exclusions)
- The audit engine traces claims to OKF `sources[]` for provenance

This gives us **graph-aware retrieval** (following links between concepts) instead of just similarity search.

---

## AI Usage Practices

- **OKF grounding** — every pitch claim is generated from structured OKF concept files, not raw PDF text or LLM general knowledge
- **Source attribution** — every concept carries `sources` metadata with exact PDF page and section references
- **Hallucination detection** — the audit engine cross-references each claim against OKF source provenance
- **Assumption labelling** — when company data is uncertain, assumptions are explicitly marked
- **Human-in-the-loop** — advisors must review and approve every generated pitch
- **Centralized prompts** — all LLM prompts are versioned in `app/utils/prompts.py`
- **Web search verification** — company profiles are enriched with real-time web data, not just LLM training data

---

## Agentic Development Practices

| File | Purpose |
|------|---------|
| [`mind.md`](mind.md) | Persistent project memory — context, design rules, and tech decisions |
| [`log.md`](log.md) | Living work tracker — task status, phase progress, decision log |
| [`map.md`](map.md) | System blueprint — file manifest, API schema, data models |
| [`architecture.html`](architecture.html) | Visual system architecture with data flows |

---

## Policy Documents

| Insurer | Product | Coverage Range |
|---------|---------|---------------|
| Aditya Birla Health Insurance | Activ One | ₹5 Lacs – ₹6 Crores |
| Care Health Insurance | Care Health Plan | ₹5 Lacs – ₹1 Crore |
| HDFC ERGO | Optima Secure+ | ₹10 Lacs – ₹2 Crores |
| Niva Bupa | ReAssure 2.0 | ₹5 Lacs – ₹1 Crore |

---

## Deliverables

1. Working application — web UI + backend implementing the pitch generator and audit layer
2. Sample pitch deck — generated PowerPoint for a chosen company
3. Audit results — report showing traceability of claims to source policy documents
4. Write-up — approach, tools/libraries used, and key design decisions

---

## License

This project is an academic case study submission for NMIMS 2026.
