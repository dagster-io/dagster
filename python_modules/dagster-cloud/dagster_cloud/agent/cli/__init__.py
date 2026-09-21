import json
import logging
import logging.config
import os
from collections.abc import Mapping
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import cast

import dagster._check as check
import yaml
from dagster._core.errors import DagsterHomeNotSetError
from dagster._utils.interrupts import capture_interrupts
from dagster._utils.log import default_date_format_string, default_format_string
from dagster._utils.merger import deep_merge_dicts
from dagster_cloud_cli import ui
from dagster_shared.yaml_utils import load_yaml_from_globs
from typer import Argument, Option, Typer

from dagster_cloud.agent.dagster_cloud_agent import DagsterCloudAgent
from dagster_cloud.instance import DagsterCloudAgentInstance

app = Typer(help="Interact with the Dagster Cloud agent.")


def agent_home_exception():
    dagster_home_loc = (
        f"No Dagster config provided in specified directory {os.getenv('DAGSTER_HOME')}. "
        "You must specify the location of a directory containing a dagster.yaml "
        "file as a parameter or by setting the DAGSTER_HOME environment variable."
        if os.getenv("DAGSTER_HOME")
        else (
            "No directory provided or DAGSTER_CLOUD environment variable set. "
            "You must supply the location of a directory containing a dagster.yaml "
            "file as a parameter or by setting the DAGSTER_HOME environment variable."
        )
    )
    return ui.error(f"No Dagster config found.\n\n{dagster_home_loc}")


def run_local_agent(agent_logging_config: Mapping[str, object] | None) -> None:
    try:
        with DagsterCloudAgentInstance.get() as inst:
            instance = check.inst(inst, DagsterCloudAgentInstance)

            logging.basicConfig(
                level=logging.INFO,
                format=default_format_string(),
                datefmt=default_date_format_string(),
                handlers=[logging.StreamHandler()],
            )

            if agent_logging_config:
                logging.config.dictConfig(
                    {
                        "version": 1,
                        "disable_existing_loggers": False,
                        **agent_logging_config,
                    }
                )

            user_code_launcher = instance.user_code_launcher
            user_code_launcher.start()

            with DagsterCloudAgent(instance) as agent:
                agent.run_loop(user_code_launcher, agent_uuid=instance.instance_uuid)
    except DagsterHomeNotSetError:
        raise agent_home_exception()


def run_local_agent_in_environment(
    dagster_home: Path | None, agent_logging_config: Mapping[str, object] | None
):
    with capture_interrupts():
        old_env = None
        try:
            old_env = dict(os.environ)
            if dagster_home:
                os.environ["DAGSTER_HOME"] = str(dagster_home.resolve())
            run_local_agent(agent_logging_config)
        finally:
            os.environ.clear()
            if old_env is not None:
                os.environ.update(old_env)


def run_local_agent_in_temp_environment(
    agent_token: str,
    deployment: str,
    agent_label: str | None,
    instance_config: str | None,
    user_code_launcher_module: str | None,
    user_code_launcher_class: str | None,
    user_code_launcher_config: str | None,
    agent_logging_config: Mapping[str, object] | None,
):
    config = {
        "instance_class": {
            "module": "dagster_cloud.instance",
            "class": "DagsterCloudAgentInstance",
        },
        "dagster_cloud_api": {},
        "user_code_launcher": {
            "module": "dagster_cloud.workspace.user_code_launcher",
            "class": "ProcessUserCodeLauncher",
        },
    }
    if instance_config:
        parsed = json.loads(instance_config)
        config = deep_merge_dicts(config, parsed)

    if agent_token:
        config["dagster_cloud_api"]["agent_token"] = agent_token
    if deployment:
        config["dagster_cloud_api"]["deployment"] = deployment
    if agent_label:
        config["dagster_cloud_api"]["agent_label"] = agent_label
    if user_code_launcher_module:
        config["user_code_launcher"]["module"] = user_code_launcher_module
    if user_code_launcher_class:
        config["user_code_launcher"]["class"] = user_code_launcher_class
    if user_code_launcher_config:
        try:
            config["user_code_launcher"]["config"] = json.loads(user_code_launcher_config)
        except json.JSONDecodeError as e:
            raise ui.error(f"Invalid User Code Launcher config JSON:\n{e}")

    with TemporaryDirectory() as d:
        with open(os.path.join(d, "dagster.yaml"), "w", encoding="utf8") as f:
            f.write(yaml.dump(config))
        run_local_agent_in_environment(Path(d), agent_logging_config)


@app.command(
    help=(
        "Runs the Dagster Cloud agent. The agent can either be run ephemerally by specifying an"
        " agent token and deployment name as CLI options, or the agent can pull its config from a"
        " dagster.yaml file. To use a dagster.yaml file, either pass a directory containing the"
        " file as a CLI argument or set the DAGSTER_HOME environment variable."
    ),
    short_help="Run the Dagster Cloud agent.",
)
def run(
    dagster_home: Path | None = Argument(None),
    agent_token: str = Option(
        None, "--agent-token", "-a", help="Agent token, if running ephemerally."
    ),
    deployment: str = Option(
        None, "--deployment", "-d", help="Deployment, if running ephemerally."
    ),
    agent_label: str = Option(
        None, "--agent-label", "-l", help="Optional agent label, if running ephemerally."
    ),
    user_code_launcher: str = Option(
        None,
        "--user-code-launcher",
        help="User Code Launcher to use. Defaults to the local Process User Code Launcher.",
        hidden=True,
    ),
    instance_config: str = Option(
        None,
        "--config",
        help="Dagster instance config, in JSON format.",
    ),
    user_code_launcher_config: str = Option(
        None,
        "--user-code-launcher-config",
        help="Config to supply the User Code Launcher, in JSON format.",
        hidden=True,
    ),
    agent_logging_config_path: Path | None = Option(
        None,
        "--agent-logging-config-path",
        help=(
            "Yaml file with logging config for the agent process that can be passed into"
            " logging.dictConfig"
        ),
        exists=True,
    ),
    agent_logging_config_string: str | None = Option(
        None,
        "--agent-logging-config-string",
        help=(
            "inlined json with logging config for the agent process that can be passed into"
            " logging.dictConfig. Cannot be provided if --agent-logging-config-path is specified."
        ),
    ),
):
    if agent_logging_config_string and agent_logging_config_path:
        raise ui.error(
            "Only --agent-logging-config-path or --agent-logging-config-string can be specified, not both"
        )
    else:
        agent_logging_config = _get_agent_logging_config(
            agent_logging_config_path, agent_logging_config_string
        )
    if (
        agent_token
        or deployment
        or agent_label
        or instance_config
        or user_code_launcher_config
        or user_code_launcher
    ):
        if not instance_config and (not agent_token or not deployment):
            raise ui.error("To run ephemerally, must supply both an agent token and a deployment.")
        if dagster_home:
            raise ui.error("Cannot supply both a dagster home directory and ephemeral parameters.")

        if user_code_launcher:
            user_code_launcher_module = ""
            user_code_launcher_class = user_code_launcher
            if "." in user_code_launcher:
                user_code_launcher_module, user_code_launcher_class = user_code_launcher.rsplit(
                    ".", 1
                )
        else:
            user_code_launcher_module = None
            user_code_launcher_class = None

        run_local_agent_in_temp_environment(
            agent_token,
            deployment,
            agent_label,
            instance_config,
            user_code_launcher_module,
            user_code_launcher_class,
            user_code_launcher_config,
            agent_logging_config,
        )
    else:
        run_local_agent_in_environment(dagster_home, agent_logging_config)


def _get_agent_logging_config(
    agent_logging_config_path: Path | None,
    agent_logging_config_string: str | None,
) -> Mapping[str, object] | None:
    agent_logging_config: Mapping[str, object] | None = None
    if agent_logging_config_path:
        agent_logging_config = cast(
            "Mapping[str, object]",
            load_yaml_from_globs(str(agent_logging_config_path)),
        )
    elif agent_logging_config_string:
        agent_logging_config = json.loads(agent_logging_config_string)
    return agent_logging_config
