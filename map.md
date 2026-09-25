# MAP — System Blueprint

> Complete reference of what lives where and why. Every file, every function, every data flow.

---

## Directory Tree

```
Marsh-Case-Study/
│
├── README.md                          # Project overview, setup, usage
├── mind.md                            # Permanent project memory + design rules
├── log.md                             # Work tracker + decision log
├── map.md                             # THIS FILE — system blueprint
├── architecture.html                  # Interactive system architecture diagram
├── requirements.txt                   # Python dependencies
├── .env.example                       # API key template (no secrets committed)
├── .gitignore                         # Ignore venv, .env, __pycache__, etc.
│
├── Policy Documents/                  # Source data — 4 insurance policy PDFs
│   ├── ABHI Product Brochure.pdf      #   Aditya Birla — Activ One
│   ├── Care Health Product Brochure.pdf  #   Care Health Insurance
│   ├── HDFC Product Brochure.pdf      #   HDFC ERGO — Optima Secure+
│   └── Niva Bupa Product Brochure.pdf #   Niva Bupa — ReAssure 2.0
│
├── docs/                              # Documentation & case study
│   └── Marsh - Internship Case Study.pdf  # Original problem statement
│
├── app/                               # Application source code
│   ├── main.py                        # Streamlit entry point — orchestrates everything
│   ├── config.py                      # Environment, API keys, constants
│   ├── styles.css                     # Custom CSS — the human-touch design
│   │
│   ├── components/                    # UI building blocks
│   │   ├── __init__.py
│   │   ├── header.py                  # App header — logo, title, subtitle
│   │   ├── input_form.py             # Company name input + policy selector
│   │   ├── pitch_viewer.py           # Display generated pitch slides
│   │   └── audit_panel.py            # Audit results — scores, citations, flags
│   │
│   ├── core/                          # Business logic — the brain
│   │   ├── __init__.py
│   │   ├── company_profile.py        # generateCompanyProfile(company_name)
│   │   ├── pitch_generator.py        # generateMarketingPitch()
│   │   ├── audit_engine.py           # auditPitchContent(pitch_slides, policy_docs)
│   │   └── pptx_builder.py           # Build downloadable PowerPoint files
│   │
│   ├── rag/                           # Retrieval-Augmented Generation pipeline
│   │   ├── __init__.py
│   │   ├── document_loader.py        # PDF → text → structured chunks
│   │   ├── vector_store.py           # Embedding + FAISS index management
│   │   └── retriever.py             # Query → ranked relevant chunks
│   │
│   └── utils/                         # Shared utilities
│       ├── __init__.py
│       ├── prompts.py                # All LLM prompts — centralized, versioned
│       └── helpers.py                # Formatting, validation, shared logic
│
├── output/                            # Generated artifacts
│   ├── sample_pitch_*.pptx           # Generated pitch deck(s)
│   └── audit_report_*.json           # Corresponding audit reports
│
└── write_up/                          # Final submission document
    └── approach_writeup.md            # Approach, tools, design decisions
```

---

## File Manifest — What Each File Does

### Root Level

| File | Type | Purpose |
|------|------|---------|
| `README.md` | Documentation | First thing anyone sees. Project overview, setup instructions, screenshots, architecture summary. Written for evaluators. |
| `mind.md` | Memory | Permanent project context. Design rules (Anti-AI-Look Manifesto), tech stack decisions, file structure reference. Read this before making any change. |
| `log.md` | Tracker | Living document. Task status, phase progress, decision log, blockers. Updated as work progresses. |
| `map.md` | Blueprint | THIS FILE. Complete system reference — file purposes, function signatures, data flows. |
| `architecture.html` | Visualization | Interactive HTML diagram showing system architecture, data flows, and component relationships. |
| `requirements.txt` | Config | All Python package dependencies with pinned versions. |
| `.env.example` | Config | Template for environment variables. Never commit the actual `.env`. |
| `.gitignore` | Config | Excludes: `.env`, `__pycache__/`, `*.pyc`, `venv/`, `.faiss_index/`, `output/*.pptx` (generated files) |

### `Policy Documents/` — Source Data

| File | Insurer | Product | Pages | Key Data |
|------|---------|---------|-------|----------|
| `ABHI Product Brochure.pdf` | Aditya Birla Health Insurance | Activ One | 2 | HealthReturns™, Claim Protect, Super Credit 6X, Super Reload, SI ₹5L–₹6Cr |
| `Care Health Product Brochure.pdf` | Care Health Insurance | Care Health Plan | 4 | Unlimited Recharge, Cumulative Bonus 500%, 7-zone pricing, Wellness 30% |
| `HDFC Product Brochure.pdf` | HDFC ERGO | Optima Secure+ | 16 | Secure 2X, Infinite Benefit, Protect Benefit, Deductible 65%, SI ₹10L–₹2Cr |
| `Niva Bupa Product Brochure.pdf` | Niva Bupa | ReAssure 2.0 | 2 | Platinum/Titanium+, ReAssure+, Booster+ 5X/10X, Live Healthy 30% |

### `app/` — Application Code

#### Entry Point

| File | Key Functions | Description |
|------|---------------|-------------|
| `main.py` | `main()` | Streamlit app entry. Loads CSS, initializes RAG, renders UI components, orchestrates the generate → audit → download flow. Single-page layout. |
| `config.py` | `get_api_key()`, `POLICY_DIR`, `OUTPUT_DIR` | Loads `.env`, exposes constants. No secrets hardcoded. |
| `styles.css` | — | Custom CSS overriding Streamlit defaults. Implements the Anti-AI-Look Manifesto from `mind.md`. Inter font, warm neutrals, left-aligned, minimal. |

#### `app/components/` — UI Components

| File | Key Functions | Description |
|------|---------------|-------------|
| `header.py` | `render_header()` | Top section: app title, one-line description. No logo image — typographic only. Clean, editorial. |
| `input_form.py` | `render_input_form()` → `(company_name, selected_policies)` | Company name text input + multi-select for policy documents + Generate button. Validation: both fields required. |
| `pitch_viewer.py` | `render_pitch(pitch_data)` | Displays generated pitch content as readable slides. Each slide is a section with proper headings. Shows slide number. |
| `audit_panel.py` | `render_audit(audit_report)` | Shows: overall confidence %, per-claim breakdown (verified/partial/unverifiable), source citations, flagged items. Approve/Edit/Reject buttons. |

#### `app/core/` — Business Logic

| File | Key Functions | Signature | Description |
|------|---------------|-----------|-------------|
| `company_profile.py` | `generate_company_profile()` | `(company_name: str) → CompanyProfile` | Calls Gemini to research company. Returns: industry, size, HQ, key_risks, insurance_needs. Unverified fields marked `[Assumed]`. |
| `pitch_generator.py` | `generate_marketing_pitch()` | `(profile: CompanyProfile, policies: list, retriever: Retriever) → PitchDeck` | Retrieves relevant policy chunks via RAG, then calls Gemini to produce structured 3-5 slide content. Each slide: title + bullet points + source_references. |
| `audit_engine.py` | `audit_pitch_content()` | `(pitch: PitchDeck, policy_docs: list[PolicyDoc]) → AuditReport` | Extracts each factual claim from pitch. For each: searches policy text for supporting evidence. Returns: status (verified/partial/unverifiable), source_text, confidence_score. |
| `pptx_builder.py` | `build_pptx()` | `(pitch: PitchDeck, profile: CompanyProfile) → bytes` | Creates PowerPoint using `python-pptx`. Clean slide design: title layout, content layout, recommendation layout. Returns file bytes for download. |

#### `app/rag/` — Retrieval-Augmented Generation

| File | Key Functions | Signature | Description |
|------|---------------|-----------|-------------|
| `document_loader.py` | `load_policy_documents()` | `(pdf_paths: list[str]) → list[DocumentChunk]` | Reads PDFs with PyPDF2. Chunks by logical sections (not arbitrary character count). Each chunk has: text, source_file, page_number, section_type. |
| `vector_store.py` | `build_index()`, `load_index()` | Various | Generates embeddings (Gemini or sentence-transformers). Builds FAISS index. Saves/loads from disk at `.faiss_index/`. |
| `retriever.py` | `retrieve()` | `(query: str, top_k: int = 8) → list[RetrievalResult]` | Takes a natural language query, returns top-k relevant chunks with similarity scores and full metadata. |

#### `app/utils/` — Shared Utilities

| File | Key Contents | Description |
|------|-------------|-------------|
| `prompts.py` | `COMPANY_PROFILE_PROMPT`, `PITCH_GENERATION_PROMPT`, `AUDIT_PROMPT` | Every LLM prompt lives here. Centralized for consistency. Each prompt has explicit grounding instructions: "Only cite benefits found in the provided policy text." |
| `helpers.py` | `format_currency()`, `validate_company_name()`, `sanitize_text()` | Small shared functions used across modules. |

---

## Data Flow — Step by Step

```
USER INPUT
  │
  ├── company_name: "Infosys"
  └── selected_policies: ["HDFC", "Care Health"]
         │
         ▼
┌─────────────────────────────────┐
│  1. generateCompanyProfile()     │
│     Input:  "Infosys"           │
│     Source: Gemini LLM          │
│     Output: CompanyProfile {    │
│       industry: "IT Services"   │
│       size: "300,000+"          │
│       risks: ["tech workforce   │
│         burnout", "global ops"] │
│     }                           │
└──────────┬──────────────────────┘
           │
           ▼
┌─────────────────────────────────┐
│  2. RAG Retrieval               │
│     Input:  CompanyProfile +    │
│             selected policies   │
│     Source: FAISS vector store  │
│     Output: top-k policy chunks │
│             with source metadata│
└──────────┬──────────────────────┘
           │
           ▼
┌─────────────────────────────────┐
│  3. generateMarketingPitch()     │
│     Input:  profile + chunks    │
│     Source: Gemini LLM          │
│     Output: PitchDeck {         │
│       slides: [                 │
│         {title, bullets,        │
│          source_refs}           │
│       ]                         │
│     }                           │
└──────────┬──────────────────────┘
           │
     ┌─────┴─────┐
     ▼           ▼
┌──────────┐ ┌──────────────────────┐
│ 4a. PPTX │ │ 4b. auditPitchContent│
│ Builder  │ │   Input: slides +    │
│          │ │          policy docs  │
│ Output:  │ │   Output: AuditReport│
│ .pptx    │ │   {per_claim_status, │
│ file     │ │    confidence_score}  │
└──────────┘ └──────────────────────┘
     │                │
     ▼                ▼
┌─────────────────────────────────┐
│  5. UI Display                  │
│     - Pitch slides (readable)   │
│     - PPTX download button      │
│     - Audit report panel        │
│     - Approve / Edit / Reject   │
└─────────────────────────────────┘
```

---

## Data Models

```python
@dataclass
class CompanyProfile:
    name: str
    industry: str
    size: str               # employee count or revenue
    headquarters: str
    key_risks: list[str]    # business/health risks
    insurance_needs: list[str]
    assumptions: list[str]  # items marked [Assumed]

@dataclass
class DocumentChunk:
    text: str
    source_file: str        # e.g., "HDFC Product Brochure.pdf"
    page_number: int
    section_type: str       # e.g., "benefits", "exclusions", "pricing"
    insurer: str            # e.g., "HDFC ERGO"
    product_name: str       # e.g., "Optima Secure+"

@dataclass
class RetrievalResult:
    chunk: DocumentChunk
    similarity_score: float

@dataclass
class SlideContent:
    slide_number: int
    title: str
    bullets: list[str]
    source_references: list[str]  # which policy clauses support this

@dataclass
class PitchDeck:
    company: str
    slides: list[SlideContent]
    recommended_policy: str
    generated_at: str

@dataclass
class ClaimAudit:
    claim_text: str
    status: str             # "verified" | "partial" | "unverifiable"
    confidence: float       # 0.0 to 1.0
    source_text: str        # matching policy text (if found)
    source_file: str        # which PDF
    source_page: int        # which page

@dataclass
class AuditReport:
    overall_confidence: float
    total_claims: int
    verified: int
    partial: int
    unverifiable: int
    claims: list[ClaimAudit]
    generated_at: str
```

---

## Dependency Graph

```
main.py
  ├── config.py
  ├── styles.css
  ├── components/header.py
  ├── components/input_form.py
  ├── components/pitch_viewer.py
  ├── components/audit_panel.py
  ├── core/company_profile.py
  │     └── utils/prompts.py
  ├── core/pitch_generator.py
  │     ├── utils/prompts.py
  │     └── rag/retriever.py
  │           └── rag/vector_store.py
  │                 └── rag/document_loader.py
  ├── core/audit_engine.py
  │     └── utils/prompts.py
  └── core/pptx_builder.py
```

---

## External Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| `streamlit` | ≥1.38 | Web UI framework |
| `google-generativeai` | ≥0.8 | Gemini API client |
| `langchain` | ≥0.3 | RAG orchestration |
| `langchain-google-genai` | ≥2.0 | LangChain Gemini integration |
| `faiss-cpu` | ≥1.8 | Vector similarity search |
| `python-pptx` | ≥1.0 | PowerPoint generation |
| `PyPDF2` | ≥3.0 | PDF text extraction |
| `python-dotenv` | ≥1.0 | Environment variable loading |
