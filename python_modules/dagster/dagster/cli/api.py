from __future__ import print_function

import os
import signal
import sys
import time
from collections import namedtuple
from contextlib import contextmanager

import click

from dagster import check, seven
from dagster.cli.workspace.cli_target import (
    get_repository_location_from_kwargs,
    get_repository_origin_from_kwargs,
    python_origin_target_argument,
    repository_target_argument,
)
from dagster.core.definitions.reconstructable import repository_def_from_target_def
from dagster.core.errors import DagsterLaunchFailedError, DagsterSubprocessError
from dagster.core.events import EngineEventData
from dagster.core.execution.api import (
    create_execution_plan,
    execute_plan_iterator,
    execute_run_iterator,
)
from dagster.core.execution.retries import Retries
from dagster.core.host_representation import external_repository_data_from_def
from dagster.core.host_representation.external import ExternalPipeline
from dagster.core.host_representation.external_data import (
    ExternalExecutionParamsData,
    ExternalExecutionParamsErrorData,
    ExternalPartitionConfigData,
    ExternalPartitionExecutionErrorData,
    ExternalPartitionNamesData,
    ExternalPartitionSetExecutionParamData,
    ExternalPartitionTagsData,
    ExternalPipelineSubsetResult,
    ExternalRepositoryData,
    ExternalScheduleExecutionData,
    ExternalScheduleExecutionErrorData,
)
from dagster.core.host_representation.selector import PipelineSelector
from dagster.core.instance import DagsterInstance
from dagster.core.origin import RepositoryPythonOrigin
from dagster.core.scheduler import (
    ScheduleTickData,
    ScheduleTickStatus,
    ScheduledExecutionFailed,
    ScheduledExecutionSkipped,
    ScheduledExecutionSuccess,
)
from dagster.core.snap.execution_plan_snapshot import (
    ExecutionPlanSnapshot,
    ExecutionPlanSnapshotErrorData,
)
from dagster.core.storage.tags import check_tags
from dagster.core.types.loadable_target_origin import LoadableTargetOrigin
from dagster.grpc import DagsterGrpcServer
from dagster.grpc.impl import (
    get_external_execution_plan_snapshot,
    get_external_pipeline_subset_result,
    get_external_schedule_execution,
    get_external_triggered_execution_params,
    get_partition_config,
    get_partition_names,
    get_partition_set_execution_param_data,
    get_partition_tags,
)
from dagster.grpc.types import (
    ExecuteRunArgs,
    ExecuteStepArgs,
    ExecutionPlanSnapshotArgs,
    ExternalScheduleExecutionArgs,
    ExternalTriggeredExecutionArgs,
    ListRepositoriesInput,
    ListRepositoriesResponse,
    LoadableRepositorySymbol,
    PartitionArgs,
    PartitionNamesArgs,
    PartitionSetExecutionParamArgs,
    PipelineSubsetSnapshotArgs,
    ScheduleExecutionDataMode,
)
from dagster.grpc.utils import get_loadable_targets
from dagster.serdes import (
    deserialize_json_to_dagster_namedtuple,
    serialize_dagster_namedtuple,
    whitelist_for_serdes,
)
from dagster.serdes.ipc import (
    ipc_write_stream,
    ipc_write_unary_response,
    read_unary_input,
    setup_interrupt_support,
)
from dagster.utils.error import SerializableErrorInfo, serializable_error_info_from_exc_info
from dagster.utils.hosted_user_process import (
    recon_pipeline_from_origin,
    recon_repository_from_origin,
)
from dagster.utils.merger import merge_dicts

# Helpers


def unary_api_cli_command(name, help_str, input_cls, output_cls):
    """
    Use this to decorate synchronous api cli commands that take
    one object and return one object.
    """
    check.str_param(name, "name")
    check.str_param(help_str, "help_str")
    check.type_param(input_cls, "input_cls")
    check.inst_param(output_cls, "output_cls", (tuple, check.type_types))

    def wrap(fn):
        @click.command(name=name, help=help_str)
        @click.argument("input_file", type=click.Path())
        @click.argument("output_file", type=click.Path())
        def command(input_file, output_file):
            args = check.inst(read_unary_input(input_file), input_cls)
            output = check.inst(fn(args), output_cls)
            ipc_write_unary_response(output_file, output)

        return command

    return wrap


@unary_api_cli_command(
    name="list_repositories",
    help_str=(
        "[INTERNAL] Return the snapshot for the given repository. This is an internal utility. "
        "Users should generally not invoke this command interactively."
    ),
    input_cls=ListRepositoriesInput,
    output_cls=(ListRepositoriesResponse, SerializableErrorInfo),
)
def list_repositories_command(args):
    check.inst_param(args, "args", ListRepositoriesInput)
    python_file, module_name, working_directory, attribute = (
        args.python_file,
        args.module_name,
        args.working_directory,
        args.attribute,
    )
    try:
        loadable_targets = get_loadable_targets(
            python_file, module_name, working_directory, attribute
        )
        return ListRepositoriesResponse(
            [
                LoadableRepositorySymbol(
                    attribute=lt.attribute,
                    repository_name=repository_def_from_target_def(lt.target_definition).name,
                )
                for lt in loadable_targets
            ]
        )
    except Exception:  # pylint: disable=broad-except
        return serializable_error_info_from_exc_info(sys.exc_info())


@unary_api_cli_command(
    name="repository",
    help_str=(
        "[INTERNAL] Return all repository symbols in a given python_file or module name. "
        "Used to bootstrap workspace creation process. This is an internal utility. Users should "
        "generally not invoke this command interactively."
    ),
    input_cls=RepositoryPythonOrigin,
    output_cls=ExternalRepositoryData,
)
def repository_snapshot_command(repository_python_origin):

    recon_repo = recon_repository_from_origin(repository_python_origin)
    return external_repository_data_from_def(recon_repo.get_definition())


@unary_api_cli_command(
    name="pipeline_subset",
    help_str=(
        "[INTERNAL] Return ExternalPipelineSubsetResult for the given pipeline. This is an "
        "internal utility. Users should generally not invoke this command interactively."
    ),
    input_cls=PipelineSubsetSnapshotArgs,
    output_cls=ExternalPipelineSubsetResult,
)
def pipeline_subset_snapshot_command(args):
    return get_external_pipeline_subset_result(
        recon_pipeline_from_origin(args.pipeline_origin), args.solid_selection
    )


@unary_api_cli_command(
    name="execution_plan",
    help_str=(
        "[INTERNAL] Create an execution plan and return its snapshot. This is an internal utility. "
        "Users should generally not invoke this command interactively."
    ),
    input_cls=ExecutionPlanSnapshotArgs,
    output_cls=(ExecutionPlanSnapshot, ExecutionPlanSnapshotErrorData),
)
def execution_plan_snapshot_command(args):
    check.inst_param(args, "args", ExecutionPlanSnapshotArgs)

    recon_pipeline = recon_pipeline_from_origin(args.pipeline_origin)
    return get_external_execution_plan_snapshot(recon_pipeline, args)


@unary_api_cli_command(
    name="partition_config",
    help_str=(
        "[INTERNAL] Return the config for a partition. This is an internal utility. Users should "
        "generally not invoke this command interactively."
    ),
    input_cls=PartitionArgs,
    output_cls=(ExternalPartitionConfigData, ExternalPartitionExecutionErrorData),
)
def partition_config_command(args):
    check.inst_param(args, "args", PartitionArgs)
    return get_partition_config(args)


@unary_api_cli_command(
    name="partition_tags",
    help_str=(
        "[INTERNAL] Return the tags for a partition. This is an internal utility. Users should "
        "generally not invoke this command interactively."
    ),
    input_cls=PartitionArgs,
    output_cls=(ExternalPartitionTagsData, ExternalPartitionExecutionErrorData),
)
def partition_tags_command(args):
    return get_partition_tags(args)


@unary_api_cli_command(
    name="partition_names",
    help_str=(
        "[INTERNAL] Return the partition names for a partition set . This is an internal utility. "
        "Users should generally not invoke this command interactively."
    ),
    input_cls=PartitionNamesArgs,
    output_cls=(ExternalPartitionNamesData, ExternalPartitionExecutionErrorData),
)
def partition_names_command(args):
    return get_partition_names(args)


@unary_api_cli_command(
    name="partition_set_execution_param_data",
    help_str=(
        "[INTERNAL] Return the args for launching a partition backfill. This is an internal "
        "utility. Users should generally not invoke this command interactively."
    ),
    input_cls=PartitionSetExecutionParamArgs,
    output_cls=(ExternalPartitionSetExecutionParamData, ExternalPartitionExecutionErrorData),
)
def partition_set_execution_param_command(args):
    return get_partition_set_execution_param_data(args)


@unary_api_cli_command(
    name="schedule_config",
    help_str=(
        "[INTERNAL] Return the config for a schedule. This is an internal utility. Users should "
        "generally not invoke this command interactively."
    ),
    input_cls=ExternalScheduleExecutionArgs,
    output_cls=(ExternalScheduleExecutionData, ExternalScheduleExecutionErrorData),
)
def schedule_execution_data_command(args):
    recon_repo = recon_repository_from_origin(args.repository_origin)
    return get_external_schedule_execution(recon_repo, args)


@unary_api_cli_command(
    name="trigger_execution_params",
    help_str=(
        "[INTERNAL] Return the execution params for a triggered execution. This is an internal "
        "utility. Users should generally not invoke this command interactively."
    ),
    input_cls=ExternalTriggeredExecutionArgs,
    output_cls=(ExternalExecutionParamsData, ExternalExecutionParamsErrorData),
)
def trigger_execution_params_command(args):
    recon_repo = recon_repository_from_origin(args.repository_origin)
    return get_external_triggered_execution_params(recon_repo, args)


@whitelist_for_serdes
class ExecuteRunArgsLoadComplete(namedtuple("_ExecuteRunArgsLoadComplete", "")):
    pass


@click.command(
    name="execute_run",
    help=(
        "[INTERNAL] This is an internal utility. Users should generally not invoke this command "
        "interactively."
    ),
)
@click.argument("input_file", type=click.Path())
@click.argument("output_file", type=click.Path())
def execute_run_command(input_file, output_file):
    args = check.inst(read_unary_input(input_file), ExecuteRunArgs)
    recon_pipeline = recon_pipeline_from_origin(args.pipeline_origin)
    with DagsterInstance.from_ref(args.instance_ref) as instance:
        with ipc_write_stream(output_file) as ipc_stream:

            def send_to_stream(event):
                ipc_stream.send(event)

            return _execute_run_command_body(
                recon_pipeline, args.pipeline_run_id, instance, send_to_stream
            )


@click.command(
    name="execute_run_with_structured_logs",
    help=(
        "[INTERNAL] This is an internal utility. Users should generally not invoke this command "
        "interactively."
    ),
)
@click.argument("input_json", type=click.STRING)
def execute_run_with_structured_logs_command(input_json):
    signal.signal(signal.SIGTERM, signal.getsignal(signal.SIGINT))

    args = check.inst(deserialize_json_to_dagster_namedtuple(input_json), ExecuteRunArgs)
    recon_pipeline = recon_pipeline_from_origin(args.pipeline_origin)

    with (
        DagsterInstance.from_ref(args.instance_ref) if args.instance_ref else DagsterInstance.get()
    ) as instance:
        buffer = []

        def send_to_buffer(event):
            buffer.append(serialize_dagster_namedtuple(event))

        _execute_run_command_body(recon_pipeline, args.pipeline_run_id, instance, send_to_buffer)

        for line in buffer:
            click.echo(line)


def _execute_run_command_body(recon_pipeline, pipeline_run_id, instance, write_stream_fn):

    # we need to send but the fact that we have loaded the args so the calling
    # process knows it is safe to clean up the temp input file
    write_stream_fn(ExecuteRunArgsLoadComplete())

    pipeline_run = instance.get_run_by_id(pipeline_run_id)

    pid = os.getpid()
    instance.report_engine_event(
        "Started process for pipeline (pid: {pid}).".format(pid=pid),
        pipeline_run,
        EngineEventData.in_process(pid, marker_end="cli_api_subprocess_init"),
    )

    # Perform setup so that termination of the execution will unwind and report to the
    # instance correctly
    setup_interrupt_support()

    try:
        for event in execute_run_iterator(recon_pipeline, pipeline_run, instance):
            write_stream_fn(event)
    except DagsterSubprocessError as err:
        if not all(
            [err_info.cls_name == "KeyboardInterrupt" for err_info in err.subprocess_error_infos]
        ):
            instance.report_engine_event(
                "An exception was thrown during execution that is likely a framework error, "
                "rather than an error in user code.",
                pipeline_run,
                EngineEventData.engine_error(serializable_error_info_from_exc_info(sys.exc_info())),
            )
    except Exception:  # pylint: disable=broad-except
        instance.report_engine_event(
            "An exception was thrown during execution that is likely a framework error, "
            "rather than an error in user code.",
            pipeline_run,
            EngineEventData.engine_error(serializable_error_info_from_exc_info(sys.exc_info())),
        )
    finally:
        instance.report_engine_event(
            "Process for pipeline exited (pid: {pid}).".format(pid=pid), pipeline_run,
        )


@click.command(
    name="execute_step_with_structured_logs",
    help=(
        "[INTERNAL] This is an internal utility. Users should generally not invoke this command "
        "interactively."
    ),
)
@click.argument("input_json", type=click.STRING)
def execute_step_with_structured_logs_command(input_json):
    signal.signal(signal.SIGTERM, signal.getsignal(signal.SIGINT))

    args = check.inst(deserialize_json_to_dagster_namedtuple(input_json), ExecuteStepArgs)

    with (
        DagsterInstance.from_ref(args.instance_ref) if args.instance_ref else DagsterInstance.get()
    ) as instance:
        pipeline_run = instance.get_run_by_id(args.pipeline_run_id)
        recon_pipeline = recon_pipeline_from_origin(args.pipeline_origin)

        execution_plan = create_execution_plan(
            recon_pipeline.subset_for_execution_from_existing_pipeline(
                pipeline_run.solids_to_execute
            ),
            run_config=args.run_config,
            step_keys_to_execute=args.step_keys_to_execute,
            mode=args.mode,
        )

        retries = Retries.from_config(args.retries_dict)

        buff = []
        for event in execute_plan_iterator(
            execution_plan, pipeline_run, instance, run_config=args.run_config, retries=retries,
        ):
            buff.append(serialize_dagster_namedtuple(event))

        for line in buff:
            click.echo(line)


class _ScheduleTickHolder:
    def __init__(self, tick, instance):
        self._tick = tick
        self._instance = instance
        self._set = False

    def update_with_status(self, status, **kwargs):
        self._tick = self._tick.with_status(status=status, **kwargs)

    def write(self):
        self._instance.update_schedule_tick(self._tick)


@contextmanager
def _schedule_tick_state(instance, stream, tick_data):
    tick = instance.create_schedule_tick(tick_data)
    holder = _ScheduleTickHolder(tick=tick, instance=instance)
    try:
        yield holder
    except Exception:  # pylint: disable=broad-except
        error_data = serializable_error_info_from_exc_info(sys.exc_info())
        holder.update_with_status(ScheduleTickStatus.FAILURE, error=error_data)
        stream.send(ScheduledExecutionFailed(run_id=None, errors=[error_data]))
    finally:
        holder.write()


@click.command(name="grpc", help="Serve the Dagster inter-process API over GRPC")
@click.option(
    "--port",
    "-p",
    type=click.INT,
    required=False,
    help="Port over which to serve. You must pass one and only one of --port/-p or --socket/-f.",
)
@click.option(
    "--socket",
    "-s",
    type=click.Path(),
    required=False,
    help="Serve over a UDS socket. You must pass one and only one of --port/-p or --socket/-f.",
)
@click.option(
    "--host",
    "-h",
    type=click.STRING,
    required=False,
    default="localhost",
    help="Hostname at which to serve. Default is localhost.",
)
@click.option(
    "--max_workers",
    "-n",
    type=click.INT,
    required=False,
    default=1,
    help="Maximum number of (threaded) workers to use in the GRPC server",
)
@click.option(
    "--heartbeat",
    is_flag=True,
    help=(
        "If set, the GRPC server will shut itself down when it fails to receive a heartbeat "
        "after a timeout configurable with --heartbeat-timeout."
    ),
)
@click.option(
    "--heartbeat-timeout",
    type=click.INT,
    required=False,
    default=30,
    help="Timout after which to shutdown if --heartbeat is set and a heartbeat is not received",
)
@python_origin_target_argument
def grpc_command(
    port=None,
    socket=None,
    host="localhost",
    max_workers=1,
    heartbeat=False,
    heartbeat_timeout=30,
    **kwargs
):
    if seven.IS_WINDOWS and port is None:
        raise click.UsageError(
            "You must pass a valid --port/-p on Windows: --socket/-f not supported."
        )
    if not (port or socket and not (port and socket)):
        raise click.UsageError("You must pass one and only one of --port/-p or --socket/-f.")

    loadable_target_origin = None
    if any(kwargs[key] for key in ["attribute", "working_directory", "module_name", "python_file"]):
        loadable_target_origin = LoadableTargetOrigin(
            executable_path=sys.executable,
            attribute=kwargs["attribute"],
            working_directory=kwargs["working_directory"],
            module_name=kwargs["module_name"],
            python_file=kwargs["python_file"],
        )

    server = DagsterGrpcServer(
        port=port,
        socket=socket,
        host=host,
        loadable_target_origin=loadable_target_origin,
        max_workers=max_workers,
        heartbeat=heartbeat,
        heartbeat_timeout=heartbeat_timeout,
    )

    server.serve()


###################################################################################################
# WARNING: these cli args are encoded in cron, so are not safely changed without migration
###################################################################################################
@click.command(
    name="launch_scheduled_execution",
    help=(
        "[INTERNAL] This is an internal utility. Users should generally not invoke this command "
        "interactively."
    ),
)
@click.argument("output_file", type=click.Path())
@repository_target_argument
@click.option("--schedule_name")
def launch_scheduled_execution(output_file, schedule_name, **kwargs):
    with ipc_write_stream(output_file) as stream:
        with DagsterInstance.get() as instance:
            repository_origin = get_repository_origin_from_kwargs(kwargs)
            schedule_origin = repository_origin.get_schedule_origin(schedule_name)

            # open the tick scope before we load any external artifacts so that
            # load errors are stored in DB
            with _schedule_tick_state(
                instance,
                stream,
                ScheduleTickData(
                    schedule_origin_id=schedule_origin.get_id(),
                    schedule_name=schedule_name,
                    timestamp=time.time(),
                    cron_schedule=None,  # not yet loaded
                    status=ScheduleTickStatus.STARTED,
                ),
            ) as tick:
                with get_repository_location_from_kwargs(kwargs, instance) as repo_location:
                    repo_dict = repo_location.get_repositories()
                    check.invariant(
                        repo_dict and len(repo_dict) == 1,
                        "Passed in arguments should reference exactly one repository, instead there are {num_repos}".format(
                            num_repos=len(repo_dict)
                        ),
                    )
                    external_repo = next(iter(repo_dict.values()))
                    check.invariant(
                        schedule_name
                        in [schedule.name for schedule in external_repo.get_external_schedules()],
                        "Could not find schedule named {schedule_name}".format(
                            schedule_name=schedule_name
                        ),
                    )
                    external_schedule = external_repo.get_external_schedule(schedule_name)
                    tick.update_with_status(
                        status=ScheduleTickStatus.STARTED,
                        cron_schedule=external_schedule.cron_schedule,
                    )
                    _launch_scheduled_execution(
                        instance, repo_location, external_repo, external_schedule, tick, stream
                    )


def _launch_scheduled_execution(
    instance, repo_location, external_repo, external_schedule, tick, stream
):
    pipeline_selector = PipelineSelector(
        location_name=repo_location.name,
        repository_name=external_repo.name,
        pipeline_name=external_schedule.pipeline_name,
        solid_selection=external_schedule.solid_selection,
    )

    subset_pipeline_result = repo_location.get_subset_external_pipeline_result(pipeline_selector)
    external_pipeline = ExternalPipeline(
        subset_pipeline_result.external_pipeline_data, external_repo.handle,
    )

    schedule_execution_data = repo_location.get_external_schedule_execution_data(
        instance=instance,
        repository_handle=external_repo.handle,
        schedule_name=external_schedule.name,
        schedule_execution_data_mode=ScheduleExecutionDataMode.LAUNCH_SCHEDULED_EXECUTION,
        scheduled_execution_datetime_utc=None,  # No way to know this in general for this scheduler
    )

    run_config = {}
    schedule_tags = {}
    execution_plan_snapshot = None
    errors = []

    if isinstance(schedule_execution_data, ExternalScheduleExecutionErrorData):
        error = schedule_execution_data.error
        tick.update_with_status(ScheduleTickStatus.FAILURE, error=error)
        stream.send(ScheduledExecutionFailed(run_id=None, errors=[error]))
        return
    elif not schedule_execution_data.should_execute:
        # Update tick to skipped state and return
        tick.update_with_status(ScheduleTickStatus.SKIPPED)
        stream.send(ScheduledExecutionSkipped())
        return
    else:
        run_config = schedule_execution_data.run_config
        schedule_tags = schedule_execution_data.tags
        try:
            external_execution_plan = repo_location.get_external_execution_plan(
                external_pipeline, run_config, external_schedule.mode, step_keys_to_execute=None,
            )
            execution_plan_snapshot = external_execution_plan.execution_plan_snapshot
        except DagsterSubprocessError as e:
            errors.extend(e.subprocess_error_infos)
        except Exception as e:  # pylint: disable=broad-except
            errors.append(serializable_error_info_from_exc_info(sys.exc_info()))

    pipeline_tags = external_pipeline.tags or {}
    check_tags(pipeline_tags, "pipeline_tags")
    tags = merge_dicts(pipeline_tags, schedule_tags)

    # Enter the run in the DB with the information we have
    possibly_invalid_pipeline_run = instance.create_run(
        pipeline_name=external_schedule.pipeline_name,
        run_id=None,
        run_config=run_config,
        mode=external_schedule.mode,
        solids_to_execute=external_pipeline.solids_to_execute,
        step_keys_to_execute=None,
        solid_selection=external_pipeline.solid_selection,
        status=None,
        root_run_id=None,
        parent_run_id=None,
        tags=tags,
        pipeline_snapshot=external_pipeline.pipeline_snapshot,
        execution_plan_snapshot=execution_plan_snapshot,
        parent_pipeline_snapshot=external_pipeline.parent_pipeline_snapshot,
    )

    tick.update_with_status(ScheduleTickStatus.SUCCESS, run_id=possibly_invalid_pipeline_run.run_id)

    # If there were errors, inject them into the event log and fail the run
    if len(errors) > 0:
        for error in errors:
            instance.report_engine_event(
                error.message, possibly_invalid_pipeline_run, EngineEventData.engine_error(error),
            )
        instance.report_run_failed(possibly_invalid_pipeline_run)
        stream.send(
            ScheduledExecutionFailed(run_id=possibly_invalid_pipeline_run.run_id, errors=errors)
        )
        return

    try:
        launched_run = instance.launch_run(possibly_invalid_pipeline_run.run_id, external_pipeline)
    except DagsterLaunchFailedError:
        error = serializable_error_info_from_exc_info(sys.exc_info())
        instance.report_engine_event(
            error.message, possibly_invalid_pipeline_run, EngineEventData.engine_error(error),
        )
        instance.report_run_failed(possibly_invalid_pipeline_run)
        stream.send(
            ScheduledExecutionFailed(run_id=possibly_invalid_pipeline_run.run_id, errors=[error])
        )
        return

    stream.send(ScheduledExecutionSuccess(run_id=launched_run.run_id))
    return


def create_api_cli_group():
    group = click.Group(
        name="api",
        help=(
            "[INTERNAL] These commands are intended to support internal use cases. Users should "
            "generally not invoke these commands interactively."
        ),
    )

    group.add_command(execute_run_command)
    group.add_command(execute_run_with_structured_logs_command)
    group.add_command(execute_step_with_structured_logs_command)
    group.add_command(repository_snapshot_command)
    group.add_command(pipeline_subset_snapshot_command)
    group.add_command(execution_plan_snapshot_command)
    group.add_command(list_repositories_command)
    group.add_command(partition_config_command)
    group.add_command(partition_tags_command)
    group.add_command(partition_names_command)
    group.add_command(partition_set_execution_param_command)
    group.add_command(schedule_execution_data_command)
    group.add_command(trigger_execution_params_command)
    group.add_command(launch_scheduled_execution)
    group.add_command(grpc_command)
    return group


api_cli = create_api_cli_group()
