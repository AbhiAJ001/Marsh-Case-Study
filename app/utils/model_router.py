"""
Model Router — Automatic LLM fallback chain.

Priority order:
  1. Google Gemini (gemini-3.8-flash) — primary
  2. Groq Llama 3.3 70B              — fallback when Gemini quota is exhausted
  3. Groq Gemma2 9B                  — secondary fallback

Usage:
    from app.utils.model_router import generate

    result = generate(prompt, temperature=0.3, max_tokens=2048)
    # Returns: {"text": "...", "model_used": "gemini|groq-llama|groq-gemma"}
"""

import os
import time
import json
from dotenv import load_dotenv
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
load_dotenv(PROJECT_ROOT / ".env")

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")
GROQ_API_KEY   = os.getenv("GROQ_API_KEY", "")


# ─── Gemini call ────────────────────────────────────────────────────────────

def _call_gemini(prompt: str, temperature: float, max_tokens: int) -> str:
    import google.generativeai as genai
    from google.api_core.exceptions import ResourceExhausted

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

def _call_groq(prompt: str, temperature: float, max_tokens: int,
               model: str = "llama-3.3-70b-versatile") -> str:
    from groq import Groq, RateLimitError

    if not GROQ_API_KEY:
        raise RuntimeError("GROQ_API_KEY not set")

    client = Groq(api_key=GROQ_API_KEY)
    completion = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        temperature=temperature,
        max_tokens=max_tokens,
    )
    return completion.choices[0].message.content


# ─── Main router ────────────────────────────────────────────────────────────

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
        ("gemini-3.8-flash",    lambda: _call_gemini(prompt, temperature, max_tokens)),
        ("groq-gpt-oss-120b",   lambda: _call_groq(prompt, temperature, max_tokens, "openai/gpt-oss-120b")),
        ("groq-qwen3.8-27b",    lambda: _call_groq(prompt, temperature, max_tokens, "qwen/qwen3.8-27b")),
        ("groq-gpt-oss-20b",    lambda: _call_groq(prompt, temperature, max_tokens, "openai/gpt-oss-20b")),
    ]

    last_error = None
    for model_name, caller in providers:
        try:
            print(f"[ModelRouter] Trying {model_name}...")
            text = caller()
            print(f"[ModelRouter] [OK] Success with {model_name}")
            return {"text": text, "model_used": model_name}
        except Exception as e:
            err_str = str(e)
            # Rate limit or quota errors → try next provider
            if any(kw in err_str.lower() for kw in ["quota", "rate limit", "429", "resource exhausted", "ratelimit"]):
                print(f"[ModelRouter] [X] {model_name} rate-limited -- switching to next provider")
                last_error = e
                continue
            # Any other error → also try next (don't crash on one bad provider)
            print(f"[ModelRouter] [X] {model_name} error: {err_str[:120]} -- trying next provider")
            last_error = e
            continue

    raise RuntimeError(
        f"All LLM providers failed. Last error: {last_error}. "
        "Check your API keys and quota status."
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
