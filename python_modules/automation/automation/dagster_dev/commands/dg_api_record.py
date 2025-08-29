"""Unified API recording command that replaces separate GraphQL and CLI recording.

This command combines the functionality of the previous record_graphql and record_cli_output
commands, with support for batch processing entire domains or individual fixtures.
"""

import json
import sys
import traceback
from collections.abc import Mapping
from pathlib import Path
from typing import Any, Optional

import click
import yaml
from dagster_dg_cli.utils.plus.gql_client import DagsterPlusGraphQLClient, IGraphQLClient


class RecordingClient(IGraphQLClient):
    """GraphQL client that records all execute() calls for later replay."""

    def __init__(self, real_client: DagsterPlusGraphQLClient):
        """Wrap a real GraphQL client to record its responses."""
        self.real_client = real_client
        self.recorded_responses = []

    def execute(self, query: str, variables: Optional[Mapping[str, Any]] = None) -> dict:
        """Execute query on real client and record the response."""
        response = self.real_client.execute(query, variables)
        self.recorded_responses.append(response)
        return response

    def get_recorded_responses(self) -> list[dict[str, Any]]:
        """Return all recorded GraphQL responses."""
        return self.recorded_responses


def find_repo_root() -> Path:
    """Get repository root relative to this command file location."""
    # This file is at: python_modules/automation/automation/dagster_dev/commands/dg_api_record.py
    # Repo root is: ../../../../../ from this file (6 levels up)
    command_file = Path(__file__).absolute()
    repo_root = command_file.parent.parent.parent.parent.parent.parent
    return repo_root


def load_domain_commands(domain: str) -> dict[str, dict]:
    """Load command registry for a domain from scenarios.yaml."""
    repo_root = find_repo_root()
    api_tests_dir = (
        repo_root
        / "python_modules"
        / "libraries"
        / "dagster-dg-cli"
        / "dagster_dg_cli_tests"
        / "cli_tests"
        / "api_tests"
    )
    domain_dir = api_tests_dir / f"{domain}_tests"
    recordings_dir = domain_dir / "recordings"
    scenarios_file = domain_dir / "scenarios.yaml"

    if not recordings_dir.exists():
        click.echo(f"Creating domain directory: {recordings_dir}")
        recordings_dir.mkdir(parents=True, exist_ok=True)

    if not scenarios_file.exists():
        click.echo(f"Error: Scenarios file not found: {scenarios_file}", err=True)
        click.echo("Create the scenarios.yaml registry file first with your recording commands.")
        return {}

    try:
        with open(scenarios_file) as f:
            scenarios_data = yaml.safe_load(f) or {}
        return scenarios_data
    except Exception as e:
        click.echo(f"Error loading scenarios.yaml: {e}", err=True)
        return {}


def record_graphql_for_fixture(domain: str, fixture_name: str, command: str) -> bool:
    """Record GraphQL response for a single fixture. Returns True if successful.

    Args:
        domain: API domain (e.g., 'asset', 'deployment')
        fixture_name: Name of the fixture scenario
        command: Command to execute
    """
    repo_root = find_repo_root()
    api_tests_dir = (
        repo_root
        / "python_modules"
        / "libraries"
        / "dagster-dg-cli"
        / "dagster_dg_cli_tests"
        / "cli_tests"
        / "api_tests"
    )
    recording_dir = api_tests_dir / f"{domain}_tests" / "recordings" / fixture_name

    recording_dir.mkdir(parents=True, exist_ok=True)
    click.echo(f"🚀 Recording for {domain}.{fixture_name}: {command}")

    try:
        # Import dependencies needed for command execution
        from click.testing import CliRunner
        from dagster_dg_cli.cli import cli as root_cli
        from dagster_dg_cli.cli.api.client import DgApiTestContext
        from dagster_dg_cli.utils.plus.gql_client import DagsterPlusGraphQLClient

        # Create a real GraphQL client for recording (assumes user is already authenticated)
        try:
            # Use the default config resolution - same as normal CLI commands
            from dagster_dg_cli.cli.api.shared import get_config_or_error

            config = get_config_or_error()
            real_client = DagsterPlusGraphQLClient.from_config(config)
        except Exception as e:
            raise click.ClickException(
                f"Failed to create GraphQL client for recording: {e}\n"
                "Make sure you're authenticated with Dagster Plus (run 'dg auth login' first)."
            )

        # Wrap in recording client
        recording_client = RecordingClient(real_client)

        # Create test context with recording client
        recording_context = DgApiTestContext(client_factory=lambda config: recording_client)

        # Execute command with recording context
        runner = CliRunner()
        args = command.split()[1:]  # Skip 'dg'
        result = runner.invoke(root_cli, args, obj=recording_context, catch_exceptions=False)

        # For error scenarios, we still want to record the GraphQL responses even if command failed
        # The GraphQL client will have recorded the error responses that we need for testing
        if result.exit_code != 0:
            click.echo(f"Command failed (exit code {result.exit_code}): {result.output}")
            click.echo("Recording GraphQL responses from failed command...")

        # Save recorded GraphQL responses (including error responses)
        recorded_responses = recording_client.get_recorded_responses()

        if recorded_responses:
            for i, response in enumerate(recorded_responses, 1):
                json_file = recording_dir / f"{i:02d}_response.json"
                with open(json_file, "w") as f:
                    json.dump(response, f, indent=2, sort_keys=True)
                click.echo(f"📄 Saved GraphQL response {i} to {json_file}")

            click.echo(
                f"✅ Captured {len(recorded_responses)} GraphQL response(s) for {fixture_name}"
            )
        else:
            click.echo(f"⚠️  No GraphQL responses recorded for {fixture_name}")

        return True

    except KeyboardInterrupt:
        click.echo("\n⏹️  Recording interrupted", err=True)
        return False
    except Exception as e:
        click.echo(f"Error executing command: {e}", err=True)
        click.echo("🔍 Full traceback:")
        click.echo(traceback.format_exc())
        return False


@click.command(name="dg-api-record")
@click.argument("domain", required=True)
@click.option(
    "--recording",
    type=str,
    help="Specific recording to record (if omitted, runs all recordings in domain)",
)
def dg_api_record(domain: str, recording: str):
    """Record GraphQL responses for API tests.

    Records GraphQL responses for API tests. Can process a single fixture or all fixtures in a domain.

    Args:
        domain: API domain (e.g., 'deployment', 'run', 'asset')

    Examples:
        # Record entire domain
        dagster-dev dg-api-record asset

        # Record single recording
        dagster-dev dg-api-record asset --recording success_multiple_assets

    """
    # Load domain commands
    commands_data = load_domain_commands(domain)
    if not commands_data:
        sys.exit(1)

    # Determine which recordings to process
    if recording:
        if recording not in commands_data:
            available = list(commands_data.keys())
            click.echo(f"Error: Recording '{recording}' not found in {domain} commands", err=True)
            click.echo(f"Available recordings: {available}")
            sys.exit(1)
        target_fixtures = [recording]
    else:
        target_fixtures = list(commands_data.keys())

    click.echo(f"📁 Domain: {domain}")
    click.echo(f"🎯 Target recordings: {target_fixtures}")
    click.echo("🔄 Steps: Recording")

    # Process GraphQL recording
    click.echo(f"🚀 Recording GraphQL responses for {domain}...")
    graphql_success = True
    for fixture_name in target_fixtures:
        fixture_data = commands_data[fixture_name]
        command = fixture_data if isinstance(fixture_data, str) else fixture_data.get("command", "")

        if not command:
            click.echo(f"Error: No command found for fixture {fixture_name}", err=True)
            graphql_success = False
            continue

        success = record_graphql_for_fixture(domain, fixture_name, command)
        if not success:
            graphql_success = False
            click.echo(f"❌ Failed to record GraphQL for {fixture_name}")
        else:
            click.echo(f"✅ GraphQL recorded for {fixture_name}")

    # Final status
    if graphql_success:
        click.echo(f"🎉 Successfully recorded GraphQL for {domain}")
    else:
        click.echo(f"⚠️  GraphQL recording completed with some failures for {domain}")

    # Exit with error code if any step failed
    if not graphql_success:
        sys.exit(1)
