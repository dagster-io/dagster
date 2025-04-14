# The following allows logging calls with extra arguments
# ruff: noqa: PLE1205
import importlib.util
import json
import logging
import time
from collections.abc import Mapping
from enum import Enum
from typing import Callable, Optional

import typer
from typer.models import CommandInfo

from dagster_cloud_cli.utils import create_stub_app

from .commands.branch_deployment import app as branch_deployment_app
from .commands.ci import app as ci_app
from .commands.config import (
    app as config_app,
    app_configure as configure_app,
)
from .commands.deployment import app as deployment_app
from .commands.job import app as job_app
from .commands.organization import (
    app as organization_app,
    legacy_settings_app,
)
from .commands.run import app as run_app
from .commands.serverless import app as serverless_app
from .commands.workspace import app as workspace_app
from .version import __version__

has_dagster_cloud = importlib.util.find_spec("dagster_cloud") is not None


if has_dagster_cloud:
    from dagster_cloud.agent.cli import app as agent_app
    from dagster_cloud.pex.grpc.server.cli import app as pex_app
else:
    agent_app = create_stub_app("dagster-cloud")
    pex_app = create_stub_app("dagster-cloud")


def _import_commands(
    parent: typer.Typer,
    child: typer.Typer,
    remap_fn: Optional[Callable[[CommandInfo], CommandInfo]] = None,
) -> None:
    """Copies the commands from one Typer app to another.
    Equivalent of `add_typer` but doesn't add a subcommand.
    """
    for raw_command in child.registered_commands:
        command = remap_fn(raw_command) if remap_fn else raw_command
        parent.registered_commands.append(command)


def _rename_command(command_info: CommandInfo, name: str) -> CommandInfo:
    return CommandInfo(
        name=name,
        cls=command_info.cls,
        context_settings=command_info.context_settings,
        callback=command_info.callback,
        help=command_info.help,
        epilog=command_info.epilog,
        short_help=command_info.short_help,
        options_metavar=command_info.options_metavar,
        add_help_option=command_info.add_help_option,
        no_args_is_help=command_info.no_args_is_help,
        hidden=command_info.hidden,
        deprecated=command_info.deprecated,
        # This avoids an error if a user is using an older version of Typer, since
        # `rich_help_panel` was added in typer==0.6.0.
        **(
            {"rich_help_panel": getattr(command_info, "rich_help_panel")}
            if hasattr(command_info, "rich_help_panel")
            else {}
        ),
    )


app = typer.Typer(
    help="CLI tools for working with Dagster Cloud.",
    no_args_is_help=True,
    context_settings={
        "help_option_names": ["-h", "--help"],
    },
    pretty_exceptions_enable=False,  # don't display overly verbose stack traces
)


def version_callback(value: bool):
    if value:
        typer.echo(f"Dagster Cloud version: {__version__}")
        raise typer.Exit()


class LogFormat(Enum):
    DEFAULT = "default"
    FLUENTBIT = "fluentbit"


class FluentbitJsonFormatter(logging.Formatter):
    def __init__(self, fmt: str, json_fields: Mapping[str, str]):
        super().__init__(fmt=fmt)
        self.json_fields = dict(json_fields)

    def format(self, record: logging.LogRecord) -> str:
        log = super().format(record)
        output = {
            # Time format specified here: https://github.com/fluent/fluent-bit/blob/master/conf/parsers.conf#L35-L39
            "time": time.strftime("%d/%b/%Y:%H:%M:%S %z", time.localtime(record.created)),
            "log": log,
            "status": record.levelname,
            "logger": record.name,
        }

        if isinstance(record.args, dict):
            for source_field, target_field in self.json_fields.items():
                if source_field in record.args:
                    output[target_field] = str(record.args[source_field])

        return json.dumps(output)


def log_format_callback(value: LogFormat):
    if value == LogFormat.FLUENTBIT:
        logger = logging.getLogger()
        for handler in logger.handlers[:]:
            logger.removeHandler(handler)
        logger.setLevel(logging.INFO)
        handler = logging.StreamHandler()
        handler.setFormatter(
            FluentbitJsonFormatter(
                "%(module)s - %(message)s",
                {"event_name": "event_name", "duration_seconds": "duration_seconds"},
            )
        )
        logger.addHandler(handler)


@app.callback()
def main(
    _version: bool = typer.Option(
        False,
        "--version",
        "-v",
        callback=version_callback,
        is_eager=True,
        show_default=False,
        help="Show Dagster Cloud version.",
    ),
    log_format: LogFormat = typer.Option(
        "default",
        "--log-format",
        envvar="DAGSTER_LOG_FORMAT",
        callback=log_format_callback,
        is_eager=True,
        show_default=True,
        help="Logging level and format",
    ),
):
    return


@app.command(hidden=True)
def logtest() -> None:
    logging.info("this is an info message")
    logging.error("this is an error message")
    logging.warning("this is a warning message")
    try:
        print(1 / 0)
    except:
        logging.exception("this is inside an exception")
    logger = logging.getLogger("cloud-events")
    logger.info(
        "logger info message with some tags", {"event_name": "event.NAME", "duration_seconds": 0.11}
    )
    logger.error(
        "logger error message with some tags",
        {"event_name": "event.NAME", "duration_seconds": 0.11},
    )


app.add_typer(agent_app, name="agent", no_args_is_help=True)
app.add_typer(config_app, name="config", no_args_is_help=True)
app.add_typer(deployment_app, name="deployment", no_args_is_help=True)
app.add_typer(organization_app, name="organization", no_args_is_help=True)
app.add_typer(workspace_app, name="workspace", no_args_is_help=True, hidden=True)
_import_commands(
    deployment_app,
    workspace_app,
    remap_fn=lambda c: (
        _rename_command(c, f"{c.name}-locations") if c.name and "location" not in c.name else c
    ),
)
app.add_typer(branch_deployment_app, name="branch-deployment", no_args_is_help=True)
app.add_typer(job_app, name="job", no_args_is_help=True)
app.add_typer(run_app, name="run", no_args_is_help=True, hidden=True)
app.add_typer(serverless_app, name="serverless", no_args_is_help=True)
app.add_typer(pex_app, name="pex", hidden=True, no_args_is_help=True)
app.add_typer(ci_app, name="ci", no_args_is_help=True)

# Deprecated in favor of organization
app.add_typer(legacy_settings_app, name="settings", hidden=True)

_import_commands(app, configure_app)

if __name__ == "__main__":
    app()
