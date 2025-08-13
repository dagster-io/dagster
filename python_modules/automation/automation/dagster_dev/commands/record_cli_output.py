"""Record CLI output using existing GraphQL fixtures (Step 2 of two-step recording).

This command uses existing GraphQL response fixtures to mock the API client,
then executes CLI commands to capture their output as snapshots.
"""

import json
import subprocess
import sys
from pathlib import Path

import click


@click.command(name="dg-api-record-cli-output")
@click.argument("domain", required=True)
@click.argument("fixture_name", required=True)
@click.option("--verbose", "-v", is_flag=True, help="Verbose output")
def record_cli_output(domain: str, fixture_name: str, verbose: bool):
    """Record CLI output using existing GraphQL fixtures.

    Uses the specified fixture to mock GraphQL responses, then runs the corresponding
    CLI command to capture its output as snapshots via pytest --snapshot-update.

    Args:
        domain: API domain (e.g., 'deployment', 'run', 'asset')
        fixture_name: Name of the fixture to use (e.g., 'success_multiple_deployments')

    Examples:
        dagster-dev dg-api-record-cli-output deployment success_multiple_deployments
        dagster-dev dg-api-record-cli-output run error_not_found
    """
    # Determine the test directory location
    api_tests_dir = (
        Path.cwd()
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
        available_domains = [d.name.replace("_tests", "") for d in api_tests_dir.glob("*_tests")]
        click.echo(f"Available domains: {available_domains}")
        sys.exit(1)

    if not fixture_file.exists():
        click.echo(f"Error: Fixture file not found: {fixture_file}", err=True)
        click.echo("Run 'record-graphql' first to capture GraphQL responses.")
        sys.exit(1)

    # Load the fixture
    try:
        with open(fixture_file) as f:
            fixtures = json.load(f)
    except (OSError, json.JSONDecodeError) as e:
        click.echo(f"Error loading fixtures: {e}", err=True)
        sys.exit(1)

    if fixture_name not in fixtures:
        available = list(fixtures.keys())
        click.echo(f"Error: Fixture '{fixture_name}' not found", err=True)
        click.echo(f"Available fixtures: {available}")
        sys.exit(1)

    if verbose:
        click.echo(f"📁 Domain: {domain}")
        click.echo(f"🎯 Fixture: {fixture_name}")
        click.echo(f"📂 Test directory: {domain_tests_dir}")

    try:
        # Run pytest with snapshot update for the specific domain tests
        pytest_command = [
            "python",
            "-m",
            "pytest",
            str(domain_tests_dir),
            "--snapshot-update",
            "-v" if verbose else "-q",
        ]

        if verbose:
            click.echo(f"🧪 Running: {' '.join(pytest_command)}")

        # Change to the correct directory for pytest to find the tests
        original_cwd = Path.cwd()

        try:
            # Run pytest from the repo root so imports work correctly
            result = subprocess.run(
                pytest_command,
                cwd=original_cwd,
                capture_output=not verbose,  # Show output if verbose
                text=True,
                check=False,
            )

            if result.returncode == 0:
                click.echo(f"✅ Successfully updated CLI output snapshots for {domain}")
                if verbose and result.stdout:
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
                if verbose:
                    click.echo(
                        "Note: Snapshot files may still have been updated despite test issues."
                    )

        finally:
            # Always restore original directory
            pass

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

        if verbose:
            click.echo(f"🎉 CLI output recording complete for {domain}.{fixture_name}")

    except subprocess.TimeoutExpired:
        click.echo("Error: pytest timed out", err=True)
        sys.exit(1)
    except KeyboardInterrupt:
        click.echo("\\n⏹️  Recording interrupted", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"Error running pytest: {e}", err=True)
        sys.exit(1)
