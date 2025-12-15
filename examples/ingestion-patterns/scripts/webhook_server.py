#!/usr/bin/env python3
import argparse
import json
import os
import uuid
from datetime import datetime
from pathlib import Path

from flask import Flask, jsonify, request

app = Flask(__name__)

# File-based storage for webhook payloads (shared with Dagster)
WEBHOOK_STORAGE_DIR = Path(os.environ.get("WEBHOOK_STORAGE_DIR", "/tmp/webhook_storage"))


def ensure_storage_dir():
    """Ensure the storage directory exists."""
    WEBHOOK_STORAGE_DIR.mkdir(parents=True, exist_ok=True)


def save_payload(source_id: str, payload: dict) -> str:
    """Save a webhook payload to file storage."""
    ensure_storage_dir()

    # Add metadata
    payload_id = payload.get("id", str(uuid.uuid4()))
    enriched_payload = {
        **payload,
        "id": payload_id,
        "received_at": datetime.now().isoformat(),
        "source_id": source_id,
    }

    # Save to source-specific file
    source_file = WEBHOOK_STORAGE_DIR / f"{source_id}.json"

    # Load existing payloads
    existing = []
    if source_file.exists():
        with open(source_file) as f:
            existing = json.load(f)

    # Append new payload
    existing.append(enriched_payload)

    # Save back
    with open(source_file, "w") as f:
        json.dump(existing, f, indent=2)

    return payload_id


@app.route("/health", methods=["GET"])
def health():
    """Health check endpoint."""
    return jsonify({"status": "healthy", "storage_dir": str(WEBHOOK_STORAGE_DIR)})


@app.route("/webhook/<source_id>", methods=["POST"])
def receive_webhook(source_id: str):
    """Receive a webhook payload and store it for processing."""
    if not request.is_json:
        return jsonify({"error": "Content-Type must be application/json"}), 400

    payload = request.get_json()

    # Validate required fields
    if "timestamp" not in payload:
        payload["timestamp"] = datetime.now().isoformat()

    if "data" not in payload:
        payload["data"] = {}

    payload_id = save_payload(source_id, payload)

    print(  # noqa: T201
        f"[{datetime.now().isoformat()}] Received webhook: source={source_id}, id={payload_id}"
    )

    return jsonify(
        {
            "status": "received",
            "id": payload_id,
            "source": source_id,
        }
    ), 201


@app.route("/webhook/<source_id>/pending", methods=["GET"])
def get_pending(source_id: str):
    """Get pending payloads for a source (for debugging)."""
    source_file = WEBHOOK_STORAGE_DIR / f"{source_id}.json"

    if not source_file.exists():
        return jsonify({"source": source_id, "pending": [], "count": 0})

    with open(source_file) as f:
        payloads = json.load(f)

    return jsonify({"source": source_id, "pending": payloads, "count": len(payloads)})


@app.route("/webhook/<source_id>/clear", methods=["DELETE"])
def clear_pending(source_id: str):
    """Clear pending payloads for a source."""
    source_file = WEBHOOK_STORAGE_DIR / f"{source_id}.json"

    if source_file.exists():
        source_file.unlink()

    return jsonify({"status": "cleared", "source": source_id})


def main():
    parser = argparse.ArgumentParser(description="Webhook receiver server")
    parser.add_argument("--port", type=int, default=5050, help="Port to listen on (default: 5050)")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to (default: 0.0.0.0)")

    args = parser.parse_args()

    ensure_storage_dir()
    print(f"Webhook server starting on {args.host}:{args.port}")  # noqa: T201
    print(f"Storage directory: {WEBHOOK_STORAGE_DIR}")  # noqa: T201
    print(f"Send webhooks to: POST http://localhost:{args.port}/webhook/<source_id>")  # noqa: T201

    app.run(host=args.host, port=args.port, debug=False)


if __name__ == "__main__":
    main()
