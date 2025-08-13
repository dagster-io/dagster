"""Fixture loading utilities for deployment API tests."""

import json
from pathlib import Path
from typing import Any

from dagster_dg_cli_tests.cli_tests.api_tests.shared.yaml_loader import (
    load_fixture_commands_from_yaml,
)


def load_deployment_response_fixture(response_name: str) -> dict[str, Any]:
    """Load a deployment GraphQL response fixture from JSON.

    Args:
        response_name: Name of the response fixture (e.g., 'success_multiple_deployments')

    Returns:
        The GraphQL response data
    """
    fixtures_file = Path(__file__).parent / "responses.json"

    if not fixtures_file.exists():
        raise ValueError(f"Fixture file not found: {fixtures_file}")

    with open(fixtures_file) as f:
        fixtures = json.load(f)

    if response_name not in fixtures:
        available = list(fixtures.keys())
        raise ValueError(
            f"Response fixture '{response_name}' not found in {fixtures_file}. "
            f"Available fixtures: {available}"
        )

    return fixtures[response_name]


def get_deployment_fixture_command(response_name: str) -> str:
    """Get the command that generates a specific deployment fixture.

    Args:
        response_name: Name of the response fixture

    Returns:
        The dg command that generates this fixture
    """
    commands_file = Path(__file__).parent / "commands.yaml"
    fixture_commands = load_fixture_commands_from_yaml(commands_file)

    if response_name not in fixture_commands:
        available = list(fixture_commands.keys())
        raise ValueError(f"Fixture '{response_name}' not found. Available fixtures: {available}")

    return fixture_commands[response_name].command


def list_deployment_fixtures() -> dict[str, Any]:
    """List all available deployment fixtures."""
    commands_file = Path(__file__).parent / "commands.yaml"
    fixture_commands = load_fixture_commands_from_yaml(commands_file)

    return {
        fixture_name: {
            "command": config.command,
            "depends_on": config.depends_on or [],
        }
        for fixture_name, config in fixture_commands.items()
    }
