"""Tests for --response-schema flag on all dg commands that support --json."""

import json

import pytest
from click.testing import CliRunner

# All commands with their CLI args (using --response-schema, no auth needed)
RESPONSE_SCHEMA_COMMANDS = [
    # asset commands (deployment_scoped)
    ("api asset list --response-schema", "DgApiAssetList"),
    ("api asset get --response-schema", "DgApiAsset"),
    ("api asset get-events --response-schema", "DgApiAssetEventList"),
    ("api asset get-evaluations --response-schema", "DgApiEvaluationRecordList"),
    # deployment commands (organization_scoped)
    ("api deployment list --response-schema", "DeploymentList"),
    ("api deployment get --response-schema", "Deployment"),
    # agent commands (organization_scoped)
    ("api agent list --response-schema", "DgApiAgentList"),
    ("api agent get --response-schema", "DgApiAgent"),
    # run commands (deployment_scoped)
    ("api run get --response-schema", "DgApiRun"),
    ("api run get-events --response-schema", "RunEventList"),
    # schedule commands (deployment_scoped)
    ("api schedule list --response-schema", "DgApiScheduleList"),
    ("api schedule get --response-schema", "DgApiSchedule"),
    # sensor commands (deployment_scoped)
    ("api sensor list --response-schema", "DgApiSensorList"),
    ("api sensor get --response-schema", "DgApiSensor"),
    # secret commands (organization_scoped)
    ("api secret list --response-schema", "DgApiSecretList"),
    ("api secret get --response-schema", "DgApiSecret"),
    # list commands
    ("list components --response-schema", "DgComponentList"),
    ("list registry-modules --response-schema", "DgRegistryModuleList"),
    ("list defs --response-schema", "DgDefinitionMetadataSchema"),
]


class TestResponseSchema:
    """Verify --response-schema prints valid JSON Schema and exits 0 for every command."""

    @pytest.mark.parametrize(
        "command,expected_title",
        RESPONSE_SCHEMA_COMMANDS,
        ids=[cmd for cmd, _ in RESPONSE_SCHEMA_COMMANDS],
    )
    def test_response_schema_flag(self, command: str, expected_title: str, monkeypatch):
        """Each command with --response-schema should exit 0, output valid JSON Schema,
        and require no auth credentials.
        """
        from dagster_dg_cli.cli import cli as root_cli

        # Clear auth env vars to prove no auth is needed
        monkeypatch.delenv("DAGSTER_CLOUD_API_TOKEN", raising=False)
        monkeypatch.delenv("DAGSTER_CLOUD_ORGANIZATION", raising=False)
        monkeypatch.delenv("DAGSTER_CLOUD_DEPLOYMENT", raising=False)

        runner = CliRunner()
        result = runner.invoke(root_cli, command.split())

        assert result.exit_code == 0, (
            f"Command '{command}' failed with exit code {result.exit_code}:\n{result.output}"
        )

        schema = json.loads(result.output)

        # Verify it looks like a JSON Schema
        assert "title" in schema, f"Missing 'title' in schema for '{command}'"
        assert schema["title"] == expected_title
        assert "properties" in schema or "$defs" in schema, (
            f"Missing 'properties' or '$defs' in schema for '{command}'"
        )
