"""
Shared utilities — helper functions used across the application.
"""

import json
import re


def safe_json_parse(text: str) -> dict:
    """Attempt to parse JSON from LLM output, handling common formatting issues."""
    text = text.strip()
    
    # Remove markdown code fences
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
        # Try to extract JSON object from surrounding text
        start = text.find("{")
        end = text.rfind("}") + 1
        if start >= 0 and end > start:
            try:
                return json.loads(text[start:end])
            except json.JSONDecodeError:
                pass
        return None


def truncate(text: str, max_length: int = 200) -> str:
    """Truncate text with ellipsis."""
    if len(text) <= max_length:
        return text
    return text[:max_length - 3] + "..."


def format_currency(amount: float) -> str:
    """Format amount in Indian currency notation."""
    if amount >= 10_000_000:
        return f"₹{amount / 10_000_000:.1f} Crores"
    elif amount >= 100_000:
        return f"₹{amount / 100_000:.1f} Lakhs"
    else:
        return f"₹{amount:,.0f}"
