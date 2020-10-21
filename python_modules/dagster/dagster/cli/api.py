from __future__ import print_function

import os
import signal
import sys
import threading
import time
import warnings
from collections import namedtuple
from contextlib import contextmanager

import click
from dagster import check, seven
from dagster.cli.workspace.cli_target import (
    get_repository_location_from_kwargs,
    get_repository_origin_from_kwargs,
    get_working_directory_from_kwargs,
    python_origin_target_argument,
    repository_target_argument,
)
from dagster.core.errors import DagsterSubprocessError
from dagster.core.events import EngineEventData
from dagster.core.execution.api import (
    create_execution_plan,
    execute_plan_iterator,
    execute_run_iterator,
)
from dagster.core.execution.retries import Retries
from dagster.core.host_representation.external import ExternalPipeline
from dagster.core.host_representation.external_data import ExternalScheduleExecutionErrorData
from dagster.core.host_representation.selector import PipelineSelector
from dagster.core.instance import DagsterInstance
from dagster.core.scheduler import (
    ScheduleTickData,
    ScheduleTickStatus,
    ScheduledExecutionFailed,
    ScheduledExecutionSkipped,
    ScheduledExecutionSuccess,
)
from dagster.core.storage.tags import check_tags
from dagster.core.telemetry import telemetry_wrapper
from dagster.core.types.loadable_target_origin import LoadableTargetOrigin
from dagster.grpc import DagsterGrpcClient, DagsterGrpcServer
from dagster.grpc.types import ExecuteRunArgs, ExecuteStepArgs, ScheduleExecutionDataMode
from dagster.serdes import (
    deserialize_json_to_dagster_namedtuple,
    serialize_dagster_namedtuple,
    whitelist_for_serdes,
)
from dagster.serdes.ipc import ipc_write_stream
from dagster.utils import setup_windows_interrupt_support
from dagster.utils.error import serializable_error_info_from_exc_info
from dagster.utils.hosted_user_process import recon_pipeline_from_origin
from dagster.utils.merger import merge_dicts


@whitelist_for_serdes
class ExecuteRunArgsLoadComplete(namedtuple("_ExecuteRunArgsLoadComplete", "")):
    pass


@click.command(
    name="execute_run_with_structured_logs",
    help=(
        "[INTERNAL] This is an internal utility. Users should generally not invoke this command "
        "interactively."
    ),
)
@click.argument("input_json", type=click.STRING)
def execute_run_with_structured_logs_command(input_json):
    try:
        signal.signal(signal.SIGTERM, signal.getsignal(signal.SIGINT))
    except ValueError:
        warnings.warn(
            (
                "Unexpected error attempting to manage signal handling on thread {thread_name}. "
                "You should not invoke this API (execute_run_with_structured_logs) from threads "
                "other than the main thread."
            ).format(thread_name=threading.current_thread().name)
        )

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
    setup_windows_interrupt_support()

    try:
        for event in execute_run_iterator(recon_pipeline, pipeline_run, instance):
            write_stream_fn(event)
    except KeyboardInterrupt:
        instance.report_engine_event(
            message="Pipeline execution terminated by interrupt", pipeline_run=pipeline_run,
        )
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


def get_step_stats_by_key(instance, pipeline_run, step_keys_to_execute):
    # When using the k8s executor, there whould only ever be one step key
    step_stats = instance.get_run_step_stats(pipeline_run.run_id, step_keys=step_keys_to_execute)
    step_stats_by_key = {step_stat.step_key: step_stat for step_stat in step_stats}
    return step_stats_by_key


def verify_step(instance, pipeline_run, retries, step_keys_to_execute):
    step_stats_by_key = get_step_stats_by_key(instance, pipeline_run, step_keys_to_execute)

    for step_key in step_keys_to_execute:
        step_stat_for_key = step_stats_by_key.get(step_key)
        current_attempt = retries.get_attempt_count(step_key) + 1

        # When using the k8s executor, it is possible to get into an edge case when deleting
        # a step pod. K8s will restart the pod immediately even though we don't want it to.
        # Pod can be deleted manually or due to or node failures (for example, when runnong on
        # a spot instance that is evicted).
        #
        # If we encounter one of the error cases below, we exit with a success exit code
        # so that we don't cause the "Encountered failed job pods" error.
        #
        # Instead, the step will be marked as being in an unknown state by the executor and the
        # pipeline will fail accordingly.
        if current_attempt == 1 and step_stat_for_key:
            # If this is the first attempt, there shouldn't be any step stats for this
            # event yet.
            instance.report_engine_event(
                "Attempted to run {step_key} again even though it was already started. "
                "Exiting to prevent re-running the step.".format(step_key=step_key),
                pipeline_run,
            )
            return False
        elif current_attempt > 1 and step_stat_for_key:
            # If this is a retry, then the number of previous attempts should be exactly one less
            # than the current attempt

            if step_stat_for_key.attempts != current_attempt - 1:
                instance.report_engine_event(
                    "Attempted to run retry attempt {current_attempt} for step {step_key} again "
                    "even though it was already started. Exiting to prevent re-running "
                    "the step.".format(current_attempt=current_attempt, step_key=step_key),
                    pipeline_run,
                )
                return False
        elif current_attempt > 1 and not step_stat_for_key:
            instance.report_engine_event(
                "Attempting to retry attempt {current_attempt} for step {step_key} "
                "but there is no record of the original attempt".format(
                    current_attempt=current_attempt, step_key=step_key
                ),
                pipeline_run,
            )
            return False

    return True


@click.command(
    name="execute_step_with_structured_logs",
    help=(
        "[INTERNAL] This is an internal utility. Users should generally not invoke this command "
        "interactively."
    ),
)
@click.argument("input_json", type=click.STRING)
def execute_step_with_structured_logs_command(input_json):
    try:
        signal.signal(signal.SIGTERM, signal.getsignal(signal.SIGINT))
    except ValueError:
        warnings.warn(
            (
                "Unexpected error attempting to manage signal handling on thread {thread_name}. "
                "You should not invoke this API (execute_step_with_structured_logs) from threads "
                "other than the main thread."
            ).format(thread_name=threading.current_thread().name)
        )

    args = check.inst(deserialize_json_to_dagster_namedtuple(input_json), ExecuteStepArgs)

    with (
        DagsterInstance.from_ref(args.instance_ref) if args.instance_ref else DagsterInstance.get()
    ) as instance:
        pipeline_run = instance.get_run_by_id(args.pipeline_run_id)
        recon_pipeline = recon_pipeline_from_origin(args.pipeline_origin)
        retries = Retries.from_config(args.retries_dict)

        if args.should_verify_step:
            success = verify_step(instance, pipeline_run, retries, args.step_keys_to_execute)
            if not success:
                return

        execution_plan = create_execution_plan(
            recon_pipeline.subset_for_execution_from_existing_pipeline(
                pipeline_run.solids_to_execute
            ),
            run_config=args.run_config,
            step_keys_to_execute=args.step_keys_to_execute,
            mode=args.mode,
        )

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
    help="Port over which to serve. You must pass one and only one of --port/-p or --socket/-s.",
)
@click.option(
    "--socket",
    "-s",
    type=click.Path(),
    required=False,
    help="Serve over a UDS socket. You must pass one and only one of --port/-p or --socket/-s.",
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
    help="Timeout after which to shutdown if --heartbeat is set and a heartbeat is not received",
)
@click.option(
    "--lazy-load-user-code",
    is_flag=True,
    required=False,
    default=False,
    help="Wait until the first LoadRepositories call to actually load the repositories, instead of "
    "waiting to load them when the server is launched. Useful for surfacing errors when the server "
    "is managed directly from Dagit",
)
@python_origin_target_argument
@click.option(
    "--ipc-output-file",
    type=click.Path(),
    help="Internal param used by dagster when it automatically spawns gRPC servers to communicate "
    "the success or failure of the server launching. Can be ignored by users.",
)
def grpc_command(
    port=None,
    socket=None,
    host="localhost",
    max_workers=1,
    heartbeat=False,
    heartbeat_timeout=30,
    lazy_load_user_code=False,
    ipc_output_file=None,
    **kwargs
):
    if seven.IS_WINDOWS and port is None:
        raise click.UsageError(
            "You must pass a valid --port/-p on Windows: --socket/-s not supported."
        )
    if not (port or socket and not (port and socket)):
        raise click.UsageError("You must pass one and only one of --port/-p or --socket/-s.")

    loadable_target_origin = None
    if any(
        kwargs[key]
        for key in [
            "attribute",
            "working_directory",
            "module_name",
            "package_name",
            "python_file",
            "empty_working_directory",
        ]
    ):
        loadable_target_origin = LoadableTargetOrigin(
            executable_path=sys.executable,
            attribute=kwargs["attribute"],
            working_directory=get_working_directory_from_kwargs(kwargs),
            module_name=kwargs["module_name"],
            python_file=kwargs["python_file"],
            package_name=kwargs["package_name"],
        )

    server = DagsterGrpcServer(
        port=port,
        socket=socket,
        host=host,
        loadable_target_origin=loadable_target_origin,
        max_workers=max_workers,
        heartbeat=heartbeat,
        heartbeat_timeout=heartbeat_timeout,
        lazy_load_user_code=lazy_load_user_code,
        ipc_output_file=ipc_output_file,
    )

    server.serve()


@click.command(name="grpc-health-check", help="Check the status of a dagster GRPC server")
@click.option(
    "--port",
    "-p",
    type=click.INT,
    required=False,
    help="Port over which to serve. You must pass one and only one of --port/-p or --socket/-s.",
)
@click.option(
    "--socket",
    "-s",
    type=click.Path(),
    required=False,
    help="Serve over a UDS socket. You must pass one and only one of --port/-p or --socket/-s.",
)
@click.option(
    "--host",
    "-h",
    type=click.STRING,
    required=False,
    default="localhost",
    help="Hostname at which to serve. Default is localhost.",
)
def grpc_health_check_command(port=None, socket=None, host="localhost"):
    if seven.IS_WINDOWS and port is None:
        raise click.UsageError(
            "You must pass a valid --port/-p on Windows: --socket/-s not supported."
        )
    if not (port or socket and not (port and socket)):
        raise click.UsageError("You must pass one and only one of --port/-p or --socket/-s.")

    client = DagsterGrpcClient(port=port, socket=socket, host=host)
    status = client.health_check_query()
    if status != "SERVING":
        sys.exit(1)


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
                with get_repository_location_from_kwargs(kwargs) as repo_location:
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


@telemetry_wrapper
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
        scheduled_execution_time=None,  # No way to know this in general for this scheduler
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
    except Exception:  # pylint: disable=broad-except
        stream.send(
            ScheduledExecutionFailed(
                run_id=possibly_invalid_pipeline_run.run_id,
                errors=[serializable_error_info_from_exc_info(sys.exc_info())],
            )
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

    group.add_command(execute_run_with_structured_logs_command)
    group.add_command(execute_step_with_structured_logs_command)
    group.add_command(launch_scheduled_execution)
    group.add_command(grpc_command)
    group.add_command(grpc_health_check_command)
    return group


api_cli = create_api_cli_group()
