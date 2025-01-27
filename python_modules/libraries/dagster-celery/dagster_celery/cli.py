import os
import subprocess
import uuid
from collections.abc import Mapping
from typing import Any, Optional

import click
import dagster._check as check
from celery.utils.nodenames import default_nodename, host_format
from dagster._config import post_process_config, validate_config
from dagster._core.errors import DagsterInvalidConfigError
from dagster._core.instance import DagsterInstance
from dagster._utils import mkdir_p
from dagster._utils.yaml_utils import load_yaml_from_path

from dagster_celery.executor import CeleryExecutor, celery_executor
from dagster_celery.make_app import make_app


def create_worker_cli_group():
    group = click.Group(name="worker")
    group.add_command(worker_start_command)
    group.add_command(worker_terminate_command)
    group.add_command(worker_list_command)
    return group


def get_config_value_from_yaml(yaml_path: Optional[str]) -> Mapping[str, Any]:
    if yaml_path is None:
        return {}
    parsed_yaml = load_yaml_from_path(yaml_path) or {}
    assert isinstance(parsed_yaml, dict)
    # Would be better not to hardcode this path
    return (
        parsed_yaml.get("execution", {}).get("config", {})
        or parsed_yaml.get("execution", {}).get("celery", {})  # legacy config
        or {}
    )


def get_app(config_yaml: Optional[str] = None) -> CeleryExecutor:
    return make_app(
        CeleryExecutor.for_cli(**get_config_value_from_yaml(config_yaml)).app_args()
        if config_yaml
        else CeleryExecutor.for_cli().app_args()
    )


def get_worker_name(name: Optional[str] = None) -> str:
    return name + "@%h" if name is not None else f"dagster-{str(uuid.uuid4())[-6:]}@%h"


def get_validated_config(config_yaml: Optional[str] = None) -> Any:
    config_type = celery_executor.config_schema.config_type
    config_value = get_config_value_from_yaml(config_yaml)
    config = validate_config(config_type, config_value)
    if not config.success:
        raise DagsterInvalidConfigError(
            f"Errors while loading Celery executor config at {config_yaml}.",
            config.errors,
            config_value,
        )
    return post_process_config(config_type, config_value).value  # type: ignore  # (possible none)


def get_config_dir(config_yaml=None):
    instance = DagsterInstance.get()

    config_module_name = "dagster_celery_config"

    config_dir = os.path.join(
        instance.root_directory, "dagster_celery", "config", str(uuid.uuid4())
    )
    mkdir_p(config_dir)
    config_path = os.path.join(config_dir, f"{config_module_name}.py")

    validated_config = get_validated_config(config_yaml)
    with open(config_path, "w", encoding="utf8") as fd:
        if validated_config.get("broker"):
            fd.write(
                "broker_url = '{broker_url}'\n".format(broker_url=str(validated_config["broker"]))
            )
        if validated_config.get("backend"):
            fd.write(
                "result_backend = '{result_backend}'\n".format(
                    result_backend=str(validated_config["backend"])
                )
            )
        if validated_config.get("config_source"):
            for key, value in validated_config["config_source"].items():
                fd.write(f"{key} = {value!r}\n")

    # n.b. right now we don't attempt to clean up this cache, but it might make sense to delete
    # any files older than some time if there are more than some number of files present, etc.
    return config_dir


def launch_background_worker(subprocess_args, env):
    return subprocess.Popen(
        subprocess_args + ["--detach", "--pidfile="], stdout=None, stderr=None, env=env
    )


@click.command(name="start", help="Start a dagster celery worker.")
@click.option(
    "--name",
    "-n",
    type=click.STRING,
    default=None,
    help=(
        'The name of the worker. Defaults to a unique name prefixed with "dagster-" and ending '
        "with the hostname."
    ),
)
@click.option(
    "--config-yaml",
    "-y",
    type=click.Path(exists=True),
    default=None,
    help=(
        "Specify the path to a config YAML file with options for the worker. This is the same "
        "config block that you provide to dagster_celery.celery_executor when configuring a "
        "job for execution with Celery, with, e.g., the URL of the broker to use."
    ),
)
@click.option(
    "--queue",
    "-q",
    type=click.STRING,
    multiple=True,
    help=(
        "Names of the queues on which this worker should listen for tasks.  Provide multiple -q "
        "arguments to specify multiple queues. Note that each celery worker may listen on no more "
        "than four queues."
    ),
)
@click.option(
    "--background", "-d", is_flag=True, help="Set this flag to run the worker in the background."
)
@click.option(
    "--includes",
    "-i",
    type=click.STRING,
    multiple=True,
    help=(
        "Python modules the worker should import. Provide multiple -i arguments to specify "
        "multiple modules."
    ),
)
@click.option(
    "--loglevel", "-l", type=click.STRING, default="INFO", help="Log level for the worker."
)
@click.option("--app", "-A", type=click.STRING)
@click.argument("additional_args", nargs=-1, type=click.UNPROCESSED)
def worker_start_command(
    name,
    config_yaml,
    background,
    queue,
    includes,
    loglevel,
    app,
    additional_args,
):
    check.invariant(app, "App must be specified. E.g. dagster_celery.app or dagster_celery_k8s.app")

    loglevel_args = ["--loglevel", loglevel]

    if len(queue) > 4:
        check.failed(
            "Can't start a dagster_celery worker that listens on more than four queues, due to a "
            "bug in Celery 4."
        )
    queue_args = []
    for q in queue:
        queue_args += ["-Q", q]

    includes_args = ["-I", ",".join(includes)] if includes else []

    pythonpath = get_config_dir(config_yaml)
    subprocess_args = (
        ["celery", "-A", app, "worker", "--prefetch-multiplier=1"]
        + loglevel_args
        + queue_args
        + includes_args
        + ["-n", get_worker_name(name)]
        + list(additional_args)
    )

    env = os.environ.copy()
    if pythonpath is not None:
        existing_pythonpath = env.get("PYTHONPATH", "")
        if existing_pythonpath and not existing_pythonpath.endswith(os.pathsep):
            existing_pythonpath += os.pathsep
        env["PYTHONPATH"] = f"{existing_pythonpath}{pythonpath}{os.pathsep}"
    if background:
        launch_background_worker(subprocess_args, env=env)
    else:
        return subprocess.check_call(subprocess_args, env=env)


@click.command(name="status", help="wrapper around `celery status`")
@click.option(
    "--config-yaml",
    "-y",
    type=click.Path(exists=True),
    required=True,
    help=(
        "Specify the path to a config YAML file with options for the worker. This is the same "
        "config block that you provide to dagster_celery.celery_executor when configuring a "
        "job for execution with Celery, with, e.g., the URL of the broker to use."
    ),
)
@click.option("--app", "-A", type=click.STRING)
@click.argument("additional_args", nargs=-1, type=click.UNPROCESSED)
def status_command(
    config_yaml,
    app,
    additional_args,
):
    check.invariant(app, "App must be specified. E.g. dagster_celery.app or dagster_celery_k8s.app")

    config = get_validated_config(config_yaml)
    subprocess_args = ["celery", "-A", app, "-b", str(config["broker"]), "status"] + list(
        additional_args
    )

    subprocess.check_call(subprocess_args)


@click.command(
    name="list",
    help="List running dagster-celery workers. Note that we use the broker to contact the workers.",
)
@click.option(
    "--config-yaml",
    "-y",
    type=click.Path(exists=True),
    default=None,
    help=(
        "Specify the path to a config YAML file with options for the workers you are trying to "
        "manage. This is the same config block that you provide to dagster_celery.celery_executor "
        "when configuring a job for execution with Celery, with, e.g., the URL of the broker "
        "to use. Without this config file, you will not be able to find your workers (since the "
        "CLI won't know how to reach the broker)."
    ),
)
def worker_list_command(config_yaml=None):
    app = get_app(config_yaml)

    print(app.control.inspect(timeout=1).active())  # noqa: T201  # pyright: ignore[reportAttributeAccessIssue]


@click.command(
    name="terminate",
    help=(
        "Shut down dagster-celery workers. Note that we use the broker to send signals to the "
        "workers to terminate -- if the broker is not running, this command is a no-op. "
        "Provide the argument NAME to terminate a specific worker by name."
    ),
)
@click.argument("name", default="dagster")
@click.option(
    "--all", "-a", "all_", is_flag=True, help="Set this flag to terminate all running workers."
)
@click.option(
    "--config-yaml",
    "-y",
    type=click.Path(exists=True),
    default=None,
    help=(
        "Specify the path to a config YAML file with options for the workers you are trying to "
        "manage. This is the same config block that you provide to dagster_celery.celery_executor "
        "when configuring a job for execution with Celery, with, e.g., the URL of the broker "
        "to use. Without this config file, you will not be able to terminate your workers (since "
        "the CLI won't know how to reach the broker)."
    ),
)
def worker_terminate_command(name="dagster", config_yaml=None, all_=False):
    app = get_app(config_yaml)

    if all_:
        app.control.broadcast("shutdown")  # pyright: ignore[reportAttributeAccessIssue]
    else:
        app.control.broadcast(  # pyright: ignore[reportAttributeAccessIssue]
            "shutdown", destination=[host_format(default_nodename(get_worker_name(name)))]
        )


worker_cli = create_worker_cli_group()


@click.group(commands={"worker": worker_cli, "status": status_command})
def main():
    """dagster-celery."""


if __name__ == "__main__":
    # pylint doesn't understand click
    main()
