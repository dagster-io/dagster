import os
import re
import sys
import textwrap
from collections.abc import Iterator, Mapping, Sequence
from typing import Any, Callable, Optional, TypeVar, cast

import click

import dagster._check as check
from dagster import __version__ as dagster_version
from dagster._cli.config_scaffolder import scaffold_job_config
from dagster._cli.utils import get_instance_for_cli, get_possibly_temporary_instance_for_cli
from dagster._cli.workspace.cli_target import (
    WORKSPACE_TARGET_WARNING,
    ClickArgMapping,
    ClickArgValue,
    ClickOption,
    get_code_location_from_workspace,
    get_config_from_args,
    get_job_python_origin_from_kwargs,
    get_remote_job_from_kwargs,
    get_remote_job_from_remote_repo,
    get_remote_repository_from_code_location,
    get_remote_repository_from_kwargs,
    get_run_config_from_file_list,
    get_workspace_from_kwargs,
    job_repository_target_argument,
    job_target_argument,
    python_job_config_argument,
    python_job_target_argument,
)
from dagster._core.definitions import JobDefinition
from dagster._core.definitions.reconstruct import ReconstructableJob
from dagster._core.definitions.selector import JobSubsetSelector
from dagster._core.errors import DagsterBackfillFailedError
from dagster._core.execution.api import execute_job
from dagster._core.execution.backfill import BulkActionStatus, PartitionBackfill
from dagster._core.execution.execution_result import ExecutionResult
from dagster._core.execution.job_backfill import create_backfill_run
from dagster._core.instance import DagsterInstance
from dagster._core.remote_representation import (
    CodeLocation,
    RemoteJob,
    RemoteRepository,
    RepositoryHandle,
)
from dagster._core.remote_representation.external_data import (
    PartitionNamesSnap,
    PartitionSetExecutionParamSnap,
)
from dagster._core.snap import JobSnap, NodeInvocationSnap
from dagster._core.storage.dagster_run import DagsterRun
from dagster._core.telemetry import log_remote_repo_stats, telemetry_wrapper
from dagster._core.utils import make_new_backfill_id
from dagster._core.workspace.context import BaseWorkspaceRequestContext
from dagster._seven import IS_WINDOWS, JSONDecodeError, json
from dagster._time import get_current_timestamp
from dagster._utils import DEFAULT_WORKSPACE_YAML_FILENAME, PrintFn
from dagster._utils.error import serializable_error_info_from_exc_info
from dagster._utils.hosted_user_process import recon_job_from_origin
from dagster._utils.indenting_printer import IndentingPrinter
from dagster._utils.interrupts import capture_interrupts
from dagster._utils.merger import merge_dicts
from dagster._utils.tags import normalize_tags
from dagster._utils.yaml_utils import dump_run_config_yaml

T = TypeVar("T")
T_Callable = TypeVar("T_Callable", bound=Callable[..., Any])


@click.group(name="job")
def job_cli():
    """Commands for working with Dagster jobs."""


def apply_click_params(command: T_Callable, *click_params: ClickOption) -> T_Callable:
    for click_param in click_params:
        command = click_param(command)
    return command


@job_cli.command(
    name="list",
    help=f"List the jobs in a repository. {WORKSPACE_TARGET_WARNING}",
)
@job_repository_target_argument
def job_list_command(**kwargs):
    return execute_list_command(kwargs, click.echo)


def execute_list_command(cli_args, print_fn):
    with get_possibly_temporary_instance_for_cli("``dagster job list``") as instance:
        with get_remote_repository_from_kwargs(
            instance, version=dagster_version, kwargs=cli_args
        ) as repo:
            title = f"Repository {repo.name}"
            print_fn(title)
            print_fn("*" * len(title))
            first = True
            for job in repo.get_all_jobs():
                job_title = f"Job: {job.name}"

                if not first:
                    print_fn("*" * len(job_title))
                first = False

                print_fn(job_title)
                if job.description:
                    print_fn("Description:")
                    print_fn(format_description(job.description, indent=" " * 4))
                print_fn("Ops: (Execution Order)")
                for node_name in job.job_snapshot.node_names_in_topological_order:
                    print_fn("    " + node_name)


def get_job_in_same_python_env_instructions(command_name):
    return (
        "This commands targets a job. The job can be specified in a number of ways:\n\n1. dagster"
        f" job {command_name} -f /path/to/file.py -a define_some_job\n\n2. dagster job"
        f" {command_name} -m a_module.submodule -a define_some_job\n\n3. dagster job {command_name}"
        f" -f /path/to/file.py -a define_some_repo -j <<job_name>>\n\n4. dagster job {command_name}"
        " -m a_module.submodule -a define_some_repo -j <<job_name>>"
    )


def get_job_instructions(command_name):
    return (
        "This commands targets a job. The job can be specified in a number of ways:\n\n1. dagster"
        f" job {command_name} -j <<job_name>> (works if .{DEFAULT_WORKSPACE_YAML_FILENAME} exists)\n\n2. dagster"
        f" job {command_name} -j <<job_name>> -w path/to/{DEFAULT_WORKSPACE_YAML_FILENAME}\n\n3. dagster job"
        f" {command_name} -f /path/to/file.py -a define_some_job\n\n4. dagster job {command_name} -m"
        f" a_module.submodule -a define_some_job\n\n5. dagster job {command_name} -f"
        f" /path/to/file.py -a define_some_repo -j <<job_name>>\n\n6. dagster job {command_name} -m"
        " a_module.submodule -a define_some_repo -j <<job_name>>"
    )


@job_cli.command(
    name="print",
    help="Print a job.\n\n{instructions}".format(instructions=get_job_instructions("print")),
)
@click.option("--verbose", is_flag=True)
@job_target_argument
def job_print_command(verbose, **cli_args):
    with get_possibly_temporary_instance_for_cli("``dagster job print``") as instance:
        return execute_print_command(instance, verbose, cli_args, click.echo)


def execute_print_command(instance, verbose, cli_args, print_fn):
    with get_remote_job_from_kwargs(
        instance,
        version=dagster_version,
        kwargs=cli_args,
    ) as remote_job:
        job_snapshot = remote_job.job_snapshot

        if verbose:
            print_job(
                job_snapshot,
                print_fn=print_fn,
            )
        else:
            print_ops(
                job_snapshot,
                print_fn=print_fn,
            )


def print_ops(
    job_snapshot: JobSnap,
    print_fn: Callable[..., Any],
):
    check.inst_param(job_snapshot, "job_snapshot", JobSnap)
    check.callable_param(print_fn, "print_fn")

    printer = IndentingPrinter(indent_level=2, printer=print_fn)
    printer.line(f"Job: {job_snapshot.name}")

    printer.line("Ops")
    for node in job_snapshot.dep_structure_snapshot.node_invocation_snaps:
        with printer.with_indent():
            printer.line(f"Op: {node.node_name}")


def print_job(
    job_snapshot: JobSnap,
    print_fn: Callable[..., Any],
):
    check.inst_param(job_snapshot, "job_snapshot", JobSnap)
    check.callable_param(print_fn, "print_fn")
    printer = IndentingPrinter(indent_level=2, printer=print_fn)
    printer.line(f"Job: {job_snapshot.name}")
    print_description(printer, job_snapshot.description)

    printer.line("Ops")
    for node in job_snapshot.dep_structure_snapshot.node_invocation_snaps:
        with printer.with_indent():
            print_op(printer, job_snapshot, node)


def print_description(printer, desc):
    with printer.with_indent():
        if desc:
            printer.line("Description:")
            with printer.with_indent():
                printer.line(format_description(desc, printer.current_indent_str))


def format_description(desc: str, indent: str):
    check.str_param(desc, "desc")
    check.str_param(indent, "indent")
    desc = re.sub(r"\s+", " ", desc)
    dedented = textwrap.dedent(desc)
    wrapper = textwrap.TextWrapper(initial_indent="", subsequent_indent=indent)
    filled = wrapper.fill(dedented)
    return filled


def print_op(
    printer: IndentingPrinter,
    job_snapshot: JobSnap,
    node_invocation_snap: NodeInvocationSnap,
) -> None:
    check.inst_param(job_snapshot, "job_snapshot", JobSnap)
    check.inst_param(node_invocation_snap, "node_invocation_snap", NodeInvocationSnap)
    printer.line(f"Op: {node_invocation_snap.node_name}")
    with printer.with_indent():
        printer.line("Inputs:")
        for input_dep_snap in node_invocation_snap.input_dep_snaps:
            with printer.with_indent():
                printer.line(f"Input: {input_dep_snap.input_name}")

        printer.line("Outputs:")
        for output_def_snap in job_snapshot.get_node_def_snap(
            node_invocation_snap.node_def_name
        ).output_def_snaps:
            printer.line(output_def_snap.name)


@job_cli.command(
    name="execute",
    help="Execute a job.\n\n{instructions}".format(
        instructions=get_job_in_same_python_env_instructions("execute")
    ),
)
@python_job_target_argument
@python_job_config_argument("execute")
@click.option("--tags", type=click.STRING, help="JSON string of tags to use for this job run")
@click.option(
    "-o",
    "--op-selection",
    type=click.STRING,
    help=(
        "Specify the op subselection to execute. It can be multiple clauses separated by commas."
        "Examples:"
        '\n- "some_op" will execute "some_op" itself'
        '\n- "*some_op" will execute "some_op" and all its ancestors (upstream dependencies)'
        '\n- "*some_op+++" will execute "some_op", all its ancestors, and its descendants'
        "   (downstream dependencies) within 3 levels down"
        '\n- "*some_op,other_op_a,other_op_b+" will execute "some_op" and all its'
        '   ancestors, "other_op_a" itself, and "other_op_b" and its direct child ops'
    ),
)
def job_execute_command(**kwargs: ClickArgValue):
    with capture_interrupts():
        with get_possibly_temporary_instance_for_cli("``dagster job execute``") as instance:
            execute_execute_command(instance, kwargs)


@telemetry_wrapper
def execute_execute_command(instance: DagsterInstance, kwargs: ClickArgMapping) -> ExecutionResult:
    check.inst_param(instance, "instance", DagsterInstance)

    config = list(
        check.opt_tuple_param(cast(tuple[str, ...], kwargs.get("config")), "config", of_type=str)
    )

    tags = get_tags_from_args(kwargs)

    job_origin = get_job_python_origin_from_kwargs(kwargs)
    recon_job = recon_job_from_origin(job_origin)
    op_selection = get_op_selection_from_args(kwargs)
    result = do_execute_command(recon_job, instance, config, tags, op_selection)

    if not result.success:
        raise click.ClickException(f"Run {result.run_id} resulted in failure.")

    return result


def get_tags_from_args(kwargs: ClickArgMapping) -> Mapping[str, str]:
    if kwargs.get("tags") is None:
        return {}
    try:
        tags = json.loads(check.str_elem(kwargs, "tags"))
        return check.is_dict(tags, str, str)
    except JSONDecodeError as e:
        raise click.UsageError(
            "Invalid JSON-string given for `--tags`: {}\n\n{}".format(
                kwargs.get("tags"),
                serializable_error_info_from_exc_info(sys.exc_info()).to_string(),
            )
        ) from e


def get_op_selection_from_args(kwargs: ClickArgMapping) -> Optional[Sequence[str]]:
    op_selection_str = kwargs.get("op_selection")
    if not isinstance(op_selection_str, str):
        return None

    return [ele.strip() for ele in op_selection_str.split(",")] if op_selection_str else None


def do_execute_command(
    recon_job: ReconstructableJob,
    instance: DagsterInstance,
    config: Optional[Sequence[str]],
    tags: Optional[Mapping[str, str]] = None,
    op_selection: Optional[Sequence[str]] = None,
) -> ExecutionResult:
    check.inst_param(recon_job, "recon_job", ReconstructableJob)
    check.inst_param(instance, "instance", DagsterInstance)
    check.opt_sequence_param(config, "config", of_type=str)

    with execute_job(
        recon_job,
        run_config=get_run_config_from_file_list(config),
        tags=tags,
        instance=instance,
        raise_on_error=False,
        op_selection=op_selection,
    ) as result:
        return result


@job_cli.command(
    name="launch",
    help=(
        "Launch a job using the run launcher configured on the Dagster instance.\n\n{instructions}".format(
            instructions=get_job_instructions("launch")
        )
    ),
)
@job_target_argument
@python_job_config_argument("launch")
@click.option(
    "--config-json",
    type=click.STRING,
    help="JSON string of run config to use for this job run. Cannot be used with -c / --config.",
)
@click.option("--tags", type=click.STRING, help="JSON string of tags to use for this job run")
@click.option("--run-id", type=click.STRING, help="The ID to give to the launched job run")
def job_launch_command(**kwargs) -> DagsterRun:
    with get_instance_for_cli() as instance:
        return execute_launch_command(instance, kwargs)


@telemetry_wrapper
def execute_launch_command(
    instance: DagsterInstance,
    kwargs: Mapping[str, str],
) -> DagsterRun:
    preset = cast(Optional[str], kwargs.get("preset"))
    check.inst_param(instance, "instance", DagsterInstance)
    config = get_config_from_args(kwargs)

    with get_workspace_from_kwargs(instance, version=dagster_version, kwargs=kwargs) as workspace:
        code_location = get_code_location_from_workspace(workspace, kwargs.get("location"))
        repo = get_remote_repository_from_code_location(
            code_location, cast(Optional[str], kwargs.get("repository"))
        )
        remote_job = get_remote_job_from_remote_repo(
            repo,
            cast(Optional[str], kwargs.get("job_name")),
        )

        log_remote_repo_stats(
            instance=instance,
            remote_job=remote_job,
            remote_repo=repo,
            source="pipeline_launch_command",
        )

        if preset and config:
            raise click.UsageError("Can not use --preset with -c / --config / --config-json.")

        run_tags = get_tags_from_args(kwargs)

        op_selection = get_op_selection_from_args(kwargs)

        dagster_run = _create_run(
            instance=instance,
            code_location=code_location,
            remote_repo=repo,
            remote_job=remote_job,
            run_config=config,
            tags=run_tags,
            op_selection=op_selection,
            run_id=cast(Optional[str], kwargs.get("run_id")),
        )

        return instance.submit_run(dagster_run.run_id, workspace)


def _create_run(
    instance: DagsterInstance,
    code_location: CodeLocation,
    remote_repo: RemoteRepository,
    remote_job: RemoteJob,
    run_config: Mapping[str, object],
    tags: Optional[Mapping[str, str]],
    op_selection: Optional[Sequence[str]],
    run_id: Optional[str],
) -> DagsterRun:
    check.inst_param(instance, "instance", DagsterInstance)
    check.inst_param(code_location, "code_location", CodeLocation)
    check.inst_param(remote_repo, "remote_repo", RemoteRepository)
    check.inst_param(remote_job, "remote_job", RemoteJob)
    check.opt_mapping_param(run_config, "run_config", key_type=str)

    check.opt_mapping_param(tags, "tags", key_type=str)
    check.opt_sequence_param(op_selection, "op_selection", of_type=str)
    check.opt_str_param(run_id, "run_id")

    run_config, tags, op_selection = _check_execute_remote_job_args(
        remote_job,
        run_config,
        tags,
        op_selection,
    )

    job_name = remote_job.name
    job_subset_selector = JobSubsetSelector(
        location_name=code_location.name,
        repository_name=remote_repo.name,
        job_name=job_name,
        op_selection=op_selection,
    )

    remote_job = code_location.get_job(job_subset_selector)

    execution_plan = code_location.get_execution_plan(
        remote_job,
        run_config,
        step_keys_to_execute=None,
        known_state=None,
        instance=instance,
    )
    execution_plan_snapshot = execution_plan.execution_plan_snapshot

    return instance.create_run(
        job_name=job_name,
        run_id=run_id,
        run_config=run_config,
        resolved_op_selection=remote_job.resolved_op_selection,
        step_keys_to_execute=execution_plan_snapshot.step_keys_to_execute,
        op_selection=op_selection,
        status=None,
        root_run_id=None,
        parent_run_id=None,
        tags=tags,
        job_snapshot=remote_job.job_snapshot,
        execution_plan_snapshot=execution_plan_snapshot,
        parent_job_snapshot=remote_job.parent_job_snapshot,
        remote_job_origin=remote_job.get_remote_origin(),
        job_code_origin=remote_job.get_python_origin(),
        asset_selection=None,
        asset_check_selection=None,
        asset_graph=remote_repo.asset_graph,
    )


def _check_execute_remote_job_args(
    remote_job: RemoteJob,
    run_config: Mapping[str, object],
    tags: Optional[Mapping[str, str]],
    op_selection: Optional[Sequence[str]],
) -> tuple[Mapping[str, object], Mapping[str, str], Optional[Sequence[str]]]:
    check.inst_param(remote_job, "remote_job", RemoteJob)
    run_config = check.opt_mapping_param(run_config, "run_config")

    tags = check.opt_mapping_param(tags, "tags", key_type=str)
    check.opt_sequence_param(op_selection, "op_selection", of_type=str)
    tags = merge_dicts(remote_job.tags, tags)

    return (
        run_config,
        normalize_tags(tags),
        op_selection,
    )


@job_cli.command(
    name="scaffold_config",
    help="Scaffold the config for a job.\n\n{instructions}".format(
        instructions=get_job_in_same_python_env_instructions("scaffold_config")
    ),
)
@python_job_target_argument
@click.option("--print-only-required", default=False, is_flag=True)
def job_scaffold_command(**kwargs):
    execute_scaffold_command(kwargs, click.echo)


def execute_scaffold_command(cli_args, print_fn):
    job_origin = get_job_python_origin_from_kwargs(cli_args)
    job = recon_job_from_origin(job_origin)
    skip_non_required = cli_args["print_only_required"]
    do_scaffold_command(job.get_definition(), print_fn, skip_non_required)


def do_scaffold_command(
    job_def: JobDefinition,
    printer: Callable[..., Any],
    skip_non_required: bool,
):
    check.inst_param(job_def, "job_def", JobDefinition)
    check.callable_param(printer, "printer")
    check.bool_param(skip_non_required, "skip_non_required")

    config_dict = scaffold_job_config(job_def, skip_non_required=skip_non_required)
    yaml_string = dump_run_config_yaml(config_dict)
    printer(yaml_string)


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
    with get_instance_for_cli() as instance:
        execute_backfill_command(kwargs, click.echo, instance)


def execute_backfill_command(
    cli_args: ClickArgMapping, print_fn: PrintFn, instance: DagsterInstance
) -> None:
    with get_workspace_from_kwargs(instance, version=dagster_version, kwargs=cli_args) as workspace:
        code_location = get_code_location_from_workspace(
            workspace, check.opt_str_elem(cli_args, "location")
        )
        _execute_backfill_command_at_location(
            cli_args,
            print_fn,
            instance,
            workspace,
            code_location,
        )


def _execute_backfill_command_at_location(
    cli_args: ClickArgMapping,
    print_fn: PrintFn,
    instance: DagsterInstance,
    workspace: BaseWorkspaceRequestContext,
    code_location: CodeLocation,
) -> None:
    repo = get_remote_repository_from_code_location(
        code_location, check.opt_str_elem(cli_args, "repository")
    )

    remote_job = get_remote_job_from_remote_repo(repo, check.opt_str_elem(cli_args, "job_name"))

    noprompt = cli_args.get("noprompt")

    job_partition_set = next(
        (
            partition_set
            for partition_set in repo.get_partition_sets()
            if partition_set.job_name == remote_job.name
        ),
        None,
    )

    if not job_partition_set:
        raise click.UsageError(f"Job `{remote_job.name}` is not partitioned.")

    run_tags = get_tags_from_args(cli_args)

    repo_handle = RepositoryHandle.from_location(
        repository_name=repo.name,
        code_location=code_location,
    )

    try:
        partition_names_or_error = code_location.get_partition_names(
            repository_handle=repo_handle,
            job_name=remote_job.name,
            instance=instance,
            selected_asset_keys=None,
        )
    except Exception as e:
        error_info = serializable_error_info_from_exc_info(sys.exc_info())
        raise DagsterBackfillFailedError(
            f"Failure fetching partition names: {error_info.message}",
            serialized_error_info=error_info,
        ) from e
    if not isinstance(partition_names_or_error, PartitionNamesSnap):
        raise DagsterBackfillFailedError(
            f"Failure fetching partition names: {partition_names_or_error.error}"
        )

    partition_names = gen_partition_names_from_args(
        partition_names_or_error.partition_names, cli_args
    )

    # Print backfill info
    print_fn(f"\n Job: {remote_job.name}")
    print_fn(f"   Partitions: {print_partition_format(partition_names, indent_level=15)}\n")

    # Confirm and launch
    if noprompt or click.confirm(
        f"Do you want to proceed with the backfill ({len(partition_names)} partitions)?"
    ):
        print_fn("Launching runs... ")

        backfill_id = make_new_backfill_id()
        backfill_job = PartitionBackfill(
            backfill_id=backfill_id,
            partition_set_origin=job_partition_set.get_remote_origin(),
            status=BulkActionStatus.REQUESTED,
            partition_names=partition_names,
            from_failure=False,
            reexecution_steps=None,
            tags=run_tags,
            backfill_timestamp=get_current_timestamp(),
        )
        try:
            partition_execution_data = code_location.get_partition_set_execution_params(
                repository_handle=repo_handle,
                partition_set_name=job_partition_set.name,
                partition_names=partition_names,
                instance=instance,
            )
        except Exception:
            error_info = serializable_error_info_from_exc_info(sys.exc_info())
            instance.add_backfill(
                backfill_job.with_status(BulkActionStatus.FAILED)
                .with_error(error_info)
                .with_end_timestamp(get_current_timestamp())
            )
            raise DagsterBackfillFailedError(f"Backfill failed: {error_info}")

        assert isinstance(partition_execution_data, PartitionSetExecutionParamSnap)

        for partition_data in partition_execution_data.partition_data:
            dagster_run = create_backfill_run(
                instance,
                code_location,
                remote_job,
                job_partition_set,
                backfill_job,
                partition_data.name,
                partition_data.tags,
                partition_data.run_config,
            )
            if dagster_run:
                instance.submit_run(dagster_run.run_id, workspace)

        instance.add_backfill(
            backfill_job.with_status(BulkActionStatus.COMPLETED).with_end_timestamp(
                get_current_timestamp()
            )
        )

        print_fn(f"Launched backfill job `{backfill_id}`")

    else:
        print_fn("Aborted!")


def gen_partition_names_from_args(
    partition_names: Sequence[str], kwargs: ClickArgMapping
) -> Sequence[str]:
    partition_selector_args = [
        bool(kwargs.get("all")),
        bool(kwargs.get("partitions")),
        (bool(kwargs.get("from")) or bool(kwargs.get("to"))),
    ]
    if sum(partition_selector_args) > 1:
        raise click.UsageError(
            "error, cannot use more than one of: `--all`, `--partitions`, `--from/--to`"
        )

    if kwargs.get("all"):
        return partition_names

    if kwargs.get("partitions"):
        selected_args = [
            s.strip() for s in check.str_elem(kwargs, "partitions").split(",") if s.strip()
        ]
        selected_partitions = [
            partition for partition in partition_names if partition in selected_args
        ]
        if len(selected_partitions) < len(selected_args):
            selected_names = [partition for partition in selected_partitions]
            unknown = [selected for selected in selected_args if selected not in selected_names]
            raise click.UsageError("Unknown partitions: {}".format(", ".join(unknown)))
        return selected_partitions

    start = validate_partition_slice(partition_names, "from", kwargs.get("from"))
    end = validate_partition_slice(partition_names, "to", kwargs.get("to"))

    return partition_names[start:end]


def print_partition_format(partitions: Sequence[str], indent_level: int) -> str:
    if not IS_WINDOWS and sys.stdout.isatty():
        _, tty_width = os.popen("stty size", "r").read().split()
        screen_width = min(250, int(tty_width))
    else:
        screen_width = 250
    max_str_len = max(len(x) for x in partitions)
    spacing = 10
    num_columns = min(10, int((screen_width - indent_level) / (max_str_len + spacing)))
    column_width = int((screen_width - indent_level) / num_columns)
    prefix = " " * max(0, indent_level - spacing)
    lines = []
    for chunk in list(split_chunk(partitions, num_columns)):
        lines.append(prefix + "".join(partition.rjust(column_width) for partition in chunk))

    return "\n" + "\n".join(lines)


def split_chunk(lst: Sequence[T], n: int) -> Iterator[Sequence[T]]:
    for i in range(0, len(lst), n):
        yield lst[i : i + n]


def validate_partition_slice(partition_names: Sequence[str], name: str, value) -> int:
    is_start = name == "from"
    if value is None:
        return 0 if is_start else len(partition_names)
    if value not in partition_names:
        raise click.UsageError(f"invalid value {value} for {name}")
    index = partition_names.index(value)
    return index if is_start else index + 1
