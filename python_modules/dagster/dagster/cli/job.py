from typing import Dict

import click

import dagster._check as check
from dagster import __version__ as dagster_version
from dagster.cli.pipeline import (
    add_step_to_table,
    execute_backfill_command,
    execute_execute_command,
    execute_launch_command,
    execute_list_command,
    execute_print_command,
    execute_scaffold_command,
    get_run_config_from_file_list,
)
from dagster.cli.workspace.cli_target import (
    WORKSPACE_TARGET_WARNING,
    get_pipeline_or_job_python_origin_from_kwargs,
    job_repository_target_argument,
    job_target_argument,
    python_job_target_argument,
    python_pipeline_or_job_config_argument,
)
from dagster.core.execution.api import create_execution_plan
from dagster.core.instance import DagsterInstance
from dagster.core.storage.tags import MEMOIZED_RUN_TAG
from dagster.utils import DEFAULT_WORKSPACE_YAML_FILENAME
from dagster.utils.hosted_user_process import recon_pipeline_from_origin
from dagster.utils.interrupts import capture_interrupts

from .utils import get_instance_for_service


@click.group(name="job")
def job_cli():
    """
    Commands for working with Dagster jobs.
    """


@job_cli.command(
    name="list",
    help="List the jobs in a repository. {warning}".format(warning=WORKSPACE_TARGET_WARNING),
)
@job_repository_target_argument
def job_list_command(**kwargs):
    return execute_list_command(kwargs, click.echo, True)


def get_job_in_same_python_env_instructions(command_name):
    return (
        "This commands targets a job. The job can be specified in a number of ways:"
        "\n\n1. dagster job {command_name} -f /path/to/file.py -a define_some_job"
        "\n\n2. dagster job {command_name} -m a_module.submodule -a define_some_job"
        "\n\n3. dagster job {command_name} -f /path/to/file.py -a define_some_repo -j <<job_name>>"
        "\n\n4. dagster job {command_name} -m a_module.submodule -a define_some_repo -j <<job_name>>"
    ).format(command_name=command_name)


def get_job_instructions(command_name):
    return (
        "This commands targets a job. The job can be specified in a number of ways:"
        "\n\n1. dagster job {command_name} -j <<job_name>> (works if .{default_filename} exists)"
        "\n\n2. dagster job {command_name} -j <<job_name>> -w path/to/{default_filename}"
        "\n\n3. dagster job {command_name} -f /path/to/file.py -a define_some_job"
        "\n\n4. dagster job {command_name} -m a_module.submodule -a define_some_job"
        "\n\n5. dagster job {command_name} -f /path/to/file.py -a define_some_repo -j <<job_name>>"
        "\n\n6. dagster job {command_name} -m a_module.submodule -a define_some_repo -j <<job_name>>"
    ).format(command_name=command_name, default_filename=DEFAULT_WORKSPACE_YAML_FILENAME)


@job_cli.command(
    name="print",
    help="Print a job.\n\n{instructions}".format(instructions=get_job_instructions("print")),
)
@click.option("--verbose", is_flag=True)
@job_target_argument
def job_print_command(verbose, **cli_args):
    with get_instance_for_service("``dagster job print``") as instance:
        return execute_print_command(
            instance, verbose, cli_args, click.echo, using_job_op_graph_apis=True
        )


@job_cli.command(
    name="list_versions",
    help="Display the freshness of memoized results for the given job.\n\n{instructions}".format(
        instructions=get_job_in_same_python_env_instructions("list_versions")
    ),
)
@python_job_target_argument
@python_pipeline_or_job_config_argument("list_versions", using_job_op_graph_apis=True)
def job_list_versions_command(**kwargs):
    with DagsterInstance.get() as instance:
        execute_list_versions_command(instance, kwargs)


def execute_list_versions_command(instance: DagsterInstance, kwargs: Dict[str, object]):
    check.inst_param(instance, "instance", DagsterInstance)

    config = list(check.opt_tuple_param(kwargs.get("config"), "config", default=(), of_type=str))

    job_origin = get_pipeline_or_job_python_origin_from_kwargs(kwargs, True)
    job = recon_pipeline_from_origin(job_origin)
    run_config = get_run_config_from_file_list(config)

    memoized_plan = create_execution_plan(
        job,
        run_config=run_config,
        mode="default",
        instance_ref=instance.get_ref(),
        tags={MEMOIZED_RUN_TAG: "true"},
    )

    add_step_to_table(memoized_plan)


@job_cli.command(
    name="execute",
    help="Execute a job.\n\n{instructions}".format(
        instructions=get_job_in_same_python_env_instructions("execute")
    ),
)
@python_job_target_argument
@python_pipeline_or_job_config_argument("execute", using_job_op_graph_apis=True)
@click.option("--tags", type=click.STRING, help="JSON string of tags to use for this job run")
def job_execute_command(**kwargs):
    with capture_interrupts():
        with get_instance_for_service("``dagster job execute``") as instance:
            execute_execute_command(instance, kwargs, True)


@job_cli.command(
    name="launch",
    help="Launch a job using the run launcher configured on the Dagster instance.\n\n{instructions}".format(
        instructions=get_job_instructions("launch")
    ),
)
@job_target_argument
@python_pipeline_or_job_config_argument("launch", True)
@click.option(
    "--config-json",
    type=click.STRING,
    help="JSON string of run config to use for this job run. Cannot be used with -c / --config.",
)
@click.option("--tags", type=click.STRING, help="JSON string of tags to use for this job run")
@click.option("--run-id", type=click.STRING, help="The ID to give to the launched job run")
def job_launch_command(**kwargs):
    with DagsterInstance.get() as instance:
        return execute_launch_command(instance, kwargs)


@job_cli.command(
    name="scaffold_config",
    help="Scaffold the config for a job.\n\n{instructions}".format(
        instructions=get_job_in_same_python_env_instructions("scaffold_config")
    ),
)
@python_job_target_argument
@click.option("--print-only-required", default=False, is_flag=True)
def job_scaffold_command(**kwargs):
    execute_scaffold_command(kwargs, click.echo, using_job_op_graph_apis=True)


@job_cli.command(
    name="backfill",
    help="Backfill a partitioned job.\n\n{instructions}".format(
        instructions=get_job_instructions("backfill")
    ),
)
@job_target_argument
@click.option(
    "--partitions",
    type=click.STRING,
    help="Comma-separated list of partition names that we want to backfill",
)
@click.option(
    "--all",
    type=click.STRING,
    help="Specify to select all partitions to backfill.",
)
@click.option(
    "--from",
    type=click.STRING,
    help=(
        "Specify a start partition for this backfill job"
        "\n\nExample: "
        "dagster job backfill log_daily_stats --from 20191101"
    ),
)
@click.option(
    "--to",
    type=click.STRING,
    help=(
        "Specify an end partition for this backfill job"
        "\n\nExample: "
        "dagster job backfill log_daily_stats --to 20191201"
    ),
)
@click.option("--tags", type=click.STRING, help="JSON string of tags to use for this job run")
@click.option("--noprompt", is_flag=True)
def job_backfill_command(**kwargs):
    with DagsterInstance.get() as instance:
        execute_backfill_command(kwargs, click.echo, instance, True)
