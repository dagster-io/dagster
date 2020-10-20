import os
import subprocess
import uuid

import click
from celery.utils.nodenames import default_nodename, host_format
from dagster import check
from dagster.config.post_process import post_process_config
from dagster.config.validate import validate_config
from dagster.core.errors import DagsterInvalidConfigError
from dagster.core.instance import DagsterInstance
from dagster.utils import load_yaml_from_path, mkdir_p

from .executor import CeleryExecutor, celery_executor
from .make_app import make_app


def create_worker_cli_group():
    group = click.Group(name="worker")
    group.add_command(worker_start_command)
    group.add_command(worker_terminate_command)
    group.add_command(worker_list_command)
    return group


def get_config_value_from_yaml(yaml_path):
    if yaml_path is None:
        return {}
    parsed_yaml = load_yaml_from_path(yaml_path) or {}
    # Would be better not to hardcode this path
    return parsed_yaml.get("execution", {}).get("celery", {}) or {}


def get_app(config_yaml=None):
    return make_app(
        CeleryExecutor.for_cli(**get_config_value_from_yaml(config_yaml)).app_args()
        if config_yaml
        else CeleryExecutor.for_cli().app_args()
    )


def get_worker_name(name=None):
    return (
        name + "@%h"
        if name is not None
        else "dagster-{uniq}@%h".format(uniq=str(uuid.uuid4())[-6:])
    )


def get_config_dir(config_yaml=None):
    instance = DagsterInstance.get()
    config_type = celery_executor.config_schema.config_type
    config_value = get_config_value_from_yaml(config_yaml)

    config_module_name = "dagster_celery_config"

    config_dir = os.path.join(
        instance.root_directory, "dagster_celery", "config", str(uuid.uuid4())
    )
    mkdir_p(config_dir)
    config_path = os.path.join(
        config_dir, "{config_module_name}.py".format(config_module_name=config_module_name)
    )

    config = validate_config(config_type, config_value)
    if not config.success:
        raise DagsterInvalidConfigError(
            "Errors while loading Celery executor config at {}.".format(config_yaml),
            config.errors,
            config_value,
        )

    validated_config = post_process_config(config_type, config_value).value
    with open(config_path, "w") as fd:
        if "broker" in validated_config and validated_config["broker"]:
            fd.write(
                "broker_url = '{broker_url}'\n".format(broker_url=str(validated_config["broker"]))
            )
        if "backend" in validated_config and validated_config["backend"]:
            fd.write(
                "result_backend = '{result_backend}'\n".format(
                    result_backend=str(validated_config["backend"])
                )
            )
        if "config_source" in validated_config and validated_config["config_source"]:
            for key, value in validated_config["config_source"].items():
                fd.write("{key} = {value}\n".format(key=key, value=repr(value)))

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
        "pipeline for execution with Celery, with, e.g., the URL of the broker to use."
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
    name, config_yaml, background, queue, includes, loglevel, app, additional_args,
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
        env["PYTHONPATH"] = "{existing_pythonpath}:{pythonpath}:".format(
            existing_pythonpath=env.get("PYTHONPATH", ""), pythonpath=pythonpath
        )

    if background:
        launch_background_worker(subprocess_args, env=env)
    else:
        return subprocess.check_call(subprocess_args, env=env)


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
        "when configuring a pipeline for execution with Celery, with, e.g., the URL of the broker "
        "to use. Without this config file, you will not be able to find your workers (since the "
        "CLI won't know how to reach the broker)."
    ),
)
def worker_list_command(config_yaml=None):
    app = get_app(config_yaml)

    print(app.control.inspect(timeout=1).active())  # pylint: disable=print-call


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
        "when configuring a pipeline for execution with Celery, with, e.g., the URL of the broker "
        "to use. Without this config file, you will not be able to terminate your workers (since "
        "the CLI won't know how to reach the broker)."
    ),
)
def worker_terminate_command(name="dagster", config_yaml=None, all_=False):
    app = get_app(config_yaml)

    if all_:
        app.control.broadcast("shutdown")
    else:
        app.control.broadcast(
            "shutdown", destination=[host_format(default_nodename(get_worker_name(name)))]
        )


worker_cli = create_worker_cli_group()


@click.group(commands={"worker": worker_cli})
def main():
    """dagster-celery"""


if __name__ == "__main__":
    # pylint doesn't understand click
    main()  # pylint:disable=no-value-for-parameter
