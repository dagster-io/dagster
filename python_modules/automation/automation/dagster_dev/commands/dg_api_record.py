"""Unified API recording command that replaces separate GraphQL and CLI recording.

This command combines the functionality of the previous record_graphql and record_cli_output
commands, with support for batch processing entire domains or individual fixtures.
"""

import json
import shlex
import subprocess
import sys
from pathlib import Path

import click
import yaml


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
    fixture_dir = api_tests_dir / f"{domain}_tests" / "fixtures"
    scenarios_file = fixture_dir / "scenarios.yaml"

    if not fixture_dir.exists():
        click.echo(f"Error: Domain directory not found: {fixture_dir}", err=True)
        available_domains = [d.name.replace("_tests", "") for d in api_tests_dir.glob("*_tests")]
        click.echo(f"Available domains: {available_domains}")
        return {}

    if not scenarios_file.exists():
        click.echo(f"Error: Scenarios file not found: {scenarios_file}", err=True)
        click.echo("Create the scenarios.yaml registry file first with your fixture commands.")
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
    fixture_dir = api_tests_dir / f"{domain}_tests" / "fixtures" / fixture_name

    fixture_dir.mkdir(parents=True, exist_ok=True)
    click.echo(f"🚀 Recording for {domain}.{fixture_name}: {command}")

    # Ensure --json flag is present for structured output
    if "--json" not in command:
        click.echo(
            f"Error: --json flag is required for GraphQL response capture: {command}", err=True
        )
        return False

    try:
        # Execute the dg command and capture output
        result = subprocess.run(
            shlex.split(command),
            capture_output=True,
            text=True,
            check=False,
            timeout=60,
        )

        # Note: cli_output.txt files are no longer created as they're not used by tests
        # Tests use syrupy snapshots instead

        # For JSON commands, also save the parsed response as a numbered JSON file
        if result.returncode == 0:
            try:
                graphql_response = json.loads(result.stdout)
                json_file = fixture_dir / "01_response.json"
                with open(json_file, "w") as f:
                    json.dump(graphql_response, f, indent=2, sort_keys=True)
                click.echo(f"✅ Captured successful response for {fixture_name}")
                click.echo(f"📄 Saved to {json_file}")
            except json.JSONDecodeError as e:
                click.echo(f"Warning: Command output is not valid JSON: {e}")
                click.echo("No JSON file created")
        else:
            click.echo(f"⚠️  Command failed with exit code {result.returncode}")
            if fixture_name.startswith("error_"):
                click.echo(f"✅ Captured error response for {fixture_name}")
            else:
                click.echo(f"❌ Unexpected failure for {fixture_name}")
                return False

        return True

    except subprocess.TimeoutExpired:
        click.echo(f"Error: Command timed out after 60 seconds: {command}", err=True)
        return False
    except KeyboardInterrupt:
        click.echo("\n⏹️  Recording interrupted", err=True)
        return False
    except Exception as e:
        click.echo(f"Error executing command: {e}", err=True)
        return False


@click.command(name="dg-api-record")
@click.argument("domain", required=True)
@click.option(
    "--fixture",
    type=str,
    help="Specific fixture to record (if omitted, runs all fixtures in domain)",
)
@click.option("--graphql", is_flag=True, help="Record GraphQL responses (Step 1)")
def dg_api_record(domain: str, fixture: str, graphql: bool):
    """Record GraphQL responses for API tests.

    Records GraphQL responses for API tests. Can process a single fixture or all fixtures in a domain.

    Args:
        domain: API domain (e.g., 'deployment', 'run', 'asset')

    Examples:
        # Record entire domain
        dagster-dev dg-api-record asset

        # Record single fixture
        dagster-dev dg-api-record asset --fixture success_multiple_assets

        # Record GraphQL only
        dagster-dev dg-api-record asset --graphql
    """
    # Always run GraphQL recording

    # Load domain commands
    commands_data = load_domain_commands(domain)
    if not commands_data:
        sys.exit(1)

    # Determine which fixtures to process
    if fixture:
        if fixture not in commands_data:
            available = list(commands_data.keys())
            click.echo(f"Error: Fixture '{fixture}' not found in {domain} commands", err=True)
            click.echo(f"Available fixtures: {available}")
            sys.exit(1)
        target_fixtures = [fixture]
    else:
        target_fixtures = list(commands_data.keys())

    click.echo(f"📁 Domain: {domain}")
    click.echo(f"🎯 Target fixtures: {target_fixtures}")
    click.echo("🔄 Steps: GraphQL")

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
