# SESSION LOG — Marsh Case Study: AI-Powered Insurance Pitch Generator
## Project Repository: https://github.com/AbhiAJ001/Marsh-Case-Study

---

## PROJECT OVERVIEW

**Goal**: Build an AI-powered insurance pitch generation system for Marsh (NMIMS 2026 Case Study).  
Given a company name + selected insurance policies, the system:
1. Researches the company using LLM intelligence
2. Retrieves structured policy knowledge from OKF bundles + FAISS vector store
3. Generates a tailored 5-slide marketing pitch grounded in real policy documents
4. Audits every claim in the pitch for accuracy
5. Exports the pitch as a downloadable PowerPoint (PPTX)

**Tech Stack**: Python · Flask · Vanilla JS/HTML/CSS · Google Gemini · Groq · LangChain · FAISS · OKF · python-pptx

---

## SESSION TIMELINE

---

### 📌 Sep 25, 2026 — 13:29 IST | Initial Scaffold
**Commit**: `5e4c413` — *Initial project scaffold: architecture, documentation, and folder structure*

**What was done**:
- Created the GitHub repository `AbhiAJ001/Marsh-Case-Study`
- Set up project folder structure: `app/`, `frontend/`, `knowledge_bundle/`, `Policy Documents/`
- Created `README.md`, `map.md` (system map), `mind.md` (design principles), `log.md`
- Created `architecture.html` — visual system architecture diagram with full agent flow
- Defined the **Anti-AI-Look Manifesto** (permanent design rule):
  - No purple-to-blue gradients, no glassmorphism, no emoji UI
  - Warm neutrals + ONE accent (slate blue), Inter typography
  - "Notion meets Linear meets Stripe Docs" aesthetic

---

### 📌 Sep 25, 2026 — 16:23 IST | Architecture Redesign
**Commit**: `32d2bef` — *Architecture v2: OKF knowledge layer + HTML/CSS/JS frontend + Flask API*

**What was done**:
- Replaced initial Streamlit plan with **plain HTML + CSS + Vanilla JS** (per user request)
- Integrated **OKF (Open Knowledge Format)** as the primary knowledge layer
  - Cloned `https://github.com/GoogleCloudPlatform/knowledge-catalog.git`
  - Ran OKF Research subagent to understand the bundle format (YAML frontmatter + Markdown body)
- Defined fallback: **LangChain + FAISS** for vector similarity search
- Defined Flask as the REST API bridge between frontend and Python AI modules
- Architecture decision: Frontend ↔ Flask ↔ Agents (OKF / LangChain / Gemini)

---

### 📌 Sep 25, 2026 — 23:25 IST | Phase 1: OKF Knowledge Bundle
**Commit**: `778b8ff` — *Phase 1: OKF Knowledge Bundle — complete*

**Files created**:
- `app/okf/bundle_builder.py` — Reads PDF policy documents and generates OKF Markdown concept files
- `app/okf/bundle_reader.py` — Loads, indexes, and traverses OKF concept files
- `app/okf/okf_retriever.py` — Graph-aware retriever (type-based, tag-based, graph-traversal, keyword search)
- `knowledge_bundle/` — 23 OKF concept files generated from 4 insurance PDFs:
  - `policies/` — 4 master policy docs (ABHI Activ One, Care Health, HDFC ERGO Optima Secure+, Niva Bupa ReAssure 2.0)
  - `benefits/` — 9 benefit concepts (HealthReturns, Super Reload, Infinite Benefit, etc.)
  - `coverages/` — 3 coverage concepts (inpatient care, daycare, pre/post hospitalisation)
  - `exclusions/` — 3 exclusion concepts (waiting periods, standard exclusions, PED)
  - `pricing/` — 4 pricing concepts (sum insured options, zone pricing, deductibles, renewals)

**Key decision**: OKF uses YAML frontmatter (`id`, `type`, `tags`, `links`) + Markdown body. Cross-links enable graph traversal for richer context retrieval.

---

### 📌 Sep 25, 2026 — 23:26 IST | Phase 2: LangChain Fallback RAG
**Commit**: `c1ea2d6` — *Phase 2: LangChain Fallback RAG — complete*

**Files created**:
- `app/rag/vector_store.py` — FAISS vector index builder from PDF documents
- `app/rag/langchain_fallback.py` — Semantic search fallback when OKF context is thin (<5 concepts)

**Bug fixed**: `langchain.schema.Document` → `langchain_core.documents.Document` (LangChain v0.3 breaking change)

---

### 📌 Sep 25, 2026 — 23:28 IST | Phase 3: Core AI Functions
**Commit**: `39e6226` — *Phase 3: Core AI Functions — complete*

**Files created**:
- `app/utils/prompts.py` — All LLM prompts in one place (COMPANY_PROFILE_PROMPT, PITCH_GENERATION_PROMPT, AUDIT_PROMPT)
- `app/core/company_profile.py` — Generates structured company profile JSON via LLM
- `app/core/pitch_generator.py` — Combines OKF context + company profile → pitch JSON
- `app/core/audit_engine.py` — Verifies pitch claims against OKF source knowledge
- `app/config.py` — Loads `.env`, manages API key, returns config dict

**LLM used**: Google Gemini (via `google-generativeai` package)

---

### 📌 Sep 25, 2026 — 23:31 IST | Phase 4: Frontend
**Commit**: `b558106` — *Phase 4: Frontend — HTML/CSS/JS, human-crafted design*

**Files created**:
- `frontend/index.html` — 4-step UI (Company Input → Profile → Pitch → Audit)
- `frontend/css/styles.css` — Full design system: warm neutrals, Inter font, strict typography hierarchy, minimal shadows
- `frontend/js/app.js` — Vanilla JS orchestration: fetch APIs, render profile/pitch/audit, error handling

**Design rules enforced**:
- Left-aligned content, generous whitespace
- No entrance animations, no glassmorphism
- Status badge (READY/LOADING) in top-right corner
- Step numbers with large, clean headings

---

### 📌 Sep 25, 2026 — 23:33 IST | Phase 5-7: Server, Audit, PPTX
**Commit**: `6fe98b5` — *Phase 5-7: Flask server, Audit engine, PPTX builder — complete*

**Files created**:
- `app/server.py` — Flask REST API with 5 routes: `/api/policies`, `/api/profile`, `/api/pitch`, `/api/audit`, `/api/download-pptx`
- `app/core/pptx_builder.py` — Generates PowerPoint from pitch JSON using `python-pptx`

**Run command established**: `python -m app.server` from project root (not `python app/server.py`)

---

### 🐛 Sep 25, 2026 — 23:54 IST | Bug Fix: langchain-community
**Commit**: `9b87140` — *Fix: Add missing langchain-community to requirements and update Document import*

- Added `langchain-community>=0.3` to `requirements.txt`
- Fixed import: `from langchain_core.documents import Document`

---

### 🐛 Sep 26, 2026 — 00:12 IST | Bug Fix: Dead Gemini Model
**Commit**: `b218a78` — *Fix: update model to gemini-3.8-flash and remove unsupported google_search_retrieval tool*

- `gemini-2.0-flash` → **DEAD** (404 Not Found as of Sep 2026)
- Updated all 3 AI modules to `gemini-3.8-flash`
- Removed `google_search_retrieval` tool (not compatible with `gemini-3.8-flash`)

---

### 🐛 Sep 26, 2026 — 00:19 IST | Bug Fix: Rate Limit Retries
**Commit**: `680f5c2` — *Fix: Add retry logic for Gemini 429 quota rate limits*

- Added retry loops (max 3 attempts, 35s sleep) to all 3 AI core files
- Gemini free tier limit: **20 requests/day**

---

### 🐛 Sep 26, 2026 — 00:53 IST | Bug Fix: Stale UI (Infosys → Alan Scott issue)
**Commit**: `ca819ca` — *Fix: Clear stale UI state on new search; improve error messages from API*

**Problem**: User searched "Infosys" → then "alan scott enterprises ltd" → old Infosys card remained visible when new request failed  
**Fix**:
- Added `resetResults()` in `app.js` — clears all sections before every new search
- Improved error extraction from JSON response body
- `company_profile.py` — raises `ValueError`/`RuntimeError` with human-readable messages instead of silent fallback dicts

---

### ✨ Sep 26, 2026 — 01:16 IST | Feature: Groq Fallback Router
**Commit**: `b2a18d5` — *Feat: Add Groq fallback router (Gemini → Groq GPT-OSS-120B → Qwen → GPT-OSS-20B)*

**Background**: Gemini free tier = 20 req/day. After hitting the limit, the whole app stops working.  
**Solution**: Added `app/utils/model_router.py` — automatic fallback chain:

```
Gemini 3.8-flash  →  Groq GPT-OSS-120B  →  Groq Qwen3.8-27B  →  Groq GPT-OSS-20B
```

- Groq API key added to `.env`: `GROQ_API_KEY=gsk_...`
- All 3 AI core modules refactored to use `model_router.generate()`
- Skip keywords: `quota`, `rate limit`, `429`, `resource exhausted`, `413`, `tpm`, `decommissioned`

---

### 🐛 Sep 26, 2026 — 01:24 IST | Bug Fix: Groq 413 Token Limit
**Commit**: `b02db3c` — *Fix: Handle Groq 413 TPM limit - truncate prompts and cap output tokens for Groq*

**Problem**: Groq free tier = 8,000 TPM. Pitch prompt was 8,415 tokens → `413 Request Too Large`  
**Fix**:
- `model_router.py` — `_prepare_groq_prompt()` truncates prompt to 5,000 chars before sending to Groq
- Groq output capped at `GROQ_MAX_OUTPUT_TOKENS = 1500`
- `413` added to skip-keywords list → treated as "switch provider"

---

### 🐛 Sep 26, 2026 — 01:34 IST | Bug Fix: Audit Wrong JSON Shape
**Commit**: `8b441d8` — *Fix: Audit - graceful fallback for wrong JSON shape; better frontend error messages*

- Backend: validates `audit_summary` key exists in response; falls back if not
- Frontend: `normaliseAudit()` function — handles any JSON shape without crashing UI
- Proper error extraction from response body in `handleAudit()`

---

### 🐛 Sep 26, 2026 — 01:44 IST | Bug Fix: Error Pitch Displayed as Slides
**Commit**: `ba29f34` — *Fix: Truncate OKF context at source to fit Groq TPM; detect error pitch in frontend*

**Problem**: When pitch JSON parse failed, `{"error": true, "slides": [...]}` was rendered as a valid pitch  
**Fix**:
- `pitch_generator.py` — OKF context capped at **2,500 chars**, profile JSON at **800 chars** before prompt assembly
- `app.js` — detects `pitchData.error === true` and shows clear error message, never renders broken slides

---

### ✨ Sep 26, 2026 — 10:41 IST | Feature: Multi-Agent RAG Architecture v2
**Commit**: `2f8a93c` — *Feat: Multi-agent RAG architecture v2 - parallel retrieval, parallel slide writers, orchestrator*

**Motivation**: Single-agent approach had one LLM call doing everything → truncation, generic output, failures  
**Solution**: Full multi-agent system with specialised agents running in parallel

**New files**:
```
app/agents/
├── base_agent.py              ← Abstract BaseAgent, AgentResult, async wrapper
├── orchestrator.py            ← PitchOrchestrator — coordinates all agents
├── research/
│   └── research_agent.py      ← Phase A: Company research (ResearchAgent)
├── retrieval/
│   └── policy_retrieval_agent.py  ← Phase B: One agent per policy (parallel)
├── pitch/
│   └── slide_agents.py        ← Phase C: 5 specialised slide writers (parallel)
│       ├── ExecutiveSummaryAgent
│       ├── RiskAlignmentAgent
│       ├── PolicyComparisonAgent
│       ├── ROIValueAgent
│       └── CallToActionAgent
└── audit/
    └── fact_checker_agent.py  ← Phase D: Claim-level fact checking
```

**Execution flow**:
```
Phase A:  ResearchAgent                     (sequential — needed first)
Phase B:  PolicyRetrievalAgents × N         (PARALLEL via asyncio.gather)
Phase C:  SlideWriterAgents × 5             (PARALLEL via asyncio.gather)
Phase D:  FactCheckerAgent (on-demand)
```

**Improvements vs v1**:
| | v1 | v2 |
|---|---|---|
| Policy retrieval | All merged, truncated | Per-policy, full budget |
| Slide writing | 1 call for all 5 slides | 5 parallel specialised agents |
| Token per call | 8,000+ (hit limits) | 1,500–2,000 per agent |
| Audit | One batch, often fails | Slide-by-slide micro-prompts |

**`app/server.py` updated** to route all requests through `PitchOrchestrator` — same API contract, zero frontend changes needed.

---

### ✨ Sep 26, 2026 — 12:01 IST | Model Router v2 — 5 Providers, 7 Keys
**Commit**: `99679e2` — *Feat: Model Router v2 - 5 providers, 7 API keys, agent-specific routing chains*

**New API keys integrated**:
- Gemini (updated key), Groq (updated key)
- Mistral key 1 + key 2 (`mistral-large-latest`, `mistral-medium-latest`)
- OpenRouter key 1 + key 2 (`llama-3.3-70b-instruct`, `gemini-2.0-flash-exp:free`)
- NVIDIA NIM (`meta/llama-3.1-70b-instruct`)

**Model chain** (9 slots):
```
Gemini → OpenRouter Llama → NVIDIA Llama → Mistral Large → Groq 120B
→ OpenRouter Gemini → Mistral Medium → Groq Qwen → Groq 20B
```

**Agent-specific routing**:
- `task_type="research"` → Gemini first
- `task_type="pitch"` → OpenRouter/NVIDIA first
- `task_type="audit"` → Mistral first

**New package**: `openai>=1.40` — used as OpenAI-compatible client for OpenRouter, NVIDIA, Mistral

---

### 🐛 Sep 26, 2026 — 18:11 IST | Fix: All 5 Slide Agents Get task_type="pitch"
**Commit**: `f8fa3a0` — *Fix: All 5 slide agents now use task_type='pitch' for smart routing*

**Problem**: Only `ExecutiveSummaryAgent` had `task_type="pitch"`. The other 4 agents (`RiskAlignmentAgent`, `PolicyComparisonAgent`, `ROIValueAgent`, `CallToActionAgent`) used `"general"` routing — meaning Gemini was tried first even though OpenRouter Llama-3.3-70B and NVIDIA Llama-3.1-70B are better at structured creative JSON.

**Fix**: Added `task_type = "pitch"` to all 4 remaining slide agents.

---

### ✨ Sep 26, 2026 — 18:15 IST | Feat: Step Progress Indicators + Full Mobile Responsiveness
**Commit**: `8ca9b7f` — *Feat: Step-by-step loading indicators + full mobile responsiveness*

**Loading Indicators**:
- Added inline 3-step progress tracker between input form and results
- Step 1: **Researching Company** — spinner while API call runs, green tick + industry/size summary on done
- Step 2: **Retrieving Policy Knowledge** — shows count of OKF bundles loaded
- Step 3: **Writing Pitch Slides** — shows "5 specialist agents writing in parallel", tick + slide count on done
- Each step icon: idle (number) → running (spinning ring) → done (green ✓)
- Generate button disabled during generation to prevent double-submit
- Enter key on company name input now submits the form

**Mobile Responsiveness**:
- **768px (tablet)**: reduced container padding, smaller section titles
- **640px (mobile)**: input grid → 1 column; buttons → full-width stacked; profile rows → vertical; audit stats wrap
- **400px (small phone)**: smaller font base, audit stats vertical stack, claim header stacks vertically
- All cards (profile, slide, audit) reduce padding on small screens


**Commit**: `b9f9e0c` — *Fix: Audit now works - slide-by-slide micro-prompts bypass Groq TPM limits*

**Problem**: Combined audit prompt (5 slides + 4 policy contexts) = 10,000+ tokens → Groq truncates → model returns knowledge dump → fallback "0 claims"  
**Fix**: `FactCheckerAgent` now audits **one slide at a time**:
- Each micro-audit = ~1,000 tokens input + 400 tokens output → always within 8,000 TPM limit
- Results merged into unified report with per-claim `VERIFIED/UNVERIFIED/INACCURATE/ASSUMPTION` status
- Real output: "5 claims, 2 verified, 3 flagged" with confidence scores and notes

---

## FINAL SYSTEM ARCHITECTURE

```
User (Browser)
    │
    ▼
frontend/index.html + styles.css + app.js  (Vanilla JS, Anti-AI-Look design)
    │
    ▼ HTTP (REST)
app/server.py  (Flask, 5 routes)
    │
    ▼
app/agents/orchestrator.py  (PitchOrchestrator)
    │
    ├── Phase A → ResearchAgent         → LLM: company profile JSON
    │
    ├── Phase B → PolicyRetrievalAgent  → OKF bundle + FAISS (per policy, parallel)
    │              × N policies
    │
    ├── Phase C → SlideWriterAgents     → LLM: one slide each (parallel)
    │              × 5 slides
    │
    └── Phase D → FactCheckerAgent      → LLM: micro-audit per slide
                  (on-demand)
    │
    ▼
app/utils/model_router.py  (Gemini → Groq GPT-OSS-120B → Qwen → GPT-OSS-20B)
    │
    ├── Google Gemini 3.8-flash  (primary, 20 req/day free)
    └── Groq (fallback, 8000 TPM free tier)
```

---

## ALL FILES IN PROJECT

| File | Purpose |
|---|---|
| `app/server.py` | Flask REST API — 5 routes |
| `app/config.py` | Loads `.env`, returns config dict |
| `app/agents/base_agent.py` | Abstract agent base class + AgentResult |
| `app/agents/orchestrator.py` | Coordinates all agents (parallel + sequential) |
| `app/agents/research/research_agent.py` | Company profile generation |
| `app/agents/retrieval/policy_retrieval_agent.py` | Per-policy OKF+FAISS retrieval |
| `app/agents/pitch/slide_agents.py` | 5 specialised slide writer agents |
| `app/agents/audit/fact_checker_agent.py` | Slide-by-slide claim verification |
| `app/core/company_profile.py` | v1 profile generator (kept for reference) |
| `app/core/pitch_generator.py` | v1 pitch generator (kept for reference) |
| `app/core/audit_engine.py` | v1 audit engine (kept for reference) |
| `app/core/pptx_builder.py` | PowerPoint export |
| `app/okf/bundle_builder.py` | Builds OKF concept files from PDFs |
| `app/okf/bundle_reader.py` | Loads and indexes OKF bundle |
| `app/okf/okf_retriever.py` | Graph-aware OKF retriever |
| `app/rag/vector_store.py` | FAISS vector index builder |
| `app/rag/langchain_fallback.py` | LangChain semantic search fallback |
| `app/utils/model_router.py` | Multi-provider LLM router with auto-fallback |
| `app/utils/prompts.py` | All LLM prompts centralised |
| `frontend/index.html` | Main UI |
| `frontend/css/styles.css` | Design system (Anti-AI-Look) |
| `frontend/js/app.js` | Frontend orchestration (Vanilla JS) |
| `knowledge_bundle/` | 23 OKF concept files from 4 policy PDFs |
| `architecture.html` | Visual system architecture diagram |
| `map.md` | System map (file index) |
| `mind.md` | Design principles + permanent rules |
| `requirements.txt` | Python dependencies |
| `.env` | API keys (gitignored) |

---

## API KEYS USED

| Provider | Key Location | Limit |
|---|---|---|
| Google Gemini | `.env → GOOGLE_API_KEY` | 20 req/day (free tier) |
| Groq | `.env → GROQ_API_KEY` | 8,000 TPM (free tier) |

---

## GIT COMMIT HISTORY

| # | Date | Commit | Message |
|---|---|---|---|
| 1 | Sep 25 13:29 | `5e4c413` | Initial project scaffold |
| 2 | Sep 25 13:33 | `363fb22` | Update log.md: Phase 0 complete |
| 3 | Sep 25 16:23 | `32d2bef` | Architecture v2: OKF + HTML/JS frontend |
| 4 | Sep 25 23:25 | `778b8ff` | Phase 1: OKF Knowledge Bundle |
| 5 | Sep 25 23:26 | `c1ea2d6` | Phase 2: LangChain Fallback RAG |
| 6 | Sep 25 23:28 | `39e6226` | Phase 3: Core AI Functions |
| 7 | Sep 25 23:31 | `b558106` | Phase 4: Frontend |
| 8 | Sep 25 23:33 | `6fe98b5` | Phase 5-7: Server, Audit, PPTX |
| 9 | Sep 25 23:54 | `9b87140` | Fix: langchain-community import |
| 10 | Sep 26 00:12 | `b218a78` | Fix: Gemini model → gemini-3.8-flash |
| 11 | Sep 26 00:19 | `680f5c2` | Fix: Gemini 429 retry logic |
| 12 | Sep 26 00:53 | `ca819ca` | Fix: Stale UI state (Infosys bug) |
| 13 | Sep 26 01:16 | `b2a18d5` | Feat: Groq fallback router |
| 14 | Sep 26 01:24 | `b02db3c` | Fix: Groq 413 TPM limit |
| 15 | Sep 26 01:34 | `8b441d8` | Fix: Audit wrong JSON shape |
| 16 | Sep 26 01:44 | `ba29f34` | Fix: Error pitch detection in frontend |
| 17 | Sep 26 10:41 | `2f8a93c` | **Feat: Multi-agent RAG v2** |
| 18 | Sep 26 10:44 | `b9f9e0c` | Fix: Audit slide-by-slide micro-prompts |

---

## KNOWN PERMANENT RULES (ACTIVE)

1. **Anti-AI-Look Manifesto** — No gradients, no glassmorphism, no emoji UI. Warm neutrals, slate blue accent only.
2. **Commit-per-phase rule** — Commit and push after every completed phase.
3. **Model router order** — Gemini → Groq GPT-OSS-120B → Qwen → GPT-OSS-20B. Never hard-code a single model.
4. **Run command** — Always `python -m app.server` from project root (not `python app/server.py`).
5. **Groq TPM budget** — Max 1,500 output tokens per Groq call. Max 5,000 chars input before truncation.
6. **OKF context budget** — Cap at 2,500 chars in pitch prompts, 1,200 chars in audit micro-prompts.

---

*Last updated: Sep 26, 2026 — 11:22 IST*
