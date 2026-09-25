# LOG — Marsh AI Pitch Generator

> Last Updated: 2026-09-25 13:30 IST

---

## Status Summary

| Phase | Status | Progress |
|-------|--------|----------|
| Phase 0 — Setup & Foundation | 🟡 In Progress | ████████░░ 80% |
| Phase 1 — RAG Pipeline | ⚪ Not Started | ░░░░░░░░░░ 0% |
| Phase 2 — Core Functions | ⚪ Not Started | ░░░░░░░░░░ 0% |
| Phase 3 — UI & Styling | ⚪ Not Started | ░░░░░░░░░░ 0% |
| Phase 4 — Audit Engine | ⚪ Not Started | ░░░░░░░░░░ 0% |
| Phase 5 — PPT Generation | ⚪ Not Started | ░░░░░░░░░░ 0% |
| Phase 6 — Integration & Polish | ⚪ Not Started | ░░░░░░░░░░ 0% |
| Phase 7 — Deliverables | ⚪ Not Started | ░░░░░░░░░░ 0% |

---

## Phase 0 — Setup & Foundation

### Task 0.1: Project Analysis ✅
- **Status**: Done
- **Date**: 2026-09-24
- **Output**: Read all 5 PDFs (1 case study + 4 policy brochures), documented everything in project-analysis artifact
- **Notes**: Case study has 2 challenges, 4 deliverables. 4 policy docs cover ABHI, Care Health, HDFC ERGO, Niva Bupa

### Task 0.2: Design Philosophy & Memory System ✅
- **Status**: Done
- **Date**: 2026-09-24
- **Output**: `mind.md` (project context + anti-AI design rules), `log.md` (this file)
- **Notes**: Permanent design rules established — minimalist, human-feel, no typical AI aesthetics

### Task 0.3: Project Structure & Dependencies ✅
- **Status**: Done
- **Date**: 2026-09-25
- **Output**: Folder tree created (`app/components/`, `app/core/`, `app/rag/`, `app/utils/`, `output/`, `write_up/`, `docs/`), `__init__.py` files, `.env.example`, `.gitignore`
- **Notes**: Case study PDF moved to `docs/` folder for clean organization

### Task 0.4: System Documentation & Architecture ✅
- **Status**: Done
- **Date**: 2026-09-25
- **Output**: `map.md` (complete system blueprint), `architecture.html` (interactive diagram), `README.md`
- **Notes**: map.md covers every file, function signature, data model, dependency graph. Architecture HTML styled with same human-touch aesthetic.

### Task 0.5: GitHub Repository ✅
- **Status**: Done
- **Date**: 2026-09-25
- **Output**: https://github.com/AbhiAJ001/Marsh-Case-Study
- **Notes**: Public repo with professional README showcasing AI usage practices and agentic development workflow

### Task 0.6: API Key Configuration
- **Status**: ⚪ Not Started
- **What**: Set up Gemini API key in config, create `app/config.py` with safe key handling
- **Output**: `app/config.py`, `.env`

---

## Phase 1 — RAG Pipeline (Policy Document Intelligence)

### Task 1.1: PDF Ingestion & Chunking
- **Status**: ⚪ Not Started
- **What**: Load all 4 policy PDFs, extract text, chunk into meaningful sections (not arbitrary 500-char splits — respect document structure)
- **Output**: `app/rag/document_loader.py`
- **Key Decision**: Chunk by logical sections (benefits, exclusions, pricing, eligibility) not by character count

### Task 1.2: Vector Store (FAISS)
- **Status**: ⚪ Not Started
- **What**: Generate embeddings for chunks, build FAISS index, persist to disk
- **Output**: `app/rag/vector_store.py`, saved FAISS index
- **Key Decision**: Use Gemini embedding model or sentence-transformers

### Task 1.3: Retriever
- **Status**: ⚪ Not Started
- **What**: Query function that takes a question/context and returns top-k relevant policy chunks with metadata (which document, which section)
- **Output**: `app/rag/retriever.py`
- **Key Decision**: Top-k = 8-10, include source document name and page in metadata

---

## Phase 2 — Core Functions

### Task 2.1: generateCompanyProfile(company_name)
- **Status**: ⚪ Not Started
- **What**: Takes company name → returns structured profile: industry, employee count, HQ, key business risks, health insurance needs. Falls back to clearly-labelled assumptions.
- **Output**: `app/core/company_profile.py`
- **Key Decision**: Use Gemini's knowledge; if uncertain, prefix with "[Assumed]" label

### Task 2.2: generateMarketingPitch()
- **Status**: ⚪ Not Started
- **What**: Takes company profile + selected policies + RAG context → produces structured pitch content for 3-5 slides
- **Output**: `app/core/pitch_generator.py`
- **Slide Structure**:
  - Slide 1: Company Overview & Risk Landscape
  - Slide 2: Why Marsh (trust, network, expertise)
  - Slide 3-4: Policy Benefits Mapped to Company's Exposures
  - Slide 5: Final Recommended Policy & Next Steps

### Task 2.3: All LLM Prompts
- **Status**: ⚪ Not Started
- **What**: Centralized prompt file — every prompt used in the app, well-structured, with system instructions for grounding
- **Output**: `app/utils/prompts.py`
- **Key Decision**: Prompts enforce grounding — "only cite benefits found in the provided policy text"

---

## Phase 3 — UI & Styling (The Human Touch)

### Task 3.1: Custom CSS
- **Status**: ⚪ Not Started
- **What**: Full custom stylesheet following mind.md design rules. Override all Streamlit defaults.
- **Output**: `app/styles.css`
- **Rules**: See mind.md Anti-AI-Look Manifesto. Inter font, warm neutrals, left-aligned, minimal borders, no gradients.

### Task 3.2: App Layout & Components
- **Status**: ⚪ Not Started
- **What**: Build the main Streamlit app — header, input form (company name + policy selector + generate button), results area (pitch viewer + audit panel)
- **Output**: `app/main.py`, `app/components/*.py`
- **Key Decision**: Single page app. No sidebar. Clean vertical flow: input → loading → results.

### Task 3.3: Empty States & Error Handling
- **Status**: ⚪ Not Started
- **What**: Thoughtful empty states, loading states, error messages. No "🤷 No data found". Professional microcopy.
- **Output**: Integrated into components
- **Key Decision**: Loading shows a subtle progress indicator with stage labels ("Researching company...", "Matching policy benefits...", "Building pitch...")

---

## Phase 4 — Audit Engine (Anti-Hallucination)

### Task 4.1: auditPitchContent(pitch_slides, policy_docs)
- **Status**: ⚪ Not Started
- **What**: For each claim in the pitch, find the closest matching text in the policy documents. Classify as: ✅ Verified (with source), ⚠️ Partially Supported, ❌ Unverifiable.
- **Output**: `app/core/audit_engine.py`
- **Returns**: Structured audit report with per-claim results

### Task 4.2: Audit Report Display
- **Status**: ⚪ Not Started
- **What**: UI component showing the audit results — overall confidence score, per-slide breakdown, flagged items highlighted. Advisor can approve/edit/reject.
- **Output**: `app/components/audit_panel.py`
- **Key Decision**: Traffic light colors (green/amber/red) for claim status. Overall score as percentage.

---

## Phase 5 — PPT Generation

### Task 5.1: PowerPoint Builder
- **Status**: ⚪ Not Started
- **What**: Takes structured pitch content → creates a clean, professional 3-5 slide PPTX file
- **Output**: `app/core/pptx_builder.py`
- **Key Decision**: Clean slide design (not AI-looking). Marsh branding. Proper layouts with title + content.

### Task 5.2: Sample Pitch Deck
- **Status**: ⚪ Not Started
- **What**: Generate at least one complete sample pitch for a real company (e.g., Infosys or TCS)
- **Output**: `output/sample_pitch_[company].pptx`

---

## Phase 6 — Integration & Polish

### Task 6.1: End-to-End Flow Testing
- **Status**: ⚪ Not Started
- **What**: Test complete flow: company input → profile → pitch → audit → PPT download. Fix any breaks.

### Task 6.2: Edge Cases
- **Status**: ⚪ Not Started
- **What**: Test with unknown companies, missing inputs, invalid names, single policy selection, all policies selected.

### Task 6.3: UI Polish
- **Status**: ⚪ Not Started
- **What**: Final CSS tweaks, responsive checks, loading state refinement, microcopy review.

---

## Phase 7 — Deliverables

### Task 7.1: Final Sample Pitch + Audit Report
- **Status**: ⚪ Not Started
- **What**: Generate the submission-ready pitch deck and audit report

### Task 7.2: Write-up Document
- **Status**: ⚪ Not Started
- **What**: Short Word/PDF covering approach, tools/libraries used, key design decisions, challenges faced
- **Output**: `write_up/approach_writeup.pdf`

### Task 7.3: Code Cleanup & Comments
- **Status**: ⚪ Not Started
- **What**: Clean code, add docstrings, remove debug prints, organize imports

---

## Decision Log

| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-09-24 | Streamlit for UI | Fast to build, Python-native, can be heavily customized with CSS |
| 2026-09-24 | Google Gemini for LLM | Free tier available, strong reasoning, good for RAG |
| 2026-09-24 | FAISS for vector store | Lightweight, no server needed, fast similarity search |
| 2026-09-24 | Minimalist/human design | Explicit requirement — app must NOT look AI-generated |
| 2026-09-24 | Chunk by document structure | Better retrieval than arbitrary character splits |

---

## Issues & Blockers

| # | Issue | Status | Resolution |
|---|-------|--------|------------|
| — | None yet | — | — |
