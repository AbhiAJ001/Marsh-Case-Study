"""
Model Router — Automatic LLM fallback chain.

Priority order:
  1. Google Gemini (gemini-3.8-flash)  — primary, large context
  2. Groq GPT-OSS-120B                 — fallback, capped at 1500 tokens output
  3. Groq Qwen3.8-27B                  — secondary fallback
  4. Groq GPT-OSS-20B                  — tertiary fallback (smallest prompt)

Groq free tier cap: 8000 TPM. We cap output at 1500 tokens and truncate
the prompt to 4000 chars max so (input + output) stays well under the limit.

Usage:
    from app.utils.model_router import generate

    result = generate(prompt, temperature=0.3, max_tokens=2048)
    # Returns: {"text": "...", "model_used": "gemini|groq-..."}
"""

import os
import json
from dotenv import load_dotenv
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
load_dotenv(PROJECT_ROOT / ".env")

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")
GROQ_API_KEY   = os.getenv("GROQ_API_KEY", "")

# Groq free tier: 8000 TPM. Cap output at 1500 so prompt + output <= 8000.
# Prompt itself is truncated to ~5000 chars (~1250 tokens) in _prepare_groq_prompt.
GROQ_MAX_OUTPUT_TOKENS = 1500
GROQ_MAX_PROMPT_CHARS  = 5000   # ~1250 tokens; leaves headroom for output


# ─── Helpers ────────────────────────────────────────────────────────────────

def _prepare_groq_prompt(prompt: str) -> str:
    """Truncate prompt to stay within Groq's TPM limit."""
    if len(prompt) <= GROQ_MAX_PROMPT_CHARS:
        return prompt

    # Keep the first N chars — the instructions — and note the truncation
    truncated = prompt[:GROQ_MAX_PROMPT_CHARS]
    # Find the last newline so we don't cut mid-sentence
    cut = truncated.rfind("\n")
    if cut > GROQ_MAX_PROMPT_CHARS // 2:
        truncated = truncated[:cut]

    truncated += (
        "\n\n[CONTEXT TRUNCATED — respond with the best JSON you can based on "
        "the information above. Keep your response concise.]"
    )
    return truncated


# ─── Gemini call ────────────────────────────────────────────────────────────

def _call_gemini(prompt: str, temperature: float, max_tokens: int) -> str:
    import google.generativeai as genai

    if not GOOGLE_API_KEY:
        raise RuntimeError("GOOGLE_API_KEY not set")

    genai.configure(api_key=GOOGLE_API_KEY)
    model = genai.GenerativeModel("gemini-3.8-flash")

    response = model.generate_content(
        prompt,
        generation_config=genai.GenerationConfig(
            temperature=temperature,
            max_output_tokens=max_tokens,
        ),
    )
    return response.text


# ─── Groq call ──────────────────────────────────────────────────────────────

def _call_groq(prompt: str, temperature: float, model: str) -> str:
    from groq import Groq

    if not GROQ_API_KEY:
        raise RuntimeError("GROQ_API_KEY not set")

    # Truncate prompt and cap output tokens to stay within free-tier TPM limit
    safe_prompt = _prepare_groq_prompt(prompt)

    client = Groq(api_key=GROQ_API_KEY)
    completion = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": safe_prompt}],
        temperature=temperature,
        max_tokens=GROQ_MAX_OUTPUT_TOKENS,
    )
    return completion.choices[0].message.content


# ─── Main router ────────────────────────────────────────────────────────────

# Keywords that mean "this provider is temporarily unavailable — try the next"
_SKIP_KEYWORDS = [
    "quota", "rate limit", "429", "resource exhausted", "ratelimit",
    "rate_limit", "too large", "413", "token", "tpm", "request too large",
    "decommissioned", "does not exist", "model_not_found",
]


def generate(prompt: str, temperature: float = 0.3, max_tokens: int = 2048) -> dict:
    """
    Try each provider in order and return the first successful response.

    Returns:
        {
            "text":       str  — the raw LLM text output,
            "model_used": str  — which model actually responded
        }

    Raises:
        RuntimeError if ALL providers fail.
    """
    providers = [
        ("gemini-3.8-flash",
            lambda: _call_gemini(prompt, temperature, max_tokens)),
        ("groq-gpt-oss-120b",
            lambda: _call_groq(prompt, temperature, "openai/gpt-oss-120b")),
        ("groq-qwen3.8-27b",
            lambda: _call_groq(prompt, temperature, "qwen/qwen3.8-27b")),
        ("groq-gpt-oss-20b",
            lambda: _call_groq(prompt, temperature, "openai/gpt-oss-20b")),
    ]

    last_error = None
    for model_name, caller in providers:
        try:
            print(f"[ModelRouter] Trying {model_name}...")
            text = caller()
            if not text or not text.strip():
                raise ValueError("Empty response from model")
            print(f"[ModelRouter] [OK] Success with {model_name}")
            return {"text": text, "model_used": model_name}
        except Exception as e:
            err_str = str(e).lower()
            last_error = e
            if any(kw in err_str for kw in _SKIP_KEYWORDS):
                print(f"[ModelRouter] [X] {model_name} unavailable -- switching to next")
                continue
            # Unexpected error — still try next but log it
            print(f"[ModelRouter] [X] {model_name} unexpected error: {str(e)[:100]} -- trying next")
            continue

    raise RuntimeError(
        f"All LLM providers failed. Last error: {last_error}. "
        "Please check your API keys, quota, and try again later."
    )


def parse_json_from_response(text: str) -> dict:
    """
    Safely extract a JSON object from an LLM response,
    stripping common markdown fences that models emit.
    """
    text = text.strip()
    if text.startswith("```json"):
        text = text[7:]
    if text.startswith("```"):
        text = text[3:]
    if text.endswith("```"):
        text = text[:-3]
    text = text.strip()

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        # Try to extract first JSON object from surrounding text
        start = text.find("{")
        end   = text.rfind("}") + 1
        if start >= 0 and end > start:
            return json.loads(text[start:end])
        raise ValueError(f"Could not parse JSON from model response. Raw output:\n{text[:500]}")
