"""
Configuration module — loads environment variables and provides
a safe Gemini client. On first run, if no .env file exists,
prompts the user for their API key and saves it.
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Project root is one level up from app/
PROJECT_ROOT = Path(__file__).resolve().parent.parent
ENV_PATH = PROJECT_ROOT / ".env"

def _ensure_api_key():
    """Check for API key. If missing, prompt interactively and save to .env."""
    key = os.getenv("GOOGLE_API_KEY", "").strip()
    if key:
        return key

    print("\n" + "=" * 52)
    print("  Gemini API key not found.")
    print("  Get one free at: https://aistudio.google.com/apikey")
    print("=" * 52)

    key = input("\n  Paste your API key: ").strip()
    if not key:
        print("  No key provided. Exiting.")
        sys.exit(1)

    # Append to .env (create if missing)
    with open(ENV_PATH, "a", encoding="utf-8") as f:
        f.write(f"\nGOOGLE_API_KEY={key}\n")

    os.environ["GOOGLE_API_KEY"] = key
    print("  Key saved to .env — you won't be asked again.\n")
    return key


def load_config():
    """Load environment and return a config dict."""
    load_dotenv(ENV_PATH)

    api_key = _ensure_api_key()

    return {
        "GOOGLE_API_KEY": api_key,
        "FLASK_PORT": int(os.getenv("FLASK_PORT", "5000")),
        "FLASK_DEBUG": os.getenv("FLASK_DEBUG", "false").lower() == "true",
        "PROJECT_ROOT": PROJECT_ROOT,
        "POLICY_DIR": PROJECT_ROOT / "Policy Documents",
        "BUNDLE_DIR": PROJECT_ROOT / "knowledge_bundle",
        "OUTPUT_DIR": PROJECT_ROOT / "output",
    }


# Singleton — loaded once on import
_config = None

def get_config():
    """Return the cached config dict."""
    global _config
    if _config is None:
        _config = load_config()
    return _config
