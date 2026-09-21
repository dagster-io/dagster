"""Record GraphQL responses for dg api command tests.

Invoke from a domain's Makefile, e.g. `python ../_record.py asset`.
Requires an authenticated Dagster Plus session — see `dg auth login`.
"""

import json
import sys
import traceback
from collections.abc import Mapping
from pathlib import Path
from typing import Any

import click
from click.testing import CliRunner
from dagster_dg_cli.cli import cli as root_cli
from dagster_dg_cli.cli.api.client import DgApiTestContext
from dagster_dg_cli.cli.api.shared import get_config_or_error
from dagster_rest_resources.gql_client import DagsterPlusGraphQLClient, IGraphQLClient
from dagster_shared.yaml_utils import safe_load_yaml

API_TESTS_DIR = Path(__file__).parent


class RecordingClient(IGraphQLClient):
    """GraphQL client that records all execute() calls for later replay."""

    def __init__(self, real_client: DagsterPlusGraphQLClient):
        self.real_client = real_client
        self.recorded_responses: list[dict[str, Any]] = []

    def execute_arbitrary(
        self,
        query: str,
        operation_name: str | None = None,
        variables: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        response = self.real_client.execute_arbitrary(query, operation_name, variables)
        self.recorded_responses.append(response)
        return response

    def get_recorded_responses(self) -> list[dict[str, Any]]:
        return self.recorded_responses


def load_domain_commands(domain: str) -> dict[str, dict]:
    """Load command registry for a domain from scenarios.yaml."""
    domain_dir = API_TESTS_DIR / f"{domain}_tests"
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
        with open(scenarios_file, encoding="utf-8") as f:
            scenarios_data = safe_load_yaml(f) or {}
        return scenarios_data
    except Exception as e:
        click.echo(f"Error loading scenarios.yaml: {e}", err=True)
        return {}


def record_graphql_for_fixture(domain: str, fixture_name: str, command: str) -> bool:
    """Record GraphQL response for a single fixture. Returns True if successful."""
    recording_dir = API_TESTS_DIR / f"{domain}_tests" / "recordings" / fixture_name
    recording_dir.mkdir(parents=True, exist_ok=True)
    click.echo(f"🚀 Recording for {domain}.{fixture_name}: {command}")

    try:
        try:
            config = get_config_or_error()
            real_client = DagsterPlusGraphQLClient(
                url=config.organization_url,
                api_token=config.user_token,
                organization=config.organization,
                deployment=config.default_deployment,
            )
        except Exception as e:
            raise click.ClickException(
                f"Failed to create GraphQL client for recording: {e}\n"
                "Make sure you're authenticated with Dagster Plus (run 'dg auth login' first)."
            )

        recording_client = RecordingClient(real_client)
        recording_context = DgApiTestContext(client_factory=lambda config: recording_client)

        runner = CliRunner()
        args = command.split()[1:]  # Skip 'dg'
        result = runner.invoke(root_cli, args, obj=recording_context, catch_exceptions=False)

        if result.exit_code != 0:
            click.echo(f"Command failed (exit code {result.exit_code}): {result.output}")
            click.echo("Recording GraphQL responses from failed command...")

        recorded_responses = recording_client.get_recorded_responses()

        if recorded_responses:
            for i, response in enumerate(recorded_responses, 1):
                json_file = recording_dir / f"{i:02d}_response.json"
                with open(json_file, "w", encoding="utf-8") as f:
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


@click.command()
@click.argument("domain", required=True)
@click.option(
    "--recording",
    type=str,
    help="Specific recording to record (if omitted, runs all recordings in domain)",
)
def main(domain: str, recording: str):
    """Record GraphQL responses for dg api tests in DOMAIN.

    Examples:
        # Record entire domain
        python _record.py asset

        # Record single recording
        python _record.py asset --recording success_multiple_assets
    """
    commands_data = load_domain_commands(domain)
    if not commands_data:
        sys.exit(1)

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

    if graphql_success:
        click.echo(f"🎉 Successfully recorded GraphQL for {domain}")
    else:
        click.echo(f"⚠️  GraphQL recording completed with some failures for {domain}")

    if not graphql_success:
        sys.exit(1)


if __name__ == "__main__":
    main()
