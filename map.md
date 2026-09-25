# MAP — System Blueprint (v2)

> Complete reference of what lives where and why. Every file, every function, every data flow.
> 
> Architecture v2: HTML/CSS/JS frontend, OKF knowledge bundles, Flask API, LangChain fallback.

---

## Directory Tree

```
Marsh-Case-Study/
│
├── README.md                          # Project overview, setup, usage
├── mind.md                            # Permanent project memory + design rules
├── log.md                             # Work tracker + decision log
├── map.md                             # THIS FILE — system blueprint (v2)
├── architecture.html                  # Interactive system architecture diagram
├── requirements.txt                   # Python dependencies
├── .env.example                       # API key template (no secrets committed)
├── .gitignore                         # Ignore venv, .env, __pycache__, etc.
│
├── Policy Documents/                  # Source data — 4 insurance policy PDFs
│   ├── ABHI Product Brochure.pdf
│   ├── Care Health Product Brochure.pdf
│   ├── HDFC Product Brochure.pdf
│   └── Niva Bupa Product Brochure.pdf
│
├── docs/                              # Case study documentation
│   └── Marsh - Internship Case Study.pdf
│
├── knowledge_bundle/                  # OKF bundle — structured policy knowledge
│   ├── index.md                       # Root catalog listing all concept types
│   ├── log.md                         # Chronological change log
│   ├── policies/                      # type: Insurance Policy (4 master docs)
│   ├── coverages/                     # type: Policy Coverage (inpatient, ambulance, etc.)
│   ├── benefits/                      # type: Policy Benefit (bonus, restore, etc.)
│   ├── exclusions/                    # type: Policy Exclusion (waiting periods, etc.)
│   ├── pricing/                       # type: Pricing (SI options, zones, discounts)
│   └── references/                    # type: Reference (why Marsh, etc.)
│
├── frontend/                          # Pure HTML/CSS/JS (no framework)
│   ├── index.html                     # Single-page application
│   ├── css/
│   │   └── styles.css                 # Custom design (Anti-AI-Look Manifesto)
│   └── js/
│       └── app.js                     # Client-side logic, API calls, DOM updates
│
├── app/                               # Python backend (Flask)
│   ├── server.py                      # Flask API — serves frontend + REST endpoints
│   ├── config.py                      # Env loading, API key (first-run prompt)
│   ├── __init__.py
│   ├── core/                          # Business logic
│   │   ├── __init__.py
│   │   ├── company_profile.py         # generateCompanyProfile()
│   │   ├── pitch_generator.py         # generateMarketingPitch()
│   │   ├── audit_engine.py            # auditPitchContent()
│   │   └── pptx_builder.py            # PowerPoint file builder
│   ├── okf/                           # OKF knowledge layer (PRIMARY)
│   │   ├── __init__.py
│   │   ├── bundle_builder.py          # PDF → OKF concept files
│   │   ├── bundle_reader.py           # Parse OKF bundle, traverse concepts
│   │   └── okf_retriever.py           # OKF-aware retrieval with graph links
│   ├── rag/                           # LangChain fallback (SECONDARY)
│   │   ├── __init__.py
│   │   ├── langchain_fallback.py      # Embed OKF docs → FAISS similarity search
│   │   └── vector_store.py            # FAISS index build/load/query
│   └── utils/
│       ├── __init__.py
│       ├── prompts.py                 # All LLM prompts centralized
│       └── helpers.py                 # Shared utilities
│
├── output/                            # Generated artifacts
│   └── .gitkeep
│
└── write_up/                          # Final submission document
    └── .gitkeep
```

---

## API Endpoints (Flask)

| Method | Route | Input | Output | Description |
|--------|-------|-------|--------|-------------|
| `GET` | `/` | — | `index.html` | Serve the frontend |
| `GET` | `/api/policies` | — | `[{name, file, pages}]` | List available policy documents |
| `POST` | `/api/profile` | `{company_name}` | `CompanyProfile` JSON | Research company via Gemini + web search |
| `POST` | `/api/pitch` | `{profile, policies}` | `PitchDeck` JSON | Generate 3-5 slide pitch grounded in OKF concepts |
| `POST` | `/api/audit` | `{pitch, policies}` | `AuditReport` JSON | Trace each claim to source policy text |
| `GET` | `/api/download-pptx` | `?id=<pitch_id>` | `.pptx` file | Download generated PowerPoint |

---

## OKF Concept Schema

Every concept file in `knowledge_bundle/` follows this structure:

```yaml
---
type: Policy Coverage                    # REQUIRED
title: In-Patient Care Coverage          # Display name
description: Covers hospitalisation...   # ~25 word summary
tags: [hospitalisation, inpatient, coverage]
sources:
  - id: hdfc-p5                          # Citation anchor
    resource: "Policy Documents/HDFC Product Brochure.pdf#page=5"
    title: "Section: Hospitalisation Expenses"
generated:
  by: reference_agent/gemini-2.0-flash
  at: 2026-09-25T16:00:00Z
status: stable
---

# In-Patient Care Coverage

Covers medical expenses incurred during hospitalisation...

## Covered Policies
- [HDFC Optima Secure+](../policies/hdfc-optima-secure-plus.md) — up to Sum Insured
- [Care Health](../policies/care-health.md) — up to Sum Insured

## Related
- Exclusions: [Waiting Periods](../exclusions/waiting-periods.md)
- Benefits: [Automatic Restore](../benefits/automatic-restore.md)

[^hdfc-p5]: HDFC Product Brochure, Page 5, "Hospitalisation Expenses" section
```

---

## Data Flow

```
USER (Browser)
  │
  ├── company_name: "Infosys"
  └── selected_policies: ["HDFC", "Care Health"]
         │
         ▼  POST /api/profile
┌─────────────────────────────────────┐
│  1. generateCompanyProfile()         │
│     Gemini LLM + web search          │
│     → CompanyProfile {industry,      │
│       size, risks, insurance_needs}  │
└──────────┬──────────────────────────┘
           │
           ▼  POST /api/pitch
┌─────────────────────────────────────┐
│  2. OKF Retrieval (primary)          │
│     Read index.md → navigate to      │
│     relevant concepts by type/tag    │
│     → Coverages, Benefits, Pricing   │
│     with cross-linked Exclusions     │
│                                      │
│  3. LangChain Fallback (if needed)   │
│     FAISS similarity search on       │
│     OKF concept embeddings           │
└──────────┬──────────────────────────┘
           │
           ▼
┌─────────────────────────────────────┐
│  4. generateMarketingPitch()         │
│     Profile + OKF concepts → Gemini  │
│     → 3-5 slides with source refs    │
└──────────┬──────────────────────────┘
           │
     ┌─────┴─────┐
     ▼           ▼  POST /api/audit
┌──────────┐ ┌──────────────────────┐
│ 5a. PPTX │ │ 5b. auditPitchContent│
│ Builder  │ │   Each claim matched │
│ → .pptx  │ │   to OKF sources[]   │
│   file   │ │   → AuditReport      │
└──────────┘ └──────────────────────┘
     │                │
     ▼                ▼
┌─────────────────────────────────────┐
│  6. Frontend Display                 │
│     Pitch slides + PPTX download     │
│     Audit panel + Approve/Reject     │
└─────────────────────────────────────┘
```

---

## Key Decisions (v2)

| Decision | Rationale |
|----------|-----------|
| HTML/CSS/JS over Streamlit | Full design control, no framework constraints, looks handcrafted |
| OKF over raw PDF chunking | Structured knowledge with provenance, cross-linking, lifecycle metadata |
| LangChain as fallback only | OKF graph retrieval is primary; FAISS fills gaps when traversal isn't enough |
| Flask over FastAPI | Simpler, sufficient for this scope, serves static files natively |
| No React/Vue/Angular | Internship case study — clean vanilla code demonstrates fundamentals |
| Web search for company data | Real-time company info, not just LLM's training data |
| Gemini API key on first run | User doesn't have one yet; config.py prompts and saves to .env |
