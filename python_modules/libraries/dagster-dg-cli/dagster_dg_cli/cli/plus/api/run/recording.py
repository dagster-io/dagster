"""Simple GraphQL recording for test fixture generation."""

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Optional


def record_graphql_interaction(
    query: str,
    variables: dict[str, Any],
    response: dict[str, Any],
    command_name: str,
    record_dir: Optional[str] = None,
) -> None:
    """Record a GraphQL request/response to a JSON file."""
    if not record_dir:
        # Default to a simple recordings directory
        record_path = Path.cwd() / "recordings"
    else:
        record_path = Path(record_dir)
    record_path.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{command_name}_{timestamp}.json"

    record_data = {
        "command": command_name,
        "timestamp": datetime.now().isoformat(),
        "request": {"query": query, "variables": variables},
        "response": response,
    }

    file_path = record_path / filename
    with open(file_path, "w") as f:
        json.dump(record_data, f, indent=2)

    print(f"📼 Recorded to: {file_path}")  # noqa: T201
