"""Fixture loading utilities for asset API tests."""

import json
from pathlib import Path
from typing import Any

from dagster_dg_cli_tests.cli_tests.api_tests.shared.yaml_loader import (
    load_fixture_scenarios_from_yaml,
)


def load_asset_response_fixture(response_name: str) -> list[dict[str, Any]]:
    """Load asset GraphQL responses from a scenario folder.

    Args:
        response_name: Name of the response scenario (e.g., 'success_multiple_assets')

    Returns:
        List of GraphQL response data in order
    """
    return load_scenario_graphql_responses(response_name)


def load_scenario_graphql_responses(scenario_name: str) -> list[dict[str, Any]]:
    """Load GraphQL responses from a scenario folder.

    Args:
        scenario_name: Name of the scenario folder

    Returns:
        List of GraphQL responses in order (01_, 02_, etc.)
    """
    scenario_folder = Path(__file__).parent / scenario_name

    if not scenario_folder.exists():
        raise ValueError(f"Scenario folder not found: {scenario_folder}")

    # Find all numbered JSON files (01_*.json, 02_*.json, etc.)
    json_files = sorted([f for f in scenario_folder.glob("*.json") if f.name[0:2].isdigit()])

    if not json_files:
        raise ValueError(f"No numbered JSON files found in {scenario_folder}")

    responses = []
    for json_file in json_files:
        with open(json_file) as f:
            responses.append(json.load(f))

    return responses


def load_scenario_cli_output(scenario_name: str) -> str:
    """Load CLI output from a scenario folder.

    Args:
        scenario_name: Name of the scenario folder

    Returns:
        CLI output content
    """
    scenario_folder = Path(__file__).parent / scenario_name
    cli_output_file = scenario_folder / "cli_output.txt"

    if not cli_output_file.exists():
        raise ValueError(f"CLI output file not found: {cli_output_file}")

    with open(cli_output_file) as f:
        return f.read()


def get_asset_fixture_command(response_name: str) -> str:
    """Get the command that generates a specific asset fixture.

    Args:
        response_name: Name of the response fixture

    Returns:
        The dg command that generates this fixture
    """
    commands_file = Path(__file__).parent / "commands.yaml"
    fixture_commands = load_fixture_scenarios_from_yaml(commands_file)

    if response_name not in fixture_commands:
        available = list(fixture_commands.keys())
        raise ValueError(f"Fixture '{response_name}' not found. Available fixtures: {available}")

    return fixture_commands[response_name].command


def list_asset_fixtures() -> dict[str, Any]:
    """List all available asset fixtures."""
    commands_file = Path(__file__).parent / "commands.yaml"
    fixture_commands = load_fixture_scenarios_from_yaml(commands_file)

    return {
        fixture_name: {
            "command": config.command,
            "depends_on": config.depends_on or [],
        }
        for fixture_name, config in fixture_commands.items()
    }


def list_scenario_folders() -> list[str]:
    """List all available scenario folders."""
    fixtures_dir = Path(__file__).parent
    return [d.name for d in fixtures_dir.iterdir() if d.is_dir()]
