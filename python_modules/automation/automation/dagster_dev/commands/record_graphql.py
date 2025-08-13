"""Record GraphQL API responses from live traffic (Step 1 of two-step recording).

This command executes live dg plus api commands and captures the GraphQL responses,
updating fixture files with fresh API data.
"""

import json
import subprocess
import sys
from pathlib import Path

import click


@click.command(name="dg-api-record-graphql", context_settings={"ignore_unknown_options": True})
@click.argument("domain", required=True)
@click.argument("fixture_name", required=True)
@click.option("--verbose", "-v", is_flag=True, help="Verbose output")
def record_graphql(domain: str, fixture_name: str, verbose: bool):
    """Record GraphQL API responses from live traffic.

    Reads the command from the domain's commands registry and executes it,
    capturing the GraphQL response and updating the domain's responses.json fixture file.

    Args:
        domain: API domain (e.g., 'deployment', 'run', 'asset')
        fixture_name: Name of the fixture to update (e.g., 'success_multiple_deployments')

    Examples:
        dagster-dev dg-api-record-graphql deployment success_multiple_deployments
        dagster-dev dg-api-record-graphql run error_not_found
    """
    # Determine the fixture file location
    api_tests_dir = (
        Path.cwd()
        / "python_modules"
        / "libraries"
        / "dagster-dg-cli"
        / "dagster_dg_cli_tests"
        / "cli_tests"
        / "api_tests"
    )
    fixture_dir = api_tests_dir / f"{domain}_tests" / "fixtures"
    fixture_file = fixture_dir / "responses.json"
    commands_file = fixture_dir / "commands.py"

    if not fixture_dir.exists():
        click.echo(f"Error: Domain directory not found: {fixture_dir}", err=True)
        click.echo(
            f"Available domains: {[d.name.replace('_tests', '') for d in api_tests_dir.glob('*_tests')]}"
        )
        sys.exit(1)

    # Load the command from the commands registry
    if not commands_file.exists():
        click.echo(f"Error: Commands file not found: {commands_file}", err=True)
        click.echo("Create the commands registry file first with your fixture command.")
        sys.exit(1)

    # Import the commands registry dynamically
    import importlib.util

    spec = importlib.util.spec_from_file_location("commands", commands_file)
    if spec is None:
        click.echo(f"Error: Could not create module spec from {commands_file}", err=True)
        sys.exit(1)

    commands_module = importlib.util.module_from_spec(spec)
    if spec.loader is None:
        click.echo(f"Error: Module spec has no loader for {commands_file}", err=True)
        sys.exit(1)

    spec.loader.exec_module(commands_module)

    # Get the commands dictionary (try both domain-specific and generic names)
    commands_dict = None
    for attr_name in dir(commands_module):
        if attr_name.endswith("_FIXTURE_COMMANDS") or attr_name == "FIXTURE_COMMANDS":
            commands_dict = getattr(commands_module, attr_name)
            break

    if not commands_dict:
        click.echo(f"Error: No fixture commands dictionary found in {commands_file}", err=True)
        click.echo(
            "Expected a dictionary named like 'DEPLOYMENT_FIXTURE_COMMANDS' or 'FIXTURE_COMMANDS'"
        )
        sys.exit(1)

    if fixture_name not in commands_dict:
        available = list(commands_dict.keys())
        click.echo(f"Error: Fixture '{fixture_name}' not found in commands registry", err=True)
        click.echo(f"Available fixtures: {available}")
        sys.exit(1)

    # Get the command to execute
    fixture_command = commands_dict[fixture_name]
    dg_command = fixture_command.command

    # Ensure --json flag is present for structured output
    if "--json" not in dg_command:
        click.echo("Error: --json flag is required for GraphQL response capture", err=True)
        sys.exit(1)

    if verbose:
        click.echo(f"📁 Domain: {domain}")
        click.echo(f"🎯 Fixture: {fixture_name}")
        click.echo(f"📂 File: {fixture_file}")
        click.echo(f"🚀 Command: {dg_command}")
        click.echo(f"📝 Description: {fixture_command.description}")

    try:
        # Execute the dg command and capture output
        result = subprocess.run(
            dg_command.split(),
            capture_output=True,
            text=True,
            check=False,
            timeout=60,  # 60 second timeout
        )

        # Load existing fixtures or create empty dict
        existing_fixtures = {}
        if fixture_file.exists():
            try:
                with open(fixture_file) as f:
                    existing_fixtures = json.load(f)
            except (OSError, json.JSONDecodeError) as e:
                if verbose:
                    click.echo(f"Warning: Could not load existing fixtures: {e}")

        # Process the command output
        if result.returncode == 0:
            try:
                # Parse the CLI output as JSON - this should be the GraphQL response
                graphql_response = json.loads(result.stdout)
                existing_fixtures[fixture_name] = graphql_response

                if verbose:
                    click.echo(f"✅ Captured successful response for {fixture_name}")

            except json.JSONDecodeError as e:
                click.echo(f"Error: Command output is not valid JSON: {e}", err=True)
                click.echo(f"Output was: {result.stdout[:500]}...", err=True)
                sys.exit(1)

        else:
            # Handle error responses - especially useful for error fixtures
            if verbose:
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

                    if verbose:
                        click.echo(f"✅ Captured error response for {fixture_name}")

                except json.JSONDecodeError:
                    # Create a generic error structure
                    error_data = {
                        "error": result.stderr.strip() or result.stdout.strip() or "Command failed",
                        "exit_code": result.returncode,
                    }
                    existing_fixtures[fixture_name] = error_data

                    if verbose:
                        click.echo(f"✅ Captured generic error for {fixture_name}")
            else:
                click.echo(
                    "Error: Command failed but fixture name doesn't indicate error case", err=True
                )
                click.echo(f"Exit code: {result.returncode}", err=True)
                click.echo(f"Stderr: {result.stderr}", err=True)
                sys.exit(1)

        # Write the updated fixtures back to file
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

        click.echo(f"💾 Updated {fixture_file}")
        click.echo(f"📄 Saved CLI output to {output_file}")
        click.echo(f"📊 Total fixtures in {domain}: {len(existing_fixtures)}")

        if verbose:
            click.echo(f"🎉 GraphQL recording complete for {domain}.{fixture_name}")

    except subprocess.TimeoutExpired:
        click.echo("Error: Command timed out after 60 seconds", err=True)
        sys.exit(1)
    except KeyboardInterrupt:
        click.echo("\\n⏹️  Recording interrupted", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"Error executing command: {e}", err=True)
        sys.exit(1)
