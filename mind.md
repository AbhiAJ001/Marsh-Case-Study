# MIND — Marsh AI Pitch Generator

## Project Identity
- **Project**: Marsh AI-Powered Insurance Pitch Generator
- **For**: NMIMS 2026 Internship Case Study
- **Owner**: Abhijit
- **Started**: 2026-09-24

---

## ⚠️ PERMANENT DESIGN RULES — NEVER BREAK THESE

### The Anti-AI-Look Manifesto

This application must look like it was **built by a skilled human design team**, NOT by an AI agent. Every design decision must pass this test: *"Would a junior designer using ChatGPT produce this?"* — if yes, **reject it**.

### What We NEVER Do
- No purple-to-blue gradients
- No glassmorphism / frosted glass cards
- No excessive rounded corners on everything (border-radius: 9999px everywhere)
- No generic hero sections with oversized gradient text
- No emoji-heavy UI elements
- No card grids where every card looks identical with the same shadow
- No Tailwind default indigo/violet as primary color
- No "AI-powered" badges or sparkle icons scattered around
- No generic sans-serif that screams "I used the Tailwind default"
- No over-animated entrance effects on every single element
- No dark mode with neon accents
- No floating blobs or abstract SVG backgrounds

### What We DO — The Human Touch
- **Color**: Minimalist. Warm neutrals as base (off-whites, warm grays). ONE accent color used sparingly — Marsh brand blue (#00857C teal or a refined navy) for primary actions only. Color is earned, not sprayed.
- **Typography hierarchy** — this is the SOUL of the design:
  - `h1` — 2.25rem/36px, weight 600, letter-spacing -0.025em, color: near-black (#1a1a1a). Used ONCE per page.
  - `h2` — 1.5rem/24px, weight 600, letter-spacing -0.015em. Section headers.
  - `h3` — 1.125rem/18px, weight 500. Subsection / card titles.
  - `body` — 0.9375rem/15px, weight 400, line-height 1.65, color: #404040. Readable. Comfortable.
  - `small/caption` — 0.8125rem/13px, weight 400, color: #707070. Supporting info.
  - `label` — 0.75rem/12px, weight 500, uppercase, letter-spacing 0.05em, color: #909090. Form labels, categories.
  - **Font**: Inter or system-ui stack. NOT Poppins. NOT Space Grotesk.
- **Whitespace**: Generous but structured. Content breathes. Sections separated by space, not lines or cards.
- **Borders**: Thin (1px), light (#e5e5e5). Used to separate, not decorate.
- **Shadows**: Almost none. If used, barely visible (0 1px 2px rgba(0,0,0,0.04)). The layout itself creates hierarchy, not shadows.
- **Buttons**: Solid fill for primary (flat, no gradient), ghost/outline for secondary. Small border-radius (6px). No pill shapes for main actions.
- **Inputs**: Clean, simple. Thin bottom border or subtle full border. No heavy focus rings — a clean color change is enough.
- **Spacing system**: 4px base. 8, 12, 16, 24, 32, 48, 64, 96. Consistent. Mathematical.
- **Animation**: Minimal. 150ms transitions on hover states only. No page entrance animations. No bouncing. No parallax.
- **Icons**: Lucide or Phosphor. Thin stroke (1.5px). Never decorative — always functional.
- **Layout**: Left-aligned where possible. NOT center-aligned everything. Professional tools align left.
- **Empty states**: Thoughtful microcopy, not "No data found 🤷".

### The Feel
Think: **Notion meets Linear meets Stripe Docs**. Clean, opinionated, quietly confident. It feels like a tool built by people who actually use it, not a demo built to impress.

---

## Project Context

### What We're Building
A web application where a Marsh Client Advisor:
1. Enters a company name
2. Selects one or more policy documents (from 4 provided)
3. Clicks Generate
4. Gets a tailored 3-5 slide marketing pitch PowerPoint
5. Gets an audit report tracing every claim to policy source text
6. Can approve, edit, or reject the pitch

### The 4 Policy Documents
1. **ABHI — Activ One** (2 pages): HealthReturns™, Claim Protect, Super Credit (6X SI), Super Reload, SI ₹5L–₹6Cr
2. **Care Health** (4 pages): Unlimited Auto Recharge, Cumulative Bonus up to 500% SI, 7-zone pricing, Wellness discount 30%
3. **HDFC ERGO — Optima Secure+** (16 pages): Secure Benefit 2X, Infinite Benefit, Protect Benefit, Deductible discounts up to 65%, SI ₹10L–₹2Cr
4. **Niva Bupa — ReAssure 2.0** (2 pages): Platinum & Titanium+ variants, ReAssure+, Booster+ 5X/10X, Live Healthy 30% discount, SI ₹5L–₹1Cr

### Key Functions
- `generateCompanyProfile(company_name)` → company industry, size, risks (with labelled fallbacks)
- `generateMarketingPitch()` → 3-5 slide PPTX grounded in policy docs
- `auditPitchContent(pitch_slides, policy_docs)` → structured audit report with confidence scores

### Deliverables
1. Working application (UI + backend)
2. Sample pitch deck (PPTX)
3. Audit report with traceability
4. Write-up document (approach + decisions)

---

## Tech Stack (v2 — Revised 2026-09-25)
- **Frontend**: HTML + CSS + vanilla JS (no framework — handcrafted, full control)
- **Backend**: Flask (Python) — serves static frontend + REST API
- **LLM**: Google Gemini API (free tier — key prompted on first run)
- **Knowledge Layer**: OKF (Open Knowledge Format) from Google's knowledge-catalog repo — policy PDFs decomposed into structured concept files with YAML metadata
- **RAG Fallback**: LangChain + FAISS for similarity search when OKF graph traversal needs more context
- **PDF Processing**: PyPDF2 for text extraction
- **PPT Generation**: python-pptx
- **Company Research**: Gemini + web search (real-time company data)

---

## File Structure (v2)
```
Marsh-Case-Study/
├── Policy Documents/           # 4 source PDFs (provided)
├── docs/                       # Case study PDF
├── knowledge_bundle/           # OKF bundle (generated from PDFs)
│   ├── index.md                # Root catalog
│   ├── log.md                  # Bundle change log
│   ├── policies/               # 4 master policy docs
│   ├── coverages/              # Coverage concepts
│   ├── benefits/               # Benefit concepts
│   ├── exclusions/             # Exclusion concepts
│   ├── pricing/                # Pricing & discount concepts
│   └── references/             # Supporting references
├── frontend/                   # HTML/CSS/JS (served as static)
│   ├── index.html              # Single page app
│   ├── css/styles.css          # The human-touch design
│   └── js/app.js               # Client-side logic
├── app/                        # Python backend
│   ├── server.py               # Flask API server
│   ├── config.py               # Environment, API keys (first-run prompt)
│   ├── core/
│   │   ├── company_profile.py  # generateCompanyProfile()
│   │   ├── pitch_generator.py  # generateMarketingPitch()
│   │   ├── audit_engine.py     # auditPitchContent()
│   │   └── pptx_builder.py     # PowerPoint generation
│   ├── okf/
│   │   ├── bundle_builder.py   # PDF → OKF bundle conversion
│   │   ├── bundle_reader.py    # Read & parse OKF concepts
│   │   └── okf_retriever.py    # OKF-aware retrieval (primary)
│   ├── rag/
│   │   ├── langchain_fallback.py  # LangChain RAG (fallback)
│   │   └── vector_store.py     # FAISS index
│   └── utils/
│       ├── prompts.py          # All LLM prompts
│       └── helpers.py          # Shared utilities
├── output/                     # Generated pitch decks + audit reports
├── write_up/                   # Final submission document
├── mind.md                     # THIS FILE — project memory
├── log.md                      # Work log + task tracking
└── map.md                      # System blueprint
```

