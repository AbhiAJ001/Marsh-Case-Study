"""
Flask API Server — Serves the frontend and handles all API requests.

v2: Routes now call the PitchOrchestrator (multi-agent) instead of
    calling core modules directly. API contract is identical — the
    frontend requires zero changes.

Routes:
    GET  /                  → Serve index.html
    GET  /api/policies      → List available insurance policies
    POST /api/profile       → Research company via ResearchAgent
    POST /api/pitch         → Generate pitch via multi-agent orchestration
    POST /api/audit         → Audit pitch via FactCheckerAgent
    POST /api/download-pptx → Generate and download PowerPoint
"""

import os
import sys
from pathlib import Path
from flask import Flask, request, jsonify, send_from_directory, send_file

# Ensure app package is importable
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from app.config import get_config
from app.agents.orchestrator import PitchOrchestrator
from app.core.pptx_builder import build_pptx
from app.okf.okf_retriever import OKFRetriever

# ─── App setup ───────────────────────────────────────────────────────────────
config = get_config()

app = Flask(
    __name__,
    static_folder=str(project_root / "frontend"),
    static_url_path=""
)

# Single orchestrator instance — shared across requests
orchestrator = PitchOrchestrator(
    bundle_dir   = config["BUNDLE_DIR"],
    project_root = project_root,
)


# ─── Frontend routes ──────────────────────────────────────────────────────────

@app.route("/")
def serve_index():
    return send_from_directory(app.static_folder, "index.html")

@app.route("/css/<path:filename>")
def serve_css(filename):
    return send_from_directory(os.path.join(app.static_folder, "css"), filename)

@app.route("/js/<path:filename>")
def serve_js(filename):
    return send_from_directory(os.path.join(app.static_folder, "js"), filename)


# ─── API routes ───────────────────────────────────────────────────────────────

@app.route("/api/policies", methods=["GET"])
def api_policies():
    """Return list of available insurance policies."""
    retriever = OKFRetriever(config["BUNDLE_DIR"])
    return jsonify(retriever.get_available_policies())


@app.route("/api/profile", methods=["POST"])
def api_profile():
    """
    Phase A — Research company using ResearchAgent.
    Returns a structured company profile dict.
    """
    data = request.get_json()
    company_name = (data.get("company_name") or "").strip()

    if not company_name:
        return jsonify({"error": "Company name is required"}), 400

    try:
        profile = orchestrator.research_company(company_name)
        return jsonify(profile)
    except Exception as e:
        err = str(e)
        if "rate limit" in err.lower() or "quota" in err.lower() or "429" in err:
            msg = "Gemini API rate limit reached. The free tier allows 20 requests/day. Please wait a few minutes and try again."
        else:
            msg = f"Failed to research company: {err}"
        return jsonify({"error": msg}), 500


@app.route("/api/pitch", methods=["POST"])
def api_pitch():
    """
    Phases B + C — Parallel policy retrieval then parallel slide writing.
    Returns a complete pitch dict.
    """
    data     = request.get_json()
    profile  = data.get("profile")
    policies = data.get("policies", [])

    if not profile:
        return jsonify({"error": "Company profile is required"}), 400
    if not policies:
        return jsonify({"error": "At least one policy must be selected"}), 400

    try:
        pitch = orchestrator.generate_pitch(profile, policies)
        return jsonify(pitch)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/audit", methods=["POST"])
def api_audit():
    """
    Phase D — Fact-check pitch via FactCheckerAgent.
    Returns per-claim audit results.
    """
    data    = request.get_json()
    pitch   = data.get("pitch")
    policies = data.get("policies") or pitch.get("_policy_ids", []) if pitch else []

    if not pitch:
        return jsonify({"error": "Pitch data is required"}), 400
    if not policies:
        return jsonify({"error": "Policy IDs required for audit"}), 400

    try:
        audit = orchestrator.audit_pitch(pitch, policies)
        return jsonify(audit)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/download-pptx", methods=["POST"])
def api_download_pptx():
    """Generate and download a PowerPoint from the pitch data."""
    data  = request.get_json()
    pitch = data.get("pitch")

    if not pitch:
        return jsonify({"error": "Pitch data is required"}), 400

    try:
        buffer   = build_pptx(pitch)
        company  = pitch.get("target_company", "company").replace(" ", "_")
        filename = f"pitch_{company}.pptx"

        return send_file(
            buffer,
            mimetype="application/vnd.openxmlformats-officedocument.presentationml.presentation",
            as_attachment=True,
            download_name=filename,
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ─── Run ─────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    port  = config.get("FLASK_PORT", 5000)
    debug = config.get("FLASK_DEBUG", False)

    print(f"\n  Marsh Pitch Generator  [Multi-Agent v2]")
    print(f"  http://localhost:{port}")
    print(f"  Press Ctrl+C to stop\n")

    app.run(host="0.0.0.0", port=port, debug=debug)
