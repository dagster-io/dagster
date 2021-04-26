"""Workhorse functions for individual API requests."""

import os
import sys

import pendulum
from dagster import check
from dagster.core.definitions import ScheduleExecutionContext
from dagster.core.definitions.reconstructable import (
    ReconstructablePipeline,
    ReconstructableRepository,
)
from dagster.core.definitions.sensor import SensorExecutionContext
from dagster.core.errors import (
    DagsterExecutionInterruptedError,
    DagsterInvalidSubsetError,
    DagsterRunNotFoundError,
    PartitionExecutionError,
    ScheduleExecutionError,
    SensorExecutionError,
    user_code_error_boundary,
)
from dagster.core.events import EngineEventData
from dagster.core.execution.api import create_execution_plan, execute_run_iterator
from dagster.core.host_representation import external_pipeline_data_from_def
from dagster.core.host_representation.external_data import (
    ExternalPartitionConfigData,
    ExternalPartitionExecutionErrorData,
    ExternalPartitionExecutionParamData,
    ExternalPartitionNamesData,
    ExternalPartitionSetExecutionParamData,
    ExternalPartitionTagsData,
    ExternalPipelineSubsetResult,
    ExternalScheduleExecutionData,
    ExternalScheduleExecutionErrorData,
    ExternalSensorExecutionData,
    ExternalSensorExecutionErrorData,
)
from dagster.core.instance import DagsterInstance
from dagster.core.snap.execution_plan_snapshot import (
    ExecutionPlanSnapshotErrorData,
    snapshot_from_execution_plan,
)
from dagster.core.storage.pipeline_run import PipelineRun
from dagster.grpc.types import ExecutionPlanSnapshotArgs
from dagster.serdes import deserialize_json_to_dagster_namedtuple
from dagster.serdes.ipc import IPCErrorMessage
from dagster.utils import start_termination_thread
from dagster.utils.error import serializable_error_info_from_exc_info
from dagster.utils.interrupts import capture_interrupts

from .types import ExecuteExternalPipelineArgs


class RunInSubprocessComplete:
    """Sentinel passed over multiprocessing Queue when subprocess is complete"""


class StartRunInSubprocessSuccessful:
    """Sentinel passed over multiprocessing Queue when launch is successful in subprocess."""


def _report_run_failed_if_not_finished(instance, pipeline_run_id):
    check.inst_param(instance, "instance", DagsterInstance)
    pipeline_run = instance.get_run_by_id(pipeline_run_id)
    if pipeline_run and (not pipeline_run.is_finished):
        yield instance.report_run_failed(pipeline_run)


def core_execute_run(recon_pipeline, pipeline_run, instance):
    check.inst_param(recon_pipeline, "recon_pipeline", ReconstructablePipeline)
    check.inst_param(pipeline_run, "pipeline_run", PipelineRun)
    check.inst_param(instance, "instance", DagsterInstance)

    # try to load the pipeline definition early
    try:
        recon_pipeline.get_definition()
    except Exception:  # pylint: disable=broad-except
        yield instance.report_engine_event(
            "Could not load pipeline definition.",
            pipeline_run,
            EngineEventData.engine_error(serializable_error_info_from_exc_info(sys.exc_info())),
        )
        yield from _report_run_failed_if_not_finished(instance, pipeline_run.run_id)
        return

    try:
        yield from execute_run_iterator(recon_pipeline, pipeline_run, instance)
    except (KeyboardInterrupt, DagsterExecutionInterruptedError):
        yield from _report_run_failed_if_not_finished(instance, pipeline_run.run_id)
        yield instance.report_engine_event(
            message="Pipeline execution terminated by interrupt",
            pipeline_run=pipeline_run,
        )
    except Exception:  # pylint: disable=broad-except
        yield instance.report_engine_event(
            "An exception was thrown during execution that is likely a framework error, "
            "rather than an error in user code.",
            pipeline_run,
            EngineEventData.engine_error(serializable_error_info_from_exc_info(sys.exc_info())),
        )
        yield from _report_run_failed_if_not_finished(instance, pipeline_run.run_id)


def _run_in_subprocess(
    serialized_execute_run_args,
    recon_pipeline,
    termination_event,
    subprocess_status_handler,
    run_event_handler,
):

    start_termination_thread(termination_event)
    try:
        execute_run_args = deserialize_json_to_dagster_namedtuple(serialized_execute_run_args)
        check.inst_param(execute_run_args, "execute_run_args", ExecuteExternalPipelineArgs)

        instance = DagsterInstance.from_ref(execute_run_args.instance_ref)
        pipeline_run = instance.get_run_by_id(execute_run_args.pipeline_run_id)

        if not pipeline_run:
            raise DagsterRunNotFoundError(
                "gRPC server could not load run {run_id} in order to execute it. Make sure that the gRPC server has access to your run storage.".format(
                    run_id=execute_run_args.pipeline_run_id
                ),
                invalid_run_id=execute_run_args.pipeline_run_id,
            )

        pid = os.getpid()

    except:  # pylint: disable=bare-except
        serializable_error_info = serializable_error_info_from_exc_info(sys.exc_info())
        event = IPCErrorMessage(
            serializable_error_info=serializable_error_info,
            message="Error during RPC setup for executing run: {message}".format(
                message=serializable_error_info.message
            ),
        )
        subprocess_status_handler(event)
        subprocess_status_handler(RunInSubprocessComplete())
        if instance:
            instance.dispose()
        return

    subprocess_status_handler(StartRunInSubprocessSuccessful())

    run_event_handler(
        instance.report_engine_event(
            "Started process for pipeline (pid: {pid}).".format(pid=pid),
            pipeline_run,
            EngineEventData.in_process(pid, marker_end="cli_api_subprocess_init"),
        )
    )

    # This is so nasty but seemingly unavoidable
    # https://amir.rachum.com/blog/2017/03/03/generator-cleanup/
    closed = False
    try:
        for event in core_execute_run(recon_pipeline, pipeline_run, instance):
            run_event_handler(event)
    except GeneratorExit:
        closed = True
        raise
    finally:
        if not closed:
            run_event_handler(
                instance.report_engine_event(
                    "Process for pipeline exited (pid: {pid}).".format(pid=pid),
                    pipeline_run,
                )
            )
        subprocess_status_handler(RunInSubprocessComplete())
        instance.dispose()


def start_run_in_subprocess(
    serialized_execute_run_args, recon_pipeline, event_queue, termination_event
):
    with capture_interrupts():
        _run_in_subprocess(
            serialized_execute_run_args,
            recon_pipeline,
            termination_event,
            subprocess_status_handler=event_queue.put,
            run_event_handler=lambda x: None,
        )


def get_external_pipeline_subset_result(recon_pipeline, solid_selection):
    check.inst_param(recon_pipeline, "recon_pipeline", ReconstructablePipeline)

    if solid_selection:
        try:
            sub_pipeline = recon_pipeline.subset_for_execution(solid_selection)
            definition = sub_pipeline.get_definition()
        except DagsterInvalidSubsetError:
            return ExternalPipelineSubsetResult(
                success=False, error=serializable_error_info_from_exc_info(sys.exc_info())
            )
    else:
        definition = recon_pipeline.get_definition()

    external_pipeline_data = external_pipeline_data_from_def(definition)
    return ExternalPipelineSubsetResult(success=True, external_pipeline_data=external_pipeline_data)


def get_external_schedule_execution(
    recon_repo,
    instance_ref,
    schedule_name,
    scheduled_execution_timestamp,
    scheduled_execution_timezone,
):
    check.inst_param(
        recon_repo,
        "recon_repo",
        ReconstructableRepository,
    )
    definition = recon_repo.get_definition()
    schedule_def = definition.get_schedule_def(schedule_name)
    scheduled_execution_time = (
        pendulum.from_timestamp(
            scheduled_execution_timestamp,
            tz=scheduled_execution_timezone,
        )
        if scheduled_execution_timestamp
        else None
    )

    with ScheduleExecutionContext(instance_ref, scheduled_execution_time) as schedule_context:
        try:
            with user_code_error_boundary(
                ScheduleExecutionError,
                lambda: "Error occurred during the execution function for schedule "
                "{schedule_name}".format(schedule_name=schedule_def.name),
            ):
                return ExternalScheduleExecutionData.from_execution_data(
                    schedule_def.get_execution_data(schedule_context)
                )
        except ScheduleExecutionError:
            return ExternalScheduleExecutionErrorData(
                serializable_error_info_from_exc_info(sys.exc_info())
            )


def get_external_sensor_execution(
    recon_repo, instance_ref, sensor_name, last_completion_timestamp, last_run_key
):
    check.inst_param(
        recon_repo,
        "recon_repo",
        ReconstructableRepository,
    )

    definition = recon_repo.get_definition()
    sensor_def = definition.get_sensor_def(sensor_name)

    with SensorExecutionContext(
        instance_ref, last_completion_time=last_completion_timestamp, last_run_key=last_run_key
    ) as sensor_context:
        try:
            with user_code_error_boundary(
                SensorExecutionError,
                lambda: "Error occurred during the execution of evaluation_fn for sensor "
                "{sensor_name}".format(sensor_name=sensor_def.name),
            ):
                return ExternalSensorExecutionData.from_execution_data(
                    sensor_def.get_execution_data(sensor_context)
                )
        except SensorExecutionError:
            return ExternalSensorExecutionErrorData(
                serializable_error_info_from_exc_info(sys.exc_info())
            )


def get_partition_config(recon_repo, partition_set_name, partition_name):
    definition = recon_repo.get_definition()
    partition_set_def = definition.get_partition_set_def(partition_set_name)
    partition = partition_set_def.get_partition(partition_name)
    try:
        with user_code_error_boundary(
            PartitionExecutionError,
            lambda: "Error occurred during the evaluation of the `run_config_for_partition` "
            "function for partition set {partition_set_name}".format(
                partition_set_name=partition_set_def.name
            ),
        ):
            run_config = partition_set_def.run_config_for_partition(partition)
            return ExternalPartitionConfigData(name=partition.name, run_config=run_config)
    except PartitionExecutionError:
        return ExternalPartitionExecutionErrorData(
            serializable_error_info_from_exc_info(sys.exc_info())
        )


def get_partition_names(recon_repo, partition_set_name):
    definition = recon_repo.get_definition()
    partition_set_def = definition.get_partition_set_def(partition_set_name)
    try:
        with user_code_error_boundary(
            PartitionExecutionError,
            lambda: "Error occurred during the execution of the partition generation function for "
            "partition set {partition_set_name}".format(partition_set_name=partition_set_def.name),
        ):
            return ExternalPartitionNamesData(
                partition_names=partition_set_def.get_partition_names()
            )
    except PartitionExecutionError:
        return ExternalPartitionExecutionErrorData(
            serializable_error_info_from_exc_info(sys.exc_info())
        )


def get_partition_tags(recon_repo, partition_set_name, partition_name):
    definition = recon_repo.get_definition()
    partition_set_def = definition.get_partition_set_def(partition_set_name)
    partition = partition_set_def.get_partition(partition_name)
    try:
        with user_code_error_boundary(
            PartitionExecutionError,
            lambda: "Error occurred during the evaluation of the `tags_for_partition` function for "
            "partition set {partition_set_name}".format(partition_set_name=partition_set_def.name),
        ):
            tags = partition_set_def.tags_for_partition(partition)
            return ExternalPartitionTagsData(name=partition.name, tags=tags)
    except PartitionExecutionError:
        return ExternalPartitionExecutionErrorData(
            serializable_error_info_from_exc_info(sys.exc_info())
        )


def get_external_execution_plan_snapshot(recon_pipeline, args):
    check.inst_param(recon_pipeline, "recon_pipeline", ReconstructablePipeline)
    check.inst_param(args, "args", ExecutionPlanSnapshotArgs)

    try:
        pipeline = (
            recon_pipeline.subset_for_execution(args.solid_selection)
            if args.solid_selection
            else recon_pipeline
        )

        return snapshot_from_execution_plan(
            create_execution_plan(
                pipeline=pipeline,
                run_config=args.run_config,
                mode=args.mode,
                step_keys_to_execute=args.step_keys_to_execute,
                known_state=args.known_state,
            ),
            args.pipeline_snapshot_id,
        )
    except:  # pylint: disable=bare-except
        return ExecutionPlanSnapshotErrorData(
            error=serializable_error_info_from_exc_info(sys.exc_info())
        )


def get_partition_set_execution_param_data(recon_repo, partition_set_name, partition_names):
    repo_definition = recon_repo.get_definition()
    partition_set_def = repo_definition.get_partition_set_def(partition_set_name)
    try:
        with user_code_error_boundary(
            PartitionExecutionError,
            lambda: "Error occurred during the partition generation for partition set "
            "{partition_set_name}".format(partition_set_name=partition_set_def.name),
        ):
            all_partitions = partition_set_def.get_partitions()
        partitions = [
            partition for partition in all_partitions if partition.name in partition_names
        ]

        partition_data = []
        for partition in partitions:

            def _error_message_fn(partition_set_name, partition_name):
                return lambda: (
                    "Error occurred during the partition config and tag generation for "
                    "partition set {partition_set_name}::{partition_name}".format(
                        partition_set_name=partition_set_name, partition_name=partition_name
                    )
                )

            with user_code_error_boundary(
                PartitionExecutionError, _error_message_fn(partition_set_def.name, partition.name)
            ):
                run_config = partition_set_def.run_config_for_partition(partition)
                tags = partition_set_def.tags_for_partition(partition)

            partition_data.append(
                ExternalPartitionExecutionParamData(
                    name=partition.name,
                    tags=tags,
                    run_config=run_config,
                )
            )

        return ExternalPartitionSetExecutionParamData(partition_data=partition_data)

    except PartitionExecutionError:
        return ExternalPartitionExecutionErrorData(
            serializable_error_info_from_exc_info(sys.exc_info())
        )
