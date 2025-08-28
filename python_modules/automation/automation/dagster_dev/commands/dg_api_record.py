"""Unified API recording command that replaces separate GraphQL and CLI recording.

This command combines the functionality of the previous record_graphql and record_cli_output
commands, with support for batch processing entire domains or individual fixtures.
"""

import json
import subprocess
import sys
from pathlib import Path
from typing import Any

import click


def find_repo_root() -> Path:
    """Get repository root relative to this command file location."""
    # This file is at: python_modules/automation/automation/dagster_dev/commands/dg_api_record.py
    # Repo root is: ../../../../../ from this file (6 levels up)
    command_file = Path(__file__).absolute()
    repo_root = command_file.parent.parent.parent.parent.parent.parent
    return repo_root


def generate_query_name(query: str) -> str:
    """Generate a descriptive name from GraphQL query."""
    lines = query.strip().split("\n")
    for line in lines:
        stripped_line = line.strip()
        if stripped_line.startswith(("query ", "mutation ")):
            # Extract name after 'query ' or 'mutation '
            parts = stripped_line.split()
            if len(parts) > 1:
                name = parts[1].split("(")[0]  # Remove parameters
                return name.lower()

    # Fallback to generic names based on query content
    if "assetRecords" in query:
        return "asset_records_query"
    elif "assetNodes" in query:
        return "asset_nodes_query"
    elif "deployment" in query.lower():
        return "deployment_query"
    else:
        return "graphql_query"


def intercept_graphql_calls(command: str) -> list[dict[str, Any]]:
    """Intercept GraphQL calls during command execution.

    This is a placeholder implementation. In a real implementation,
    you would need to patch the GraphQL client to capture calls.

    Returns:
        List of intercepted GraphQL calls with query and response data
    """
    # TODO: Implement actual GraphQL interception
    # This would require patching the DagsterPlusGraphQLClient.execute method
    # and capturing both the query/variables and the response

    # For now, return empty list to maintain backwards compatibility
    # The main logic will fall back to the existing approach
    return []


def load_domain_commands(domain: str) -> dict[str, dict]:
    """Load command registry for a domain from commands.yaml."""
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
    commands_file = fixture_dir / "commands.yaml"

    if not fixture_dir.exists():
        click.echo(f"Error: Domain directory not found: {fixture_dir}", err=True)
        available_domains = [d.name.replace("_tests", "") for d in api_tests_dir.glob("*_tests")]
        click.echo(f"Available domains: {available_domains}")
        return {}

    if not commands_file.exists():
        click.echo(f"Error: Commands file not found: {commands_file}", err=True)
        click.echo("Create the commands.yaml registry file first with your fixture commands.")
        return {}

    try:
        import yaml

        with open(commands_file) as f:
            commands_data = yaml.safe_load(f) or {}
        return commands_data
    except Exception as e:
        click.echo(f"Error loading commands.yaml: {e}", err=True)
        return {}


def record_graphql_for_fixture(
    domain: str, fixture_name: str, command: str, use_folder_structure: bool = False
) -> bool:
    """Record GraphQL response for a single fixture. Returns True if successful.

    Args:
        domain: API domain (e.g., 'asset', 'deployment')
        fixture_name: Name of the fixture scenario
        command: Command to execute
        use_folder_structure: If True, use new folder-per-scenario structure
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
    fixture_dir = api_tests_dir / f"{domain}_tests" / "fixtures"

    if use_folder_structure:
        scenario_folder = fixture_dir / fixture_name
        scenario_folder.mkdir(parents=True, exist_ok=True)
        click.echo(f"🚀 Recording scenario folder for {domain}.{fixture_name}: {command}")
    else:
        fixture_file = fixture_dir / "responses.json"
        fixture_dir.mkdir(
            parents=True, exist_ok=True
        )  # Create fixture directory if it doesn't exist
        click.echo(f"🚀 Recording GraphQL for {domain}.{fixture_name}: {command}")

    # Ensure --json flag is present for structured output
    if "--json" not in command:
        click.echo(
            f"Error: --json flag is required for GraphQL response capture: {command}", err=True
        )
        return False

    try:
        # Execute the dg command and capture output
        result = subprocess.run(
            command.split(),
            capture_output=True,
            text=True,
            check=False,
            timeout=60,
        )

        if use_folder_structure:
            # For folder structure, we'll intercept GraphQL calls and save them separately
            graphql_responses = intercept_graphql_calls(command)
            if graphql_responses:
                # Save each GraphQL response as numbered JSON files
                for i, response in enumerate(graphql_responses, 1):
                    response_file = (
                        scenario_folder
                        / f"{i:02d}_{generate_query_name(response.get('query', ''))}.json"
                    )
                    with open(response_file, "w") as f:
                        json.dump(response.get("data", {}), f, indent=2)
                    click.echo(f"💾 Saved GraphQL response: {response_file}")

                # Save CLI output
                cli_output_file = scenario_folder / "cli_output.txt"
                with open(cli_output_file, "w") as f:
                    f.write(
                        result.stdout
                        if result.returncode == 0
                        else f"STDERR:\n{result.stderr}\nSTDOUT:\n{result.stdout}"
                    )
                click.echo(f"📄 Saved CLI output: {cli_output_file}")

                return True
            else:
                click.echo(f"❌ No GraphQL calls intercepted for {fixture_name}")
                return False
        else:
            # Load existing fixtures or create empty dict
            existing_fixtures = {}
            if fixture_file.exists():
                try:
                    with open(fixture_file) as f:
                        existing_fixtures = json.load(f)
                except (OSError, json.JSONDecodeError) as e:
                    click.echo(f"Warning: Could not load existing fixtures: {e}")

        # Process the command output
        if result.returncode == 0:
            try:
                # Parse the CLI output as JSON - this should be the GraphQL response
                graphql_response = json.loads(result.stdout)
                existing_fixtures[fixture_name] = graphql_response

                click.echo(f"✅ Captured successful response for {fixture_name}")

            except json.JSONDecodeError as e:
                click.echo(f"Error: Command output is not valid JSON: {e}", err=True)
                click.echo(f"Output was: {result.stdout[:500]}...", err=True)
                return False

        else:
            # Handle error responses - especially useful for error fixtures
            click.echo(f"⚠️  Command failed with exit code {result.returncode}")

            if fixture_name.startswith("error_"):
                # For error fixtures, try to capture structured error response
                try:
                    if result.stdout:
                        # Try parsing stdout first (might be JSON error response)
                        error_data = json.loads(result.stdout)
                    else:
                        # Fallback to generic error structure
                        error_data = {
                            "error": result.stderr.strip() or "Command failed",
                            "exit_code": result.returncode,
                        }

                    existing_fixtures[fixture_name] = error_data

                    click.echo(f"✅ Captured error response for {fixture_name}")

                except json.JSONDecodeError:
                    # Create a generic error structure
                    error_data = {
                        "error": result.stderr.strip() or result.stdout.strip() or "Command failed",
                        "exit_code": result.returncode,
                    }
                    existing_fixtures[fixture_name] = error_data

                    click.echo(f"✅ Captured generic error for {fixture_name}")
            else:
                click.echo(
                    f"Error: Command failed but fixture name doesn't indicate error case: {fixture_name}",
                    err=True,
                )
                click.echo(f"Exit code: {result.returncode}", err=True)
                click.echo(f"Stderr: {result.stderr}", err=True)
                return False

        if not use_folder_structure:
            # Write the updated fixtures back to file (legacy format)
            fixture_dir.mkdir(parents=True, exist_ok=True)
            with open(fixture_file, "w") as f:
                json.dump(existing_fixtures, f, indent=2, sort_keys=True)

            # Also save the raw CLI output as a text file for easy inspection
            output_file = fixture_dir / f"{fixture_name}_output.txt"
            with open(output_file, "w") as f:
                if result.returncode == 0:
                    f.write(result.stdout)
                else:
                    f.write("=== STDERR ===\n")
                    f.write(result.stderr)
                    f.write("\n=== STDOUT ===\n")
                    f.write(result.stdout)

            # Get file sizes and report them
            fixture_file_size = fixture_file.stat().st_size
            output_file_size = output_file.stat().st_size

            click.echo(f"💾 Updated {fixture_file} ({fixture_file_size} bytes)")
            click.echo(f"📄 Saved CLI output to {output_file} ({output_file_size} bytes)")

        return True

    except subprocess.TimeoutExpired:
        click.echo(f"Error: Command timed out after 60 seconds: {command}", err=True)
        return False
    except KeyboardInterrupt:
        click.echo("\\n⏹️  Recording interrupted", err=True)
        return False
    except Exception as e:
        click.echo(f"Error executing command: {e}", err=True)
        return False


def record_cli_for_domain(domain: str) -> bool:
    """Record CLI output snapshots for entire domain. Returns True if successful."""
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
    domain_tests_dir = api_tests_dir / f"{domain}_tests"
    fixture_file = domain_tests_dir / "fixtures" / "responses.json"

    if not domain_tests_dir.exists():
        click.echo(f"Error: Domain test directory not found: {domain_tests_dir}", err=True)
        return False

    if not fixture_file.exists():
        click.echo(f"Error: Fixture file not found: {fixture_file}", err=True)
        click.echo("Run GraphQL recording first to capture GraphQL responses.")
        return False

    click.echo(f"🧪 Recording CLI output for domain: {domain}")

    try:
        # Run pytest with snapshot update for the specific domain tests
        pytest_command = [
            "python",
            "-m",
            "pytest",
            str(domain_tests_dir),
            "--snapshot-update",
            "-v",
        ]

        click.echo(f"Running: {' '.join(pytest_command)}")

        # Run pytest from the repo root so imports work correctly
        result = subprocess.run(
            pytest_command,
            cwd=repo_root,
            capture_output=False,  # Always show output (verbose behavior)
            text=True,
            check=False,
        )

        if result.returncode == 0:
            click.echo(f"✅ Successfully updated CLI output snapshots for {domain}")
            if result.stdout:
                click.echo("Test output:")
                click.echo(result.stdout)
        else:
            click.echo(f"⚠️  pytest completed with issues (exit code {result.returncode})")
            if result.stdout:
                click.echo("Stdout:")
                click.echo(result.stdout)
            if result.stderr:
                click.echo("Stderr:")
                click.echo(result.stderr)

            # Don't treat test failures as fatal - snapshots may still have been updated
            click.echo("Note: Snapshot files may still have been updated despite test issues.")

        # Show what snapshot files were updated
        snapshots_dir = domain_tests_dir / "__snapshots__"
        if snapshots_dir.exists():
            snapshot_files = list(snapshots_dir.glob("*.ambr"))
            if snapshot_files:
                click.echo("📸 Updated snapshot files:")
                for snapshot_file in sorted(snapshot_files):
                    click.echo(f"  - {snapshot_file.name}")
            else:
                click.echo("⚠️  No snapshot files found - tests may not have run correctly")
        else:
            click.echo("⚠️  Snapshots directory not found - tests may not have run correctly")

        return result.returncode == 0

    except subprocess.TimeoutExpired:
        click.echo("Error: pytest timed out", err=True)
        return False
    except KeyboardInterrupt:
        click.echo("\\n⏹️  Recording interrupted", err=True)
        return False
    except Exception as e:
        click.echo(f"Error running pytest: {e}", err=True)
        return False


@click.command(name="dg-api-record")
@click.argument("domain", required=True)
@click.option(
    "--fixture",
    type=str,
    help="Specific fixture to record (if omitted, runs all fixtures in domain)",
)
@click.option("--graphql", is_flag=True, help="Record GraphQL responses (Step 1)")
@click.option("--cli", is_flag=True, help="Record CLI output snapshots (Step 2)")
@click.option("--all", "all_steps", is_flag=True, help="Run both GraphQL and CLI recording")
@click.option(
    "--folder-structure",
    is_flag=True,
    help="Use new folder-per-scenario structure instead of responses.json",
)
def dg_api_record(
    domain: str, fixture: str, graphql: bool, cli: bool, all_steps: bool, folder_structure: bool
):
    """Unified API recording command for GraphQL and CLI snapshots.

    Records GraphQL responses and/or CLI output snapshots for API tests.
    Can process a single fixture or all fixtures in a domain.

    Args:
        domain: API domain (e.g., 'deployment', 'run', 'asset')

    Examples:
        # Record entire domain (both GraphQL and CLI)
        dagster-dev dg-api-record asset

        # Record single fixture
        dagster-dev dg-api-record asset --fixture success_multiple_assets

        # Record GraphQL only for entire domain
        dagster-dev dg-api-record asset --graphql

        # Record CLI only for single fixture
        dagster-dev dg-api-record asset --fixture success_single_asset --cli
    """
    # Determine which steps to run
    if not graphql and not cli and not all_steps:
        # Default: run both steps
        run_graphql = True
        run_cli = True
    elif all_steps:
        run_graphql = True
        run_cli = True
    else:
        run_graphql = graphql
        run_cli = cli

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
    click.echo(
        f"🔄 Steps: {'GraphQL' if run_graphql else ''}{' + ' if run_graphql and run_cli else ''}{'CLI' if run_cli else ''}"
    )

    # Process GraphQL recording
    graphql_success = True
    if run_graphql:
        click.echo(f"🚀 Recording GraphQL responses for {domain}...")
        for fixture_name in target_fixtures:
            fixture_data = commands_data[fixture_name]
            command = (
                fixture_data if isinstance(fixture_data, str) else fixture_data.get("command", "")
            )

            if not command:
                click.echo(f"Error: No command found for fixture {fixture_name}", err=True)
                graphql_success = False
                continue

            success = record_graphql_for_fixture(
                domain, fixture_name, command, use_folder_structure=folder_structure
            )
            if not success:
                graphql_success = False
                click.echo(f"❌ Failed to record GraphQL for {fixture_name}")
            else:
                click.echo(f"✅ GraphQL recorded for {fixture_name}")

    # Process CLI recording
    cli_success = True
    if run_cli:
        click.echo(f"🧪 Recording CLI snapshots for {domain}...")
        cli_success = record_cli_for_domain(domain)

    # Final status
    if run_graphql and run_cli:
        if graphql_success and cli_success:
            click.echo(f"🎉 Successfully recorded both GraphQL and CLI for {domain}")
        else:
            click.echo(f"⚠️  Recording completed with some failures for {domain}")
    elif run_graphql:
        if graphql_success:
            click.echo(f"🎉 Successfully recorded GraphQL for {domain}")
        else:
            click.echo(f"⚠️  GraphQL recording completed with some failures for {domain}")
    elif run_cli:
        if cli_success:
            click.echo(f"🎉 Successfully recorded CLI snapshots for {domain}")
        else:
            click.echo(f"⚠️  CLI recording completed with failures for {domain}")

    # Exit with error code if any step failed
    if (run_graphql and not graphql_success) or (run_cli and not cli_success):
        sys.exit(1)
