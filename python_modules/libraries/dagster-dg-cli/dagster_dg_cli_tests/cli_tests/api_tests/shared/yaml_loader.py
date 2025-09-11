"""YAML loading utilities for fixture scenario configurations."""

from pathlib import Path

import yaml

from dagster_dg_cli_tests.cli_tests.api_tests.shared.fixture_config import FixtureScenario


def load_fixture_scenarios_from_yaml(yaml_file: Path) -> dict[str, FixtureScenario]:
    """Load fixture scenarios from a YAML file.

    Args:
        yaml_file: Path to YAML file containing fixture scenario definitions

    Returns:
        Dictionary mapping fixture names to FixtureScenario objects

    Raises:
        ValueError: If YAML file doesn't exist or has invalid format
    """
    if not yaml_file.exists():
        raise ValueError(f"YAML fixture file not found: {yaml_file}")

    try:
        with open(yaml_file) as f:
            yaml_data = yaml.safe_load(f) or {}
    except yaml.YAMLError as e:
        raise ValueError(f"Invalid YAML in {yaml_file}: {e}")

    fixture_scenarios = {}
    for fixture_name, config_data in yaml_data.items():
        if not isinstance(config_data, dict):
            raise ValueError(
                f"Invalid fixture config for '{fixture_name}': expected dict, got {type(config_data)}"
            )

        if "command" not in config_data:
            raise ValueError(f"Missing 'command' field for fixture '{fixture_name}'")

        fixture_scenarios[fixture_name] = FixtureScenario(
            command=config_data["command"],
            depends_on=config_data.get("depends_on"),
            has_recording=config_data.get("has_recording", True),
        )

    return fixture_scenarios
