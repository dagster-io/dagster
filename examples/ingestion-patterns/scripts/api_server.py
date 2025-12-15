#!/usr/bin/env python3
"""Simple API server that serves sample data for the pull ingestion pattern.

This server simulates an external data source API that Dagster can pull from.
It generates sample records and filters them by date range.
"""

import argparse
from datetime import datetime, timedelta
from typing import Any

from flask import Flask, jsonify, request

app = Flask(__name__)


def generate_sample_data() -> list[dict[str, Any]]:
    """Generate sample records spanning the last 7 days."""
    base_time = datetime.now() - timedelta(days=7)
    data = []
    for i in range(100):
        data.append(
            {
                "id": f"record-{i:03d}",
                "timestamp": (base_time + timedelta(hours=i)).isoformat(),
                "value": 100 + i * 10,
                "status": "active" if i % 2 == 0 else "inactive",
            }
        )
    return data


# Initialize sample data at module load time
app.config["SAMPLE_DATA"] = generate_sample_data()


@app.route("/health", methods=["GET"])
def health():
    """Health check endpoint."""
    return jsonify({"status": "healthy", "records_available": len(app.config["SAMPLE_DATA"])})


@app.route("/records", methods=["GET"])
def get_records():
    """Get records filtered by date range.

    Query parameters:
        start_date: ISO format datetime (inclusive)
        end_date: ISO format datetime (exclusive)

    Returns:
        JSON array of matching records
    """
    start_date_str = request.args.get("start_date")
    end_date_str = request.args.get("end_date")

    # Parse dates, defaulting to last 24 hours
    if end_date_str:
        end_date = datetime.fromisoformat(end_date_str)
    else:
        end_date = datetime.now()

    if start_date_str:
        start_date = datetime.fromisoformat(start_date_str)
    else:
        start_date = end_date - timedelta(days=1)

    # Filter records by date range
    sample_data = app.config["SAMPLE_DATA"]
    filtered = [
        record
        for record in sample_data
        if start_date <= datetime.fromisoformat(record["timestamp"]) < end_date
    ]

    return jsonify(filtered)


def main():
    parser = argparse.ArgumentParser(description="Sample data API server")
    parser.add_argument("--port", type=int, default=5051, help="Port to listen on (default: 5051)")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to (default: 0.0.0.0)")

    args = parser.parse_args()

    print(f"API server starting on {args.host}:{args.port}")  # noqa: T201
    print(f"Sample data: {len(app.config['SAMPLE_DATA'])} records available")  # noqa: T201
    print(f"Get records: GET http://localhost:{args.port}/records")  # noqa: T201

    app.run(host=args.host, port=args.port, debug=False)


if __name__ == "__main__":
    main()
