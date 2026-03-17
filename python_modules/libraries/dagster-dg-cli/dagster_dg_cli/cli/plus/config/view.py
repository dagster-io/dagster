import click
from dagster_dg_core.utils import DgClickCommand
from dagster_dg_core.utils.telemetry import cli_telemetry_wrapper
from dagster_shared.plus.config import (
    DagsterPlusCliConfig,
    _get_dagster_plus_config_path_and_raw_config,
)


def _censor_token(token: str) -> str:
    if len(token) <= 6:
        return "***"
    return ("*" * (len(token) - 6)) + token[-6:]


@click.command(name="view", cls=DgClickCommand)
@click.option(
    "--show-token",
    "-s",
    is_flag=True,
    default=False,
    help="Show the full user token instead of a censored version.",
)
@cli_telemetry_wrapper
def config_view_command(show_token: bool) -> None:
    """View the current Dagster Plus CLI configuration."""
    config_info = _get_dagster_plus_config_path_and_raw_config()
    if config_info is None:
        click.echo("No Dagster Plus configuration found.")
        click.echo("Run `dg plus login` to set up your configuration.")
        raise SystemExit(1)

    config = DagsterPlusCliConfig.get()
    config_path = config_info.path

    output: dict[str, object] = {}
    if config.organization is not None:
        output["organization"] = config.organization
    if config.default_deployment is not None:
        output["default_deployment"] = config.default_deployment
    if config.user_token is not None:
        output["user_token"] = config.user_token if show_token else _censor_token(config.user_token)
    if config.url is not None:
        output["url"] = config.url
    if config.agent_timeout is not None:
        output["agent_timeout"] = config.agent_timeout

    click.echo(f"Config file: {config_path}\n")
    if output:
        import yaml

        click.echo(yaml.dump(output, default_flow_style=False), nl=False)
    else:
        click.echo("Configuration is empty.")
