# SETUP — How to Run Locally

> **Time to run: ~5 minutes**

## Prerequisites

Make sure these are installed on your machine:

| Tool | Version | Download |
|------|---------|----------|
| Python | 3.10+ | https://python.org |
| pip | (comes with Python) | — |

No Docker, no Node.js, no database setup required.

---

## Step 1 — Clone or Extract

If you received a **ZIP file**, extract it to any folder, e.g.:
```
C:\Projects\marsh-pitch-generator\
```

If you're cloning from GitHub:
```bash
git clone https://github.com/AbhiAJ001/Marsh-Case-Study.git
cd Marsh-Case-Study
```

---

## Step 2 — Create a Virtual Environment

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Mac / Linux
python3 -m venv venv
source venv/bin/activate
```

---

## Step 3 — Install Dependencies

```bash
pip install -r requirements.txt
```

---

## Step 4 — Add Your API Keys

Copy the example env file and fill in at least **one** API key:

```bash
# Windows
copy .env.example .env

# Mac / Linux
cp .env.example .env
```

Then open `.env` in any text editor and add your key(s).

**Recommended free keys to use:**

| Provider | Free Tier | Get Key At |
|----------|-----------|-----------|
| **OpenRouter** | Free models available | https://openrouter.ai |
| **Groq** | Very fast, free tier | https://console.groq.com |
| **Google Gemini** | Free quota | https://aistudio.google.com |

> The system uses a **multi-model fallback chain** — if one key fails, it automatically tries the next provider. You don't need all keys, just one will work.

---

## Step 5 — Run the App

```bash
python -m app.server
```

You should see:
```
 * Running on http://127.0.0.1:5000
```

Open your browser at **http://localhost:5000**

---

## How to Use

1. **Enter a company name** (e.g. `Infosys`, `Zomato`, `Tata Motors`)
2. **Select which insurance policies** to include in the pitch
3. Click **Generate Pitch** and watch the 3-step progress tracker
4. View the **Company Profile** (AI-researched data)
5. Read the **Generated Pitch Slides** (5 slides written by 5 parallel AI agents)
6. Click **Download PPTX** to get a branded PowerPoint deck
7. Click **Run Audit** to fact-check all claims against the policy documents

---

## Project Structure

```
├── app/
│   ├── server.py              ← Flask API server (entry point)
│   ├── agents/
│   │   ├── orchestrator.py    ← Coordinates all agents
│   │   ├── research/          ← Researches the company via LLM
│   │   ├── retrieval/         ← Retrieves relevant policy knowledge
│   │   ├── pitch/             ← 5 slide-writing agents (run in parallel)
│   │   └── audit/             ← Fact-checker agent
│   ├── core/
│   │   └── pptx_builder.py    ← Generates the PowerPoint file
│   ├── okf/                   ← Open Knowledge Format retrieval engine
│   ├── utils/
│   │   └── model_router.py    ← Multi-model fallback router (9 slots)
│   └── config.py
├── frontend/
│   ├── index.html             ← Single-page web app
│   ├── css/styles.css
│   └── js/app.js
├── knowledge_bundle/          ← Policy knowledge (OKF Markdown files)
├── Policy Documents/          ← Source PDFs (4 insurance brochures)
├── docs/                      ← Original Marsh case study brief
├── requirements.txt
├── .env.example               ← API key template
└── SETUP.md                   ← This file
```

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| `ModuleNotFoundError` | Run `pip install -r requirements.txt` again |
| `Port 5000 already in use` | Change port: `python -m app.server --port 5001` or kill the existing process |
| `AI model error` | Check your `.env` file has at least one valid API key |
| `The AI model failed to produce a valid format` | The model hit a token limit — click Generate again, the system will auto-fallback to a different provider |
| Browser shows blank page | Make sure you opened `http://localhost:5000` (not the file directly) |

---

## Architecture Overview

```
Browser (index.html)
    │
    ▼
Flask Server (app/server.py)
    │
    ▼
PitchOrchestrator
    ├─► ResearchAgent         → LLM researches company risks & profile
    ├─► PolicyRetrievalAgent  → OKF engine fetches relevant policy clauses
    ├─► 5× SlideAgents        → Each writes one pitch slide (parallel)
    ├─► FactCheckerAgent      → Audits claims against policy documents
    └─► PPTXBuilder           → Generates branded PowerPoint
         │
         └─► ModelRouter (9-slot fallback chain)
               Gemini → Groq → Mistral → OpenRouter → NVIDIA NIM
```
