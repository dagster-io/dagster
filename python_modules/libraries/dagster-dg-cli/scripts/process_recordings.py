"""Process recorded GraphQL responses into test fixtures."""

import json
import sys
from pathlib import Path
from typing import Any, Optional


def load_recording(recording_path: Path) -> dict[str, Any]:
    """Load a recording file and return the data."""
    with open(recording_path) as f:
        return json.load(f)


def generate_fixture_name(command: str, response_data: dict[str, Any]) -> str:
    """Generate a Python variable name for the fixture."""
    # Extract noun and verb from command (e.g., "run_view" -> "RUN_VIEW")
    base_name = command.upper()

    # Determine if this is a success or error response
    if is_error_response(response_data):
        if "NotFound" in str(response_data):
            return f"{base_name}_NOT_FOUND_RESPONSE"
        elif "Error" in str(response_data):
            return f"{base_name}_ERROR_RESPONSE"
        else:
            return f"{base_name}_ERROR_RESPONSE"  # Generic error fallback
    else:
        return f"{base_name}_SUCCESS_RESPONSE"


def is_error_response(response_data: dict[str, Any]) -> bool:
    """Check if response represents an error."""
    # Look for error indicators in the response
    response_str = json.dumps(response_data)
    return any(
        pattern in response_str
        for pattern in [
            '"__typename": "RunNotFoundError"',
            '"__typename": "PythonError"',
            '"__typename": "InvalidPipelineRunsFilterError"',
            'Error"',  # General error pattern
        ]
    )


def format_python_fixture(fixture_name: str, response_data: dict[str, Any]) -> str:
    """Format the response data as a Python fixture."""
    # Use json.dumps with proper indentation
    json_str = json.dumps(response_data, indent=4)

    return f"""{fixture_name} = {json_str}

"""


def process_recording(recording_path: Path, output_dir: Optional[Path] = None) -> str:
    """Process a single recording file into test fixture format."""
    recording = load_recording(recording_path)

    command = recording["command"]
    response_data = recording["response"]

    # Generate fixture name and Python code
    fixture_name = generate_fixture_name(command, response_data)
    fixture_code = format_python_fixture(fixture_name, response_data)

    # Determine output location
    if not output_dir:
        # Default: put next to the recording file with .py extension
        output_path = recording_path.with_suffix(".py")
    else:
        output_path = output_dir / f"{recording_path.stem}.py"

    # Create header comment
    header = f'''"""Generated test fixture from recording.

Source: {recording_path.name}
Command: {command}
Recorded: {recording["timestamp"]}

To use in tests:
    from .fixtures.{output_path.stem} import {fixture_name}
"""

'''

    # Write the fixture file
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        f.write(header + fixture_code)

    return str(output_path)


def process_multiple_recordings(
    recording_dir: Path, output_file: Path, command_filter: Optional[str] = None
) -> None:
    """Process multiple recordings into a single fixtures file."""
    recording_files = list(recording_dir.glob("*.json"))

    if command_filter:
        # Filter recordings by command pattern (e.g., "run_")
        recording_files = [f for f in recording_files if command_filter in f.stem]

    if not recording_files:
        print(f"No recording files found in {recording_dir}")  # noqa: T201
        return

    # Process all recordings
    fixtures = []
    for recording_file in sorted(recording_files):
        try:
            recording = load_recording(recording_file)
            command = recording["command"]
            response_data = recording["response"]

            fixture_name = generate_fixture_name(command, response_data)
            fixture_code = format_python_fixture(fixture_name, response_data)

            fixtures.append(
                {
                    "name": fixture_name,
                    "code": fixture_code,
                    "source": recording_file.name,
                    "command": command,
                }
            )
        except Exception as e:
            print(f"Error processing {recording_file}: {e}")  # noqa: T201

    # Generate combined fixtures file
    header = f'''"""Generated test fixtures from recordings.

This file contains fixtures generated from recorded GraphQL responses.
Generated from {len(fixtures)} recordings in {recording_dir}

Usage:
    from .fixtures import *
    
    # Use in tests with mocking:
    mock_client.execute.return_value = RUN_VIEW_SUCCESS_RESPONSE
"""

'''

    # Write all fixtures to output file
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, "w") as f:
        f.write(header)
        for fixture in fixtures:
            f.write(f"# Generated from: {fixture['source']} ({fixture['command']})\n")
            f.write(fixture["code"])

    print(f"Generated {len(fixtures)} fixtures in {output_file}")  # noqa: T201


def main():
    """CLI interface for processing recordings."""
    if len(sys.argv) < 2:
        print("Usage:")  # noqa: T201
        print("  python scripts/process_recordings.py <recording_file>")  # noqa: T201
        print(  # noqa: T201
            "  python scripts/process_recordings.py <recordings_dir> <output_file> [command_filter]"
        )
        sys.exit(1)

    input_path = Path(sys.argv[1])

    if input_path.is_file():
        # Process single recording
        output_path = process_recording(input_path)
        print(f"Generated fixture: {output_path}")  # noqa: T201

    elif input_path.is_dir():
        # Process multiple recordings
        if len(sys.argv) < 3:
            print("Error: output file required when processing directory")  # noqa: T201
            sys.exit(1)

        output_file = Path(sys.argv[2])
        command_filter = sys.argv[3] if len(sys.argv) > 3 else None

        process_multiple_recordings(input_path, output_file, command_filter)

    else:
        print(f"Error: {input_path} not found")  # noqa: T201
        sys.exit(1)


if __name__ == "__main__":
    main()
