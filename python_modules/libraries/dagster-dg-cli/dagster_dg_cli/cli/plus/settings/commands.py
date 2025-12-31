"""Commands for managing deployment settings in Dagster+."""

from pathlib import Path
from typing import Optional

import click
from dagster_dg_core.shared_options import dg_global_options
from dagster_dg_core.utils import DgClickCommand
from dagster_dg_core.utils.telemetry import cli_telemetry_wrapper
from dagster_shared.plus.config import DagsterPlusCliConfig

from dagster_dg_cli.utils.plus.gql_client import DagsterPlusGraphQLClient
from dagster_dg_cli.utils.plus.gql_mutations import get_deployment_settings, set_deployment_settings


def _get_organization_and_deployment(
    organization: Optional[str],
    deployment: Optional[str],
) -> tuple[str, str]:
    """Get organization and deployment from flags or config.

    Args:
        organization: Organization from CLI flag (optional)
        deployment: Deployment from CLI flag (optional)

    Returns:
        Tuple of (organization, deployment)

    Raises:
        click.UsageError: If organization or deployment not found
    """
    # Check if config exists before trying to read it
    if not DagsterPlusCliConfig.exists():
        raise click.UsageError("Authentication required. Run 'dg plus login' to authenticate.")

    config = DagsterPlusCliConfig.get()

    org = organization or config.organization
    if not org or not org.strip():
        raise click.UsageError(
            "Organization not specified. Use --organization or run 'dg plus login'."
        )

    deploy = deployment or config.default_deployment
    if not deploy or not deploy.strip():
        raise click.UsageError(
            "Deployment not specified. Use --deployment or set a default with 'dg plus login'."
        )

    return org, deploy


@click.command(name="get", cls=DgClickCommand)
@click.option(
    "--organization",
    help="Dagster+ organization name. If not set, defaults to the value set by `dg plus login`.",
    envvar="DAGSTER_CLOUD_ORGANIZATION",
)
@click.option(
    "--deployment",
    help="Dagster+ deployment name. If not set, defaults to the default deployment set by `dg plus login`.",
    envvar="DAGSTER_CLOUD_DEPLOYMENT",
)
@dg_global_options
@cli_telemetry_wrapper
def get_command(
    organization: Optional[str],
    deployment: Optional[str],
    **global_options: object,
) -> None:
    """Retrieve and display current deployment settings in YAML format.

    Settings control deployment behavior including auto-materialization,
    run monitoring, retries, and more.

    Examples:
        # Get settings from default deployment
        $ dg plus settings get

        # Get settings from specific deployment
        $ dg plus settings get --deployment prod

        # Get settings from specific organization
        $ dg plus settings get --organization myorg --deployment staging
    """
    # Lazy import to avoid loading expensive yaml module during CLI initialization.
    # See: dagster_dg_cli_tests/cli_tests/import_perf_tests/test_import_perf.py
    import yaml

    # Get organization and deployment
    _get_organization_and_deployment(organization, deployment)

    # Create GraphQL client
    config = DagsterPlusCliConfig.get()
    client = DagsterPlusGraphQLClient.from_config(config)

    # Get settings
    click.echo("Retrieving deployment settings...")
    settings = get_deployment_settings(client)

    # Display as YAML
    yaml_output = yaml.dump(settings, default_flow_style=False, sort_keys=False)
    click.echo(yaml_output)


@click.command(name="set-from-file", cls=DgClickCommand)
@click.argument(
    "settings_file",
    type=click.Path(exists=True, readable=True, path_type=Path),
)
@click.option(
    "--organization",
    help="Dagster+ organization name. If not set, defaults to the value set by `dg plus login`.",
    envvar="DAGSTER_CLOUD_ORGANIZATION",
)
@click.option(
    "--deployment",
    help="Dagster+ deployment name. If not set, defaults to the default deployment set by `dg plus login`.",
    envvar="DAGSTER_CLOUD_DEPLOYMENT",
)
@dg_global_options
@cli_telemetry_wrapper
def set_from_file_command(
    settings_file: Path,
    organization: Optional[str],
    deployment: Optional[str],
    **global_options: object,
) -> None:
    """Set deployment settings from a YAML file.

    The YAML file should contain the settings structure directly.
    All settings in the file will be applied to the deployment.

    Examples:
        # Set all settings from file
        $ dg plus settings set-from-file my_settings.yaml

        # Set for specific deployment
        $ dg plus settings set-from-file settings.yaml --deployment staging

        # Example YAML file structure:
        # auto_materialize:
        #   enabled: true
        #   minimum_interval_seconds: 30
        # run_monitoring:
        #   enabled: true
        #   start_timeout_seconds: 180
    """
    # Lazy import to avoid loading expensive yaml module during CLI initialization.
    # See: dagster_dg_cli_tests/cli_tests/import_perf_tests/test_import_perf.py
    import yaml

    # Get organization and deployment
    _get_organization_and_deployment(organization, deployment)

    # Read and parse YAML file
    click.echo(f"Reading settings from {settings_file}...")
    with open(settings_file, encoding="utf-8") as f:
        settings = yaml.safe_load(f) or {}

    # Create GraphQL client
    config = DagsterPlusCliConfig.get()
    client = DagsterPlusGraphQLClient.from_config(config)

    # Set settings
    click.echo("Applying settings to deployment...")
    set_deployment_settings(client, settings)

    click.echo("✓ Deployment settings updated successfully")


def _parse_setting_flag(flag_name: str, value: str) -> tuple[list[str], str | bool | int | float]:
    """Parse a setting flag name into path components and convert value.

    Args:
        flag_name: Flag name (e.g., "auto_materialize_enabled")
        value: String value from CLI

    Returns:
        Tuple of (path_components, converted_value)
        Example: ("auto_materialize_enabled", "true") -> (["auto_materialize", "enabled"], True)
    """
    # Define known multi-word setting categories (number of underscore-separated segments)
    MULTI_WORD_CATEGORIES = {
        "auto_materialize": 2,
        "run_monitoring": 2,
        "run_retries": 2,
    }

    # Split flag name by underscores
    segments = flag_name.split("_")

    # Try to match against known multi-word categories
    category = None
    remaining_segments = []

    for cat, num_segments in MULTI_WORD_CATEGORIES.items():
        if len(segments) >= num_segments:
            potential_category = "_".join(segments[:num_segments])
            if potential_category == cat:
                category = cat
                remaining_segments = segments[num_segments:]
                break

    # If no multi-word category matched, assume first segment is the category
    if category is None:
        category = segments[0]
        remaining_segments = segments[1:]

    # Build path components: [category, field_name]
    # Field name is the remaining segments joined with underscores
    if remaining_segments:
        field_name = "_".join(remaining_segments)
        components = [category, field_name]
    else:
        # Shouldn't happen with proper flag names, but handle gracefully
        components = [category]

    # Convert string values to appropriate types
    converted_value: str | bool | int | float
    if value.lower() in ("true", "false"):
        converted_value = value.lower() == "true"
    elif value.isdigit():
        converted_value = int(value)
    else:
        try:
            converted_value = float(value)
        except ValueError:
            converted_value = value

    return components, converted_value


def _build_settings_dict(flat_settings: dict[str, object]) -> dict:
    """Build nested settings dictionary from flat flag names.

    Args:
        flat_settings: Dictionary of flat flag names to values
                      Example: {"auto_materialize_enabled": "true"}

    Returns:
        Nested settings dictionary
        Example: {"auto_materialize": {"enabled": True}}
    """
    result = {}

    for flag_name, value in flat_settings.items():
        # Value comes from Click options, which are always strings
        components, converted_value = _parse_setting_flag(flag_name, str(value))

        # Build nested structure
        current = result
        for component in components[:-1]:
            if component not in current:
                current[component] = {}
            current = current[component]

        # Set the value at the leaf
        current[components[-1]] = converted_value

    return result


@click.command(name="set", cls=DgClickCommand)
@click.option(
    "--auto-materialize-enabled",
    help="Enable or disable auto-materialization (true/false).",
)
@click.option(
    "--auto-materialize-minimum-interval",
    help="Minimum interval between auto-materialization ticks (seconds).",
)
@click.option(
    "--auto-materialize-respect-materialization-data-versions",
    help="Respect materialization data versions (true/false).",
)
@click.option(
    "--auto-materialize-max-tick-retries",
    help="Maximum number of tick retry attempts.",
)
@click.option(
    "--auto-materialize-use-sensors",
    help="Use sensors for auto-materialization execution (true/false).",
)
@click.option(
    "--run-monitoring-enabled",
    help="Enable or disable run monitoring (true/false).",
)
@click.option(
    "--run-monitoring-start-timeout",
    help="Run startup timeout in seconds.",
)
@click.option(
    "--run-monitoring-cancel-timeout",
    help="Run cancellation timeout in seconds.",
)
@click.option(
    "--run-monitoring-max-runtime",
    help="Maximum run time in seconds (0 for unlimited).",
)
@click.option(
    "--run-monitoring-poll-interval",
    help="Run monitoring poll interval in seconds.",
)
@click.option(
    "--run-retries-enabled",
    help="Enable or disable run retries (true/false).",
)
@click.option(
    "--run-retries-max-retries",
    help="Maximum number of run retry attempts.",
)
@click.option(
    "--run-retries-retry-on-asset-or-op-failure",
    help="Retry on asset or op failure (true/false).",
)
@click.option(
    "--telemetry-enabled",
    help="Enable or disable telemetry (true/false).",
)
@click.option(
    "--freshness-enabled",
    help="Enable or disable freshness checks (true/false).",
)
@click.option(
    "--organization",
    help="Dagster+ organization name. If not set, defaults to the value set by `dg plus login`.",
    envvar="DAGSTER_CLOUD_ORGANIZATION",
)
@click.option(
    "--deployment",
    help="Dagster+ deployment name. If not set, defaults to the default deployment set by `dg plus login`.",
    envvar="DAGSTER_CLOUD_DEPLOYMENT",
)
@dg_global_options
@cli_telemetry_wrapper
def set_command(
    organization: Optional[str],
    deployment: Optional[str],
    **kwargs: object,
) -> None:
    r"""Set individual deployment settings via command-line flags.

    This command allows you to set specific settings without needing
    to create a YAML file. Multiple settings can be set in a single command.

    Examples:
        # Enable auto-materialization
        $ dg plus settings set --auto-materialize-enabled true

        # Configure run monitoring
        $ dg plus settings set \
            --run-monitoring-enabled true \
            --run-monitoring-start-timeout 300

        # Set multiple settings at once
        $ dg plus settings set \
            --auto-materialize-enabled true \
            --auto-materialize-minimum-interval 60 \
            --run-retries-enabled true \
            --run-retries-max-retries 3

        # Set for specific deployment
        $ dg plus settings set --telemetry-enabled false --deployment prod
    """
    # Lazy import to avoid loading expensive yaml module during CLI initialization.
    # See: dagster_dg_cli_tests/cli_tests/import_perf_tests/test_import_perf.py
    import yaml

    # Get organization and deployment
    _get_organization_and_deployment(organization, deployment)

    # Filter out None values and non-setting flags (including global options)
    excluded_keys = ("organization", "deployment", "verbose", "use_component_modules")
    flat_settings = {
        key.replace("-", "_"): value
        for key, value in kwargs.items()
        if value is not None and key not in excluded_keys
    }

    if not flat_settings:
        raise click.UsageError(
            "No settings provided. Specify at least one setting flag. "
            "Use 'dg plus settings set --help' to see available options."
        )

    # Build nested settings structure
    settings = _build_settings_dict(flat_settings)

    # Create GraphQL client
    config = DagsterPlusCliConfig.get()
    client = DagsterPlusGraphQLClient.from_config(config)

    # Display what will be set
    click.echo("Applying the following settings:")
    yaml_output = yaml.dump(settings, default_flow_style=False, sort_keys=False)
    click.echo(yaml_output)

    # Set settings
    set_deployment_settings(client, settings)

    click.echo("✓ Deployment settings updated successfully")
