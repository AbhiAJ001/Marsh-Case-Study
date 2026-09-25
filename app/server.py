"""
Flask API Server — Serves the frontend and handles all API requests.

Routes:
    GET  /               → Serve index.html
    GET  /api/policies   → List available policies
    POST /api/profile    → Generate company profile
    POST /api/pitch      → Generate marketing pitch
    POST /api/audit      → Audit pitch content
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
from app.core.company_profile import generate_company_profile
from app.core.pitch_generator import generate_marketing_pitch
from app.core.audit_engine import audit_pitch_content
from app.core.pptx_builder import build_pptx
from app.okf.okf_retriever import OKFRetriever

# ─── App setup ───
config = get_config()

app = Flask(
    __name__,
    static_folder=str(project_root / "frontend"),
    static_url_path=""
)


# ─── Frontend routes ───

@app.route("/")
def serve_index():
    """Serve the main HTML page."""
    return send_from_directory(app.static_folder, "index.html")


@app.route("/css/<path:filename>")
def serve_css(filename):
    return send_from_directory(os.path.join(app.static_folder, "css"), filename)


@app.route("/js/<path:filename>")
def serve_js(filename):
    return send_from_directory(os.path.join(app.static_folder, "js"), filename)


# ─── API routes ───

@app.route("/api/policies", methods=["GET"])
def api_policies():
    """Return list of available insurance policies."""
    retriever = OKFRetriever(config["BUNDLE_DIR"])
    policies = retriever.get_available_policies()
    return jsonify(policies)


@app.route("/api/profile", methods=["POST"])
def api_profile():
    """Generate a company profile using Gemini + web search."""
    data = request.get_json()
    company_name = data.get("company_name", "").strip()
    
    if not company_name:
        return jsonify({"error": "Company name is required"}), 400

    try:
        profile = generate_company_profile(company_name)
        return jsonify(profile)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/pitch", methods=["POST"])
def api_pitch():
    """Generate a marketing pitch from profile + policy selection."""
    data = request.get_json()
    profile = data.get("profile")
    policies = data.get("policies", [])

    if not profile:
        return jsonify({"error": "Company profile is required"}), 400
    if not policies:
        return jsonify({"error": "At least one policy must be selected"}), 400

    try:
        pitch = generate_marketing_pitch(profile, policies)
        return jsonify(pitch)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/audit", methods=["POST"])
def api_audit():
    """Audit pitch content against source policy knowledge."""
    data = request.get_json()
    pitch = data.get("pitch")
    policies = data.get("policies", [])

    if not pitch:
        return jsonify({"error": "Pitch data is required"}), 400

    # Use policies from pitch metadata if not provided
    if not policies:
        policies = pitch.get("_policy_ids", [])
    
    if not policies:
        return jsonify({"error": "Policy IDs are required for audit"}), 400

    try:
        audit = audit_pitch_content(pitch, policies)
        return jsonify(audit)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/download-pptx", methods=["POST"])
def api_download_pptx():
    """Generate a PowerPoint file from pitch data."""
    data = request.get_json()
    pitch = data.get("pitch")

    if not pitch:
        return jsonify({"error": "Pitch data is required"}), 400

    try:
        buffer = build_pptx(pitch)
        company = pitch.get("target_company", "company").replace(" ", "_")
        filename = f"pitch_{company}.pptx"

        return send_file(
            buffer,
            mimetype="application/vnd.openxmlformats-officedocument.presentationml.presentation",
            as_attachment=True,
            download_name=filename,
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ─── Run ───

if __name__ == "__main__":
    port = config.get("FLASK_PORT", 5000)
    debug = config.get("FLASK_DEBUG", False)
    
    print(f"\n  Marsh Pitch Generator")
    print(f"  http://localhost:{port}")
    print(f"  Press Ctrl+C to stop\n")
    
    app.run(host="0.0.0.0", port=port, debug=debug)
