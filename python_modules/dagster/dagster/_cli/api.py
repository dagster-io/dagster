import base64
import json
import logging
import os
import sys
import threading
import zlib
from typing import Any, Callable, Optional, cast

import click

import dagster._check as check
import dagster._seven as seven
from dagster._cli.workspace.cli_target import (
    get_working_directory_from_kwargs,
    python_origin_target_argument,
)
from dagster._core.definitions.metadata import MetadataValue
from dagster._core.errors import DagsterExecutionInterruptedError
from dagster._core.events import DagsterEvent, DagsterEventType, EngineEventData
from dagster._core.execution.api import create_execution_plan, execute_plan_iterator
from dagster._core.execution.context_creation_job import create_context_free_log_manager
from dagster._core.execution.run_cancellation_thread import start_run_cancellation_thread
from dagster._core.instance import DagsterInstance, InstanceRef
from dagster._core.origin import (
    DEFAULT_DAGSTER_ENTRY_POINT,
    JobPythonOrigin,
    get_python_environment_entry_point,
)
from dagster._core.storage.dagster_run import DagsterRun
from dagster._core.types.loadable_target_origin import LoadableTargetOrigin
from dagster._grpc import DagsterGrpcClient, DagsterGrpcServer
from dagster._grpc.impl import core_execute_run
from dagster._grpc.server import DagsterApiServer
from dagster._grpc.types import ExecuteRunArgs, ExecuteStepArgs, ResumeRunArgs
from dagster._serdes import deserialize_value, serialize_value
from dagster._utils.error import serializable_error_info_from_exc_info
from dagster._utils.hosted_user_process import recon_job_from_origin
from dagster._utils.interrupts import capture_interrupts, setup_interrupt_handlers
from dagster._utils.log import configure_loggers

from .utils import get_instance_for_cli


@click.group(name="api", hidden=True)
def api_cli():
    """[INTERNAL] These commands are intended to support internal use cases. Users should generally
    not invoke these commands interactively.
    """


@api_cli.command(
    name="execute_run",
    help=(
        "[INTERNAL] This is an internal utility. Users should generally not invoke this command "
        "interactively."
    ),
)
@click.argument("input_json", type=click.STRING)
def execute_run_command(input_json):
    with capture_interrupts():
        args = deserialize_value(input_json, ExecuteRunArgs)

        with get_instance_for_cli(instance_ref=args.instance_ref) as instance:
            buffer = []

            def send_to_buffer(event):
                buffer.append(serialize_value(event))

            return_code = _execute_run_command_body(
                args.run_id,
                instance,
                send_to_buffer,
                set_exit_code_on_failure=args.set_exit_code_on_failure or False,
            )

            if return_code != 0:
                sys.exit(return_code)


def _execute_run_command_body(
    run_id: str,
    instance: DagsterInstance,
    write_stream_fn: Callable[[DagsterEvent], Any],
    set_exit_code_on_failure: bool,
) -> int:
    if instance.should_start_background_run_thread:
        cancellation_thread, cancellation_thread_shutdown_event = start_run_cancellation_thread(
            instance, run_id
        )
    else:
        cancellation_thread, cancellation_thread_shutdown_event = None, None

    dagster_run = check.not_none(
        instance.get_run_by_id(run_id),
        f"Run with id '{run_id}' not found for run execution.",
    )

    check.inst(
        dagster_run.job_code_origin,
        JobPythonOrigin,
        f"Run with id '{run_id}' does not include an origin.",
    )

    recon_job = recon_job_from_origin(cast(JobPythonOrigin, dagster_run.job_code_origin))

    pid = os.getpid()
    instance.report_engine_event(
        f"Started process for run (pid: {pid}).",
        dagster_run,
        EngineEventData.in_process(pid),
    )

    run_worker_failed = 0

    try:
        for event in core_execute_run(
            recon_job,
            dagster_run,
            instance,
            inject_env_vars=True,
        ):
            write_stream_fn(event)
            if event.event_type == DagsterEventType.PIPELINE_FAILURE:
                run_worker_failed = True
    except:
        # relies on core_execute_run writing failures to the event log before raising
        run_worker_failed = True
    finally:
        if instance.should_start_background_run_thread:
            cancellation_thread_shutdown_event = check.not_none(cancellation_thread_shutdown_event)
            cancellation_thread = check.not_none(cancellation_thread)
            cancellation_thread_shutdown_event.set()
            if cancellation_thread.is_alive():
                cancellation_thread.join(timeout=15)
                if cancellation_thread.is_alive():
                    instance.report_engine_event(
                        "Cancellation thread did not shutdown gracefully",
                        dagster_run,
                    )

        instance.report_engine_event(
            f"Process for run exited (pid: {pid}).",
            dagster_run,
        )

    return 1 if (run_worker_failed and set_exit_code_on_failure) else 0


@api_cli.command(
    name="resume_run",
    help=(
        "[INTERNAL] This is an internal utility. Users should generally not invoke this command "
        "interactively."
    ),
)
@click.argument("input_json", type=click.STRING)
def resume_run_command(input_json):
    with capture_interrupts():
        args = deserialize_value(input_json, ResumeRunArgs)

        with get_instance_for_cli(instance_ref=args.instance_ref) as instance:
            buffer = []

            def send_to_buffer(event):
                buffer.append(serialize_value(event))

            return_code = _resume_run_command_body(
                args.run_id,
                instance,
                send_to_buffer,
                set_exit_code_on_failure=args.set_exit_code_on_failure or False,
            )

            if return_code != 0:
                sys.exit(return_code)


def _resume_run_command_body(
    run_id: Optional[str],
    instance: DagsterInstance,
    write_stream_fn: Callable[[DagsterEvent], Any],
    set_exit_code_on_failure: bool,
):
    if instance.should_start_background_run_thread:
        cancellation_thread, cancellation_thread_shutdown_event = start_run_cancellation_thread(
            instance, run_id
        )
    else:
        cancellation_thread, cancellation_thread_shutdown_event = None, None
    dagster_run = check.not_none(
        instance.get_run_by_id(run_id),  # type: ignore
        f"Run with id '{run_id}' not found for run execution.",
    )
    check.inst(
        dagster_run.job_code_origin,
        JobPythonOrigin,
        f"Run with id '{run_id}' does not include an origin.",
    )

    recon_job = recon_job_from_origin(cast(JobPythonOrigin, dagster_run.job_code_origin))

    pid = os.getpid()
    instance.report_engine_event(
        f"Started process for resuming job (pid: {pid}).",
        dagster_run,
        EngineEventData.in_process(pid),
    )

    run_worker_failed = False

    try:
        for event in core_execute_run(
            recon_job,
            dagster_run,
            instance,
            resume_from_failure=True,
            inject_env_vars=True,
        ):
            write_stream_fn(event)
            if event.event_type == DagsterEventType.PIPELINE_FAILURE:
                run_worker_failed = True

    except:
        # relies on core_execute_run writing failures to the event log before raising
        run_worker_failed = True
    finally:
        if instance.should_start_background_run_thread:
            cancellation_thread_shutdown_event = check.not_none(cancellation_thread_shutdown_event)
            cancellation_thread = check.not_none(cancellation_thread)
            cancellation_thread_shutdown_event.set()
            if cancellation_thread.is_alive():
                cancellation_thread.join(timeout=15)
                if cancellation_thread.is_alive():
                    instance.report_engine_event(
                        "Cancellation thread did not shutdown gracefully",
                        dagster_run,
                    )
        instance.report_engine_event(
            f"Process for job exited (pid: {pid}).",
            dagster_run,
        )

    return 1 if (run_worker_failed and set_exit_code_on_failure) else 0


def get_step_stats_by_key(instance, dagster_run, step_keys_to_execute):
    # When using the k8s executor, there whould only ever be one step key
    step_stats = instance.get_run_step_stats(dagster_run.run_id, step_keys=step_keys_to_execute)
    step_stats_by_key = {step_stat.step_key: step_stat for step_stat in step_stats}
    return step_stats_by_key


def verify_step(instance, dagster_run, retry_state, step_keys_to_execute):
    step_stats_by_key = get_step_stats_by_key(instance, dagster_run, step_keys_to_execute)

    for step_key in step_keys_to_execute:
        step_stat_for_key = step_stats_by_key.get(step_key)
        current_attempt = retry_state.get_attempt_count(step_key) + 1

        # When using the k8s executor, it is possible to get into an edge case when deleting
        # a step pod. K8s will restart the pod immediately even though we don't want it to.
        # Pod can be deleted manually or due to or node failures (for example, when running on
        # a spot instance that is evicted).
        #
        # If we encounter one of the error cases below, we exit with a success exit code
        # so that we don't cause the "Encountered failed job pods" error.
        #
        # Instead, the step will be marked as being in an unknown state by the executor and the
        # job will fail accordingly.
        if current_attempt == 1 and step_stat_for_key:
            # If this is the first attempt, there shouldn't be any step stats for this
            # event yet.
            instance.report_engine_event(
                f"Attempted to run {step_key} again even though it was already started. "
                "Exiting to prevent re-running the step.",
                dagster_run,
            )
            return False
        elif current_attempt > 1 and step_stat_for_key:
            # If this is a retry, then the number of previous attempts should be exactly one less
            # than the current attempt

            if step_stat_for_key.attempts != current_attempt - 1:
                instance.report_engine_event(
                    f"Attempted to run retry attempt {current_attempt} for step {step_key} again "
                    "even though it was already started. Exiting to prevent re-running "
                    "the step.",
                    dagster_run,
                )
                return False
        elif current_attempt > 1 and not step_stat_for_key:
            instance.report_engine_event(
                f"Attempting to retry attempt {current_attempt} for step {step_key} "
                "but there is no record of the original attempt",
                dagster_run,
            )
            return False

    return True


@api_cli.command(
    name="execute_step",
    help=(
        "[INTERNAL] This is an internal utility. Users should generally not invoke this command "
        "interactively."
    ),
)
@click.argument("input_json", type=click.STRING, envvar="DAGSTER_EXECUTE_STEP_ARGS", required=False)
@click.option(
    "compressed_input_json",
    "--compressed-input-json",
    type=click.STRING,
    envvar="DAGSTER_COMPRESSED_EXECUTE_STEP_ARGS",
)
def execute_step_command(input_json, compressed_input_json):
    with capture_interrupts():
        check.invariant(
            bool(input_json) != bool(compressed_input_json),
            "Must provide one of input_json or compressed_input_json",
        )

        if compressed_input_json:
            input_json = zlib.decompress(base64.b64decode(compressed_input_json.encode())).decode()

        args = deserialize_value(input_json, ExecuteStepArgs)

        with get_instance_for_cli(instance_ref=args.instance_ref) as instance:
            dagster_run = instance.get_run_by_id(args.run_id)

            buff = []

            for event in _execute_step_command_body(
                args,
                instance,
                dagster_run,
            ):
                buff.append(serialize_value(event))

            if args.print_serialized_events:
                for line in buff:
                    click.echo(line)


def _execute_step_command_body(
    args: ExecuteStepArgs, instance: DagsterInstance, dagster_run: DagsterRun
):
    single_step_key = (
        args.step_keys_to_execute[0]
        if args.step_keys_to_execute and len(args.step_keys_to_execute) == 1
        else None
    )
    try:
        check.inst(
            dagster_run,
            DagsterRun,
            f"Run with id '{args.run_id}' not found for step execution",
        )
        check.inst(
            dagster_run.job_code_origin,
            JobPythonOrigin,
            f"Run with id '{args.run_id}' does not include an origin.",
        )

        location_name = (
            dagster_run.external_job_origin.location_name
            if dagster_run.external_job_origin
            else None
        )

        instance.inject_env_vars(location_name)

        log_manager = create_context_free_log_manager(instance, dagster_run)

        yield DagsterEvent.step_worker_started(
            log_manager,
            dagster_run.job_name,
            message="Step worker started"
            + (f' for "{single_step_key}".' if single_step_key else "."),
            metadata={"pid": MetadataValue.text(str(os.getpid()))},
            step_key=single_step_key,
        )

        if args.should_verify_step:
            success = verify_step(
                instance,
                dagster_run,
                check.not_none(args.known_state).get_retry_state(),
                args.step_keys_to_execute,
            )
            if not success:
                return

        if dagster_run.has_repository_load_data:
            repository_load_data = instance.get_execution_plan_snapshot(
                check.not_none(dagster_run.execution_plan_snapshot_id)
            ).repository_load_data
        else:
            repository_load_data = None

        recon_job = (
            recon_job_from_origin(cast(JobPythonOrigin, dagster_run.job_code_origin))
            .with_repository_load_data(repository_load_data)
            .get_subset(
                op_selection=dagster_run.resolved_op_selection,
                asset_selection=dagster_run.asset_selection,
                asset_check_selection=dagster_run.asset_check_selection,
            )
        )

        execution_plan = create_execution_plan(
            recon_job,
            run_config=dagster_run.run_config,
            step_keys_to_execute=args.step_keys_to_execute,
            known_state=args.known_state,
            repository_load_data=repository_load_data,
        )

        yield from execute_plan_iterator(
            execution_plan,
            recon_job,
            dagster_run,
            instance,
            run_config=dagster_run.run_config,
            retry_mode=args.retry_mode,
        )
    except (KeyboardInterrupt, DagsterExecutionInterruptedError):
        yield instance.report_engine_event(
            message="Step execution terminated by interrupt",
            dagster_run=dagster_run,
            step_key=single_step_key,
        )
        raise
    except Exception:
        yield instance.report_engine_event(
            "An exception was thrown during step execution that is likely a framework error,"
            " rather than an error in user code.",
            dagster_run,
            EngineEventData.engine_error(serializable_error_info_from_exc_info(sys.exc_info())),
            step_key=single_step_key,
        )
        raise


@api_cli.command(name="grpc", help="Serve the Dagster inter-process API over GRPC")
@click.option(
    "--port",
    "-p",
    type=click.INT,
    required=False,
    help="Port over which to serve. You must pass one and only one of --port/-p or --socket/-s.",
    envvar="DAGSTER_GRPC_PORT",
)
@click.option(
    "--socket",
    "-s",
    type=click.Path(),
    required=False,
    help="Serve over a UDS socket. You must pass one and only one of --port/-p or --socket/-s.",
    envvar="DAGSTER_GRPC_SOCKET",
)
@click.option(
    "--host",
    "-h",
    type=click.STRING,
    required=False,
    default="localhost",
    help="Hostname at which to serve. Default is localhost.",
    envvar="DAGSTER_GRPC_HOST",
)
@click.option(
    "--max-workers",
    "--max_workers",  # for backwards compatibility
    "-n",
    type=click.INT,
    required=False,
    default=None,
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
    help=(
        "Wait until the first LoadRepositories call to actually load the repositories, instead of"
        " waiting to load them when the server is launched. Useful for surfacing errors when the"
        " server is managed directly from the Dagster UI."
    ),
    envvar="DAGSTER_LAZY_LOAD_USER_CODE",
)
@python_origin_target_argument
@click.option(
    "--use-python-environment-entry-point",
    is_flag=True,
    required=False,
    default=False,
    help=(
        "If this flag is set, the server will signal to clients that they should launch "
        "dagster commands using `<this server's python executable> -m dagster`, instead of the "
        "default `dagster` entry point. This is useful when there are multiple Python environments "
        "running in the same machine, so a single `dagster` entry point is not enough to uniquely "
        "determine the environment."
    ),
    envvar="DAGSTER_USE_PYTHON_ENVIRONMENT_ENTRY_POINT",
)
@click.option(
    "--empty-working-directory",
    is_flag=True,
    required=False,
    default=False,
    help=(
        "Indicates that the working directory should be empty and should not set to the current "
        "directory as a default"
    ),
    envvar="DAGSTER_EMPTY_WORKING_DIRECTORY",
)
@click.option(
    "--fixed-server-id",
    type=click.STRING,
    required=False,
    help=(
        "[INTERNAL] This option should generally not be used by users. Internal param used by "
        "dagster to spawn a gRPC server with the specified server id."
    ),
)
@click.option(
    "--log-level",
    type=click.Choice(["critical", "error", "warning", "info", "debug"], case_sensitive=False),
    show_default=True,
    required=False,
    default="info",
    help="Level at which to log output from the code server process",
)
@click.option(
    "--container-image",
    type=click.STRING,
    required=False,
    help="Container image to use to run code from this server.",
    envvar="DAGSTER_CONTAINER_IMAGE",
)
@click.option(
    "--container-context",
    type=click.STRING,
    required=False,
    help=(
        "Serialized JSON with configuration for any containers created to run the "
        "code from this server."
    ),
    envvar="DAGSTER_CONTAINER_CONTEXT",
)
@click.option(
    "--inject-env-vars-from-instance",
    is_flag=True,
    required=False,
    default=False,
    help="Whether to load env vars from the instance and inject them into the environment.",
    envvar="DAGSTER_INJECT_ENV_VARS_FROM_INSTANCE",
)
@click.option(
    "--location-name",
    type=click.STRING,
    required=False,
    help="Name of the code location this server corresponds to.",
    envvar="DAGSTER_LOCATION_NAME",
)
@click.option(
    "--instance-ref",
    type=click.STRING,
    required=False,
    help="[INTERNAL] Serialized InstanceRef to use for accessing the instance",
    envvar="DAGSTER_INSTANCE_REF",
)
def grpc_command(
    port=None,
    socket=None,
    host=None,
    max_workers=None,
    heartbeat=False,
    heartbeat_timeout=30,
    lazy_load_user_code=False,
    fixed_server_id=None,
    log_level="INFO",
    use_python_environment_entry_point=False,
    container_image=None,
    container_context=None,
    location_name=None,
    instance_ref=None,
    inject_env_vars_from_instance=False,
    **kwargs,
):
    check.invariant(heartbeat_timeout > 0, "heartbeat_timeout must be greater than 0")

    check.invariant(
        max_workers is None or max_workers > 1 if heartbeat else True,
        "max_workers must be greater than 1 or set to None if heartbeat is True. "
        "If set to None, the server will use the gRPC default.",
    )

    if seven.IS_WINDOWS and port is None:
        raise click.UsageError(
            "You must pass a valid --port/-p on Windows: --socket/-s not supported."
        )
    if not (port or socket and not (port and socket)):
        raise click.UsageError("You must pass one and only one of --port/-p or --socket/-s.")

    setup_interrupt_handlers()

    configure_loggers(log_level=log_level.upper())
    logger = logging.getLogger("dagster.code_server")

    container_image = container_image or os.getenv("DAGSTER_CURRENT_IMAGE")

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
        # in the gRPC api CLI we never load more than one module or python file at a time
        module_name = check.opt_str_elem(kwargs, "module_name")
        python_file = check.opt_str_elem(kwargs, "python_file")

        loadable_target_origin = LoadableTargetOrigin(
            executable_path=sys.executable,
            attribute=kwargs["attribute"],
            working_directory=(
                None
                if kwargs.get("empty_working_directory")
                else get_working_directory_from_kwargs(kwargs)
            ),
            module_name=module_name,
            python_file=python_file,
            package_name=kwargs["package_name"],
        )

    server_termination_event = threading.Event()
    api_servicer = DagsterApiServer(
        server_termination_event=server_termination_event,
        logger=logger,
        loadable_target_origin=loadable_target_origin,
        heartbeat=heartbeat,
        heartbeat_timeout=heartbeat_timeout,
        lazy_load_user_code=lazy_load_user_code,
        fixed_server_id=fixed_server_id,
        entry_point=(
            get_python_environment_entry_point(sys.executable)
            if use_python_environment_entry_point
            else DEFAULT_DAGSTER_ENTRY_POINT
        ),
        container_image=container_image,
        container_context=(
            json.loads(container_context) if container_context is not None else None
        ),
        inject_env_vars_from_instance=inject_env_vars_from_instance,
        instance_ref=deserialize_value(instance_ref, InstanceRef) if instance_ref else None,
        location_name=location_name,
    )

    server = DagsterGrpcServer(
        server_termination_event=server_termination_event,
        dagster_api_servicer=api_servicer,
        port=port,
        socket=socket,
        host=host,
        max_workers=max_workers,
        logger=logger,
    )

    code_desc = " "
    if loadable_target_origin:
        if loadable_target_origin.python_file:
            code_desc = f" for file {loadable_target_origin.python_file} "
        elif loadable_target_origin.package_name:
            code_desc = f" for package {loadable_target_origin.package_name} "
        elif loadable_target_origin.module_name:
            code_desc = f" for module {loadable_target_origin.module_name} "

    server_desc = (
        f"Dagster code server{code_desc}on port {port} in process {os.getpid()}"
        if port
        else f"Dagster code server{code_desc}in process {os.getpid()}"
    )

    logger.info("Started %s", server_desc)

    try:
        server.serve()
    except KeyboardInterrupt:
        # Terminate cleanly on interrupt
        logger.info("Code server was interrupted")
    finally:
        logger.info("Shutting down %s", server_desc)


@api_cli.command(name="grpc-health-check", help="Check the status of a dagster GRPC server")
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
    "--use-ssl",
    is_flag=True,
    help="Whether to connect to the gRPC server over SSL",
)
def grpc_health_check_command(port=None, socket=None, host="localhost", use_ssl=False):
    if seven.IS_WINDOWS and port is None:
        raise click.UsageError(
            "You must pass a valid --port/-p on Windows: --socket/-s not supported."
        )
    if not (port or socket and not (port and socket)):
        raise click.UsageError("You must pass one and only one of --port/-p or --socket/-s.")

    client = DagsterGrpcClient(port=port, socket=socket, host=host, use_ssl=use_ssl)
    status = client.health_check_query()
    if status != "SERVING":
        click.echo(f"Unable to connect to gRPC server: {status}")
        sys.exit(1)
    else:
        click.echo("gRPC connection successful")
