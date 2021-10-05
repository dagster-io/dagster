import warnings

import click
from dagster import __version__ as dagster_version
from dagster import check
from dagster.cli.pipeline import (
    execute_list_command,
    execute_print_command,
    get_run_config_from_file_list,
    add_step_to_table,
    execute_execute_command,
)
from dagster.cli.workspace.cli_target import (
    WORKSPACE_TARGET_WARNING,
    get_pipeline_or_job_python_origin_from_kwargs,
    job_target_argument,
    python_job_target_argument,
    python_pipeline_or_job_config_argument,
    repository_target_argument,
)
from dagster.core.execution.api import create_execution_plan
from dagster.core.instance import DagsterInstance
from dagster.core.instance.config import is_dagster_home_set
from dagster.core.storage.tags import MEMOIZED_RUN_TAG
from dagster.utils import DEFAULT_WORKSPACE_YAML_FILENAME
from dagster.utils.hosted_user_process import recon_pipeline_from_origin
from dagster.utils.interrupts import capture_interrupts


@click.group(name="job")
def job_cli():
    """
    Commands for working with Dagster jobs.
    """


@job_cli.command(
    name="list",
    help="List the jobs in a repository. {warning}".format(warning=WORKSPACE_TARGET_WARNING),
)
@repository_target_argument
def job_list_command(**kwargs):
    return execute_list_command(kwargs, click.echo, True)


def get_job_in_same_python_env_instructions(command_name):
    return (
        "This commands targets a job. The job can be specified in a number of ways:"
        "\n\n1. dagster job {command_name} -f /path/to/file.py -a define_some_job"
        "\n\n2. dagster job {command_name} -m a_module.submodule -a define_some_job"
        "\n\n3. dagster job {command_name} -f /path/to/file.py -a define_some_repo -p <<job_name>>"
        "\n\n4. dagster job {command_name} -m a_module.submodule -a define_some_repo -p <<job_name>>"
    ).format(command_name=command_name)


def get_job_instructions(command_name):
    return (
        "This commands targets a job. The job can be specified in a number of ways:"
        "\n\n1. dagster job {command_name} -p <<job_name>> (works if .{default_filename} exists)"
        "\n\n2. dagster job {command_name} -p <<job_name>> -w path/to/{default_filename}"
        "\n\n3. dagster job {command_name} -f /path/to/file.py -a define_some_job"
        "\n\n4. dagster job {command_name} -m a_module.submodule -a define_some_job"
        "\n\n5. dagster job {command_name} -f /path/to/file.py -a define_some_repo -p <<job_name>>"
        "\n\n6. dagster job {command_name} -m a_module.submodule -a define_some_repo -p <<job_name>>"
    ).format(command_name=command_name, default_filename=DEFAULT_WORKSPACE_YAML_FILENAME)


@job_cli.command(
    name="print",
    help="Print a job.\n\n{instructions}".format(instructions=get_job_instructions("print")),
)
@click.option("--verbose", is_flag=True)
@job_target_argument
def job_print_command(verbose, **cli_args):
    with DagsterInstance.get() as instance:
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


def execute_list_versions_command(instance, kwargs):
    check.inst_param(instance, "instance", DagsterInstance)

    config = list(check.opt_tuple_param(kwargs.get("config"), "config", default=(), of_type=str))

    job_origin = get_pipeline_or_job_python_origin_from_kwargs(kwargs, True)
    job = recon_pipeline_from_origin(job_origin)
    run_config = get_run_config_from_file_list(config)

    memoized_plan = create_execution_plan(
        job,
        run_config=run_config,
        mode="default",
        instance=instance,
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
        if is_dagster_home_set():
            with DagsterInstance.get() as instance:
                execute_execute_command(instance, kwargs, True)
        else:
            warnings.warn(
                "DAGSTER_HOME is not set, no metadata will be recorded for this execution.\n",
            )
            execute_execute_command(DagsterInstance.ephemeral(), kwargs, True)
