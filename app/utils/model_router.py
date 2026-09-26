"""
Model Router v2 — Multi-provider, agent-aware LLM fallback chain.

Provider inventory (7 keys, 5 providers, 10 model slots):
┌─────────────────────┬────────────────────────────────┬──────────────────────┐
│ Provider            │ Model                          │ Best for             │
├─────────────────────┼────────────────────────────────┼──────────────────────┤
│ Gemini (primary)    │ gemini-3.8-flash               │ Research, profiling  │
│ OpenRouter (key 1)  │ meta-llama/llama-3.3-70b-inst  │ Pitch writing        │
│ NVIDIA NIM          │ meta/llama-3.1-70b-instruct    │ Structured JSON      │
│ Mistral (key 1)     │ mistral-large-latest           │ Fact-checking, audit │
│ Groq                │ openai/gpt-oss-120b            │ Fast fallback        │
│ OpenRouter (key 2)  │ google/gemini-2.0-flash-exp    │ Backup research      │
│ Mistral (key 2)     │ mistral-medium-latest          │ Backup audit         │
│ Groq                │ qwen/qwen3.8-27b               │ Light tasks          │
│ Groq                │ openai/gpt-oss-20b             │ Final fallback       │
└─────────────────────┴────────────────────────────────┴──────────────────────┘

Agent-specific routing (task_type parameter):
  "research"  → Gemini → OpenRouter Llama → NVIDIA → Mistral → Groq
  "pitch"     → OpenRouter Llama → NVIDIA → Gemini → Mistral → Groq
  "audit"     → Mistral → NVIDIA → OpenRouter → Gemini → Groq
  "general"   → full chain (all 9 slots in order above)

OpenRouter, NVIDIA NIM, and Mistral all speak the OpenAI wire format
so we use the `openai` package with a custom base_url for each.

Usage:
    from app.utils.model_router import generate, parse_json_from_response

    result = generate(prompt, temperature=0.3, max_tokens=1200, task_type="pitch")
    # Returns: {"text": "...", "model_used": "openrouter-llama-3.3-70b"}
"""

import os
import json
from pathlib import Path
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
load_dotenv(PROJECT_ROOT / ".env")

# ── Load all API keys ─────────────────────────────────────────────────────────
GOOGLE_API_KEY      = os.getenv("GOOGLE_API_KEY", "")
GROQ_API_KEY        = os.getenv("GROQ_API_KEY", "")
MISTRAL_API_KEY     = os.getenv("MISTRAL_API_KEY", "")
MISTRAL_API_KEY_2   = os.getenv("MISTRAL_API_KEY_2", "")
OPENROUTER_API_KEY  = os.getenv("OPENROUTER_API_KEY", "")
OPENROUTER_API_KEY_2= os.getenv("OPENROUTER_API_KEY_2", "")
NVIDIA_API_KEY      = os.getenv("NVIDIA_API_KEY", "")

# ── Token budget constants ────────────────────────────────────────────────────
GROQ_MAX_OUTPUT_TOKENS   = 1500
GROQ_MAX_PROMPT_CHARS    = 5000    # ~1250 tokens
MISTRAL_MAX_PROMPT_CHARS = 8000    # ~2000 tokens — more generous
NVIDIA_MAX_PROMPT_CHARS  = 10000   # large context window

# ── Keywords that signal "provider busy/exhausted — skip to next" ─────────────
_SKIP_KEYWORDS = [
    "quota", "rate limit", "429", "resource exhausted", "ratelimit",
    "rate_limit", "too large", "413", "token", "tpm", "rpm", "rpd",
    "request too large", "decommissioned", "does not exist", "model_not_found",
    "insufficient_quota", "billing", "exceeded", "limit reached",
    "overloaded", "503", "502", "capacity",
]


# ── Helper: truncate prompt to safe length ────────────────────────────────────

def _truncate(prompt: str, max_chars: int, label: str = "") -> str:
    if len(prompt) <= max_chars:
        return prompt
    cut = prompt[:max_chars].rfind("\n")
    if cut < max_chars // 2:
        cut = max_chars
    note = f"\n\n[CONTEXT TRUNCATED at {label} limit — respond with best JSON from above.]"
    return prompt[:cut] + note


# ── Provider callers ──────────────────────────────────────────────────────────

def _call_gemini(prompt: str, temperature: float, max_tokens: int) -> str:
    import google.generativeai as genai
    if not GOOGLE_API_KEY:
        raise RuntimeError("GOOGLE_API_KEY not set")
    genai.configure(api_key=GOOGLE_API_KEY)
    model = genai.GenerativeModel("gemini-1.5-flash")
    response = model.generate_content(
        prompt,
        generation_config=genai.GenerationConfig(
            temperature=temperature,
            max_output_tokens=max_tokens,
        ),
    )
    return response.text


def _call_openai_compat(
    prompt: str,
    temperature: float,
    max_tokens: int,
    api_key: str,
    base_url: str,
    model: str,
    max_prompt_chars: int = 12000,
    extra_headers: dict = None,
) -> str:
    """Generic caller for any OpenAI-compatible endpoint (OpenRouter / NVIDIA / Mistral)."""
    from openai import OpenAI

    if not api_key:
        raise RuntimeError(f"API key not set for {base_url}")

    safe_prompt = _truncate(prompt, max_prompt_chars, model)
    kwargs = dict(api_key=api_key, base_url=base_url)
    if extra_headers:
        kwargs["default_headers"] = extra_headers

    client = OpenAI(**kwargs)
    resp = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": safe_prompt}],
        temperature=temperature,
        max_tokens=max_tokens,
    )
    return resp.choices[0].message.content


def _call_openrouter(prompt: str, temperature: float, max_tokens: int,
                     api_key: str, model: str) -> str:
    return _call_openai_compat(
        prompt, temperature, max_tokens,
        api_key=api_key,
        base_url="https://openrouter.ai/api/v1",
        model=model,
        max_prompt_chars=NVIDIA_MAX_PROMPT_CHARS,
        extra_headers={
            "HTTP-Referer": "https://github.com/AbhiAJ001/Marsh-Case-Study",
            "X-Title": "Marsh Insurance Pitch Generator",
        },
    )


def _call_nvidia(prompt: str, temperature: float, max_tokens: int) -> str:
    return _call_openai_compat(
        prompt, temperature, max_tokens,
        api_key=NVIDIA_API_KEY,
        base_url="https://integrate.api.nvidia.com/v1",
        model="meta/llama-3.1-70b-instruct",
        max_prompt_chars=NVIDIA_MAX_PROMPT_CHARS,
    )


def _call_mistral(prompt: str, temperature: float, max_tokens: int,
                  api_key: str, model: str = "mistral-large-latest") -> str:
    return _call_openai_compat(
        prompt, temperature, max_tokens,
        api_key=api_key,
        base_url="https://api.mistral.ai/v1",
        model=model,
        max_prompt_chars=MISTRAL_MAX_PROMPT_CHARS,
    )


def _call_groq(prompt: str, temperature: float, model: str) -> str:
    from groq import Groq
    if not GROQ_API_KEY:
        raise RuntimeError("GROQ_API_KEY not set")
    safe_prompt = _truncate(prompt, GROQ_MAX_PROMPT_CHARS, "Groq")
    client = Groq(api_key=GROQ_API_KEY)
    completion = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": safe_prompt}],
        temperature=temperature,
        max_tokens=GROQ_MAX_OUTPUT_TOKENS,
    )
    return completion.choices[0].message.content


# ── Provider chains (task-specific) ──────────────────────────────────────────

def _get_providers(prompt: str, temperature: float, max_tokens: int,
                   task_type: str = "general") -> list:
    """
    Return an ordered list of (name, callable) provider slots.

    task_type controls which providers are tried first:
      "research" → Gemini first (best world-knowledge)
      "pitch"    → OpenRouter/NVIDIA first (best creative structured output)
      "audit"    → Mistral first (best rule-following strict JSON)
      "general"  → full chain, Gemini first
    """

    # All available slots
    slots = {
        "gemini":          ("gemini-1.5-flash",
                            lambda: _call_gemini(prompt, temperature, max_tokens)),
        "openrouter-llama":("openrouter-llama-3.3-70b",
                            lambda: _call_openrouter(prompt, temperature, max_tokens,
                                OPENROUTER_API_KEY, "meta-llama/llama-3.3-70b-instruct")),
        "nvidia-llama":    ("nvidia-llama-3.1-70b",
                            lambda: _call_nvidia(prompt, temperature, max_tokens)),
        "mistral-large":   ("mistral-large",
                            lambda: _call_mistral(prompt, temperature, max_tokens,
                                MISTRAL_API_KEY, "mistral-large-latest")),
        "groq-120b":       ("groq-gpt-oss-120b",
                            lambda: _call_groq(prompt, temperature, "openai/gpt-oss-120b")),
        "openrouter-gemini":("openrouter-gemini-2.0",
                             lambda: _call_openrouter(prompt, temperature, max_tokens,
                                OPENROUTER_API_KEY_2, "google/gemini-2.0-flash-exp:free")),
        "mistral-medium":  ("mistral-medium",
                            lambda: _call_mistral(prompt, temperature, max_tokens,
                                MISTRAL_API_KEY_2, "mistral-medium-latest")),
        "groq-qwen":       ("groq-qwen3.8-27b",
                            lambda: _call_groq(prompt, temperature, "qwen/qwen3.8-27b")),
        "groq-20b":        ("groq-gpt-oss-20b",
                            lambda: _call_groq(prompt, temperature, "openai/gpt-oss-20b")),
    }

    # Task-specific orderings — put the best model for each task first
    order_map = {
        # Research: needs strong world knowledge → Gemini best, NVIDIA Llama second
        "research": [
            "gemini", "openrouter-llama", "nvidia-llama",
            "mistral-large", "groq-120b", "openrouter-gemini",
            "mistral-medium", "groq-qwen", "groq-20b",
        ],
        # Pitch: needs creative, long structured JSON → NVIDIA + OpenRouter shine
        "pitch": [
            "openrouter-llama", "nvidia-llama", "gemini",
            "mistral-large", "groq-120b", "openrouter-gemini",
            "mistral-medium", "groq-qwen", "groq-20b",
        ],
        # Audit: needs strict rule-following → Mistral is best at instructions
        "audit": [
            "mistral-large", "nvidia-llama", "openrouter-llama",
            "gemini", "groq-120b", "mistral-medium",
            "openrouter-gemini", "groq-qwen", "groq-20b",
        ],
        # General: Gemini first (default)
        "general": [
            "gemini", "openrouter-llama", "nvidia-llama",
            "mistral-large", "groq-120b", "openrouter-gemini",
            "mistral-medium", "groq-qwen", "groq-20b",
        ],
    }

    order = order_map.get(task_type, order_map["general"])
    return [slots[key] for key in order if key in slots]


# ── Main entry point ──────────────────────────────────────────────────────────

def generate(
    prompt: str,
    temperature: float = 0.3,
    max_tokens: int = 1500,
    task_type: str = "general",
    require_json: bool = True,
) -> dict:
    """
    Try each provider in task-specific order and return the first success.

    Args:
        prompt:      The LLM prompt string
        temperature: Sampling temperature (0.0 – 1.0)
        max_tokens:  Max output tokens (advisory — some providers cap lower)
        task_type:   "research" | "pitch" | "audit" | "general"
                     Controls which provider is tried first.
        require_json: If True, validates that the output is parseable JSON before accepting it.

    Returns:
        {"text": str, "model_used": str}

    Raises:
        RuntimeError if ALL providers fail.
    """
    providers  = _get_providers(prompt, temperature, max_tokens, task_type)
    last_error = None

    for model_name, caller in providers:
        try:
            print(f"[ModelRouter] Trying {model_name}...")
            text = caller()
            if not text or not text.strip():
                raise ValueError("Empty response from model")
                
            if require_json:
                # This will raise ValueError if parsing fails, forcing a fallback!
                _ = parse_json_from_response(text)
                
            print(f"[ModelRouter] [OK] Success with {model_name}")
            return {"text": text, "model_used": model_name}

        except Exception as e:
            err_str    = str(e).lower()
            last_error = e
            skip       = any(kw in err_str for kw in _SKIP_KEYWORDS)
            if skip:
                print(f"[ModelRouter] [X] {model_name} rate-limited/quota -- switching")
            else:
                print(f"[ModelRouter] [X] {model_name} error: {str(e)[:80]} -- trying next")
            continue

    raise RuntimeError(
        f"All {len(providers)} providers failed for task='{task_type}'. "
        f"Last error: {last_error}. Check API keys and quotas."
    )


# ── JSON parsing helper (unchanged) ──────────────────────────────────────────

def parse_json_from_response(text: str) -> dict:
    """
    Safely extract a JSON object from an LLM response,
    stripping common markdown fences that models emit.
    """
    text = text.strip()
    # Strip common markdown fences
    for fence in ("```json", "```JSON", "```"):
        if text.startswith(fence):
            text = text[len(fence):]
            break
    if text.endswith("```"):
        text = text[:-3]
    text = text.strip()

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        # Try to extract first complete JSON object from surrounding prose
        start = text.find("{")
        end   = text.rfind("}") + 1
        if start >= 0 and end > start:
            return json.loads(text[start:end])
        raise ValueError(
            f"Could not parse JSON from model response.\n"
            f"Raw output (first 500 chars):\n{text[:500]}"
        )
