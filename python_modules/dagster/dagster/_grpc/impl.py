"""Workhorse functions for individual API requests."""

import os
import sys
from contextlib import ExitStack
from typing import Generator, Optional, Sequence, Union

import pendulum

import dagster._check as check
from dagster._core.definitions import ScheduleEvaluationContext
from dagster._core.definitions.events import AssetKey
from dagster._core.definitions.reconstruct import ReconstructablePipeline
from dagster._core.definitions.repository_definition import RepositoryDefinition
from dagster._core.definitions.sensor_definition import SensorEvaluationContext
from dagster._core.errors import (
    DagsterExecutionInterruptedError,
    DagsterRunNotFoundError,
    PartitionExecutionError,
    ScheduleExecutionError,
    SensorExecutionError,
    user_code_error_boundary,
)
from dagster._core.events import DagsterEvent, EngineEventData
from dagster._core.execution.api import create_execution_plan, execute_run_iterator
from dagster._core.host_representation import external_pipeline_data_from_def
from dagster._core.host_representation.external_data import (
    ExternalPartitionConfigData,
    ExternalPartitionExecutionErrorData,
    ExternalPartitionExecutionParamData,
    ExternalPartitionNamesData,
    ExternalPartitionSetExecutionParamData,
    ExternalPartitionTagsData,
    ExternalPipelineSubsetResult,
    ExternalScheduleExecutionErrorData,
    ExternalSensorExecutionErrorData,
)
from dagster._core.instance import DagsterInstance
from dagster._core.instance.ref import InstanceRef
from dagster._core.snap.execution_plan_snapshot import (
    ExecutionPlanSnapshotErrorData,
    snapshot_from_execution_plan,
)
from dagster._core.storage.pipeline_run import PipelineRun
from dagster._grpc.types import ExecutionPlanSnapshotArgs
from dagster._serdes import deserialize_as
from dagster._serdes.ipc import IPCErrorMessage
from dagster._seven import nullcontext
from dagster._utils import start_termination_thread
from dagster._utils.error import serializable_error_info_from_exc_info
from dagster._utils.interrupts import capture_interrupts

from .types import ExecuteExternalPipelineArgs


class RunInSubprocessComplete:
    """Sentinel passed over multiprocessing Queue when subprocess is complete"""


class StartRunInSubprocessSuccessful:
    """Sentinel passed over multiprocessing Queue when launch is successful in subprocess."""


def _report_run_failed_if_not_finished(
    instance: DagsterInstance, pipeline_run_id: str
) -> Generator[DagsterEvent, None, None]:
    check.inst_param(instance, "instance", DagsterInstance)
    pipeline_run = instance.get_run_by_id(pipeline_run_id)
    if pipeline_run and (not pipeline_run.is_finished):
        yield instance.report_run_failed(pipeline_run)


def core_execute_run(
    recon_pipeline: ReconstructablePipeline,
    pipeline_run: PipelineRun,
    instance: DagsterInstance,
    inject_env_vars: bool,
    resume_from_failure: bool = False,
) -> Generator[DagsterEvent, None, None]:
    check.inst_param(recon_pipeline, "recon_pipeline", ReconstructablePipeline)
    check.inst_param(pipeline_run, "pipeline_run", PipelineRun)
    check.inst_param(instance, "instance", DagsterInstance)

    if inject_env_vars:
        try:
            location_name = (
                pipeline_run.external_pipeline_origin.location_name
                if pipeline_run.external_pipeline_origin
                else None
            )

            instance.inject_env_vars(location_name)
        except Exception:
            yield instance.report_engine_event(
                "Error while loading environment variables.",
                pipeline_run,
                EngineEventData.engine_error(serializable_error_info_from_exc_info(sys.exc_info())),
            )
            yield from _report_run_failed_if_not_finished(instance, pipeline_run.run_id)
            raise

    # try to load the pipeline definition early
    try:
        # add in cached metadata to load repository more efficiently
        if pipeline_run.has_repository_load_data:
            execution_plan_snapshot = instance.get_execution_plan_snapshot(
                check.not_none(pipeline_run.execution_plan_snapshot_id)
            )
            recon_pipeline = recon_pipeline.with_repository_load_data(
                execution_plan_snapshot.repository_load_data,
            )
        recon_pipeline.get_definition()
    except Exception:
        yield instance.report_engine_event(
            "Could not load pipeline definition.",
            pipeline_run,
            EngineEventData.engine_error(serializable_error_info_from_exc_info(sys.exc_info())),
        )
        yield from _report_run_failed_if_not_finished(instance, pipeline_run.run_id)
        raise

    # Reload the run to verify that its status didn't change while the pipeline was loaded
    dagster_run = check.not_none(
        instance.get_run_by_id(pipeline_run.run_id),
        f"Pipeline run with id '{pipeline_run.run_id}' was deleted after the run worker started.",
    )

    try:
        dagster_run = check.not_none(instance.get_run_by_id(dagster_run.run_id))
        yield from execute_run_iterator(
            recon_pipeline, pipeline_run, instance, resume_from_failure=resume_from_failure
        )
    except (KeyboardInterrupt, DagsterExecutionInterruptedError):
        yield from _report_run_failed_if_not_finished(instance, pipeline_run.run_id)
        yield instance.report_engine_event(
            message="Run execution terminated by interrupt",
            pipeline_run=pipeline_run,
        )
        raise
    except Exception:
        yield instance.report_engine_event(
            "An exception was thrown during execution that is likely a framework error, "
            "rather than an error in user code.",
            pipeline_run,
            EngineEventData.engine_error(serializable_error_info_from_exc_info(sys.exc_info())),
        )
        yield from _report_run_failed_if_not_finished(instance, pipeline_run.run_id)
        raise


def _run_in_subprocess(
    serialized_execute_run_args,
    recon_pipeline,
    termination_event,
    subprocess_status_handler,
    run_event_handler,
):

    start_termination_thread(termination_event)
    try:
        execute_run_args = deserialize_as(serialized_execute_run_args, ExecuteExternalPipelineArgs)

        with (
            DagsterInstance.from_ref(execute_run_args.instance_ref)
            if execute_run_args.instance_ref
            else nullcontext()
        ) as instance:
            instance = check.not_none(instance)
            pipeline_run = instance.get_run_by_id(execute_run_args.pipeline_run_id)

            if not pipeline_run:
                raise DagsterRunNotFoundError(
                    "gRPC server could not load run {run_id} in order to execute it. Make sure that the gRPC server has access to your run storage.".format(
                        run_id=execute_run_args.pipeline_run_id
                    ),
                    invalid_run_id=execute_run_args.pipeline_run_id,
                )

            pid = os.getpid()

    except:
        serializable_error_info = serializable_error_info_from_exc_info(sys.exc_info())
        event = IPCErrorMessage(
            serializable_error_info=serializable_error_info,
            message="Error during RPC setup for executing run: {message}".format(
                message=serializable_error_info.message
            ),
        )
        subprocess_status_handler(event)
        subprocess_status_handler(RunInSubprocessComplete())
        return

    subprocess_status_handler(StartRunInSubprocessSuccessful())

    run_event_handler(
        instance.report_engine_event(
            "Started process for run (pid: {pid}).".format(pid=pid),
            pipeline_run,
            EngineEventData.in_process(pid),
        )
    )

    # This is so nasty but seemingly unavoidable
    # https://amir.rachum.com/blog/2017/03/03/generator-cleanup/
    closed = False
    try:
        for event in core_execute_run(
            recon_pipeline, pipeline_run, instance, inject_env_vars=False
        ):
            run_event_handler(event)
    except GeneratorExit:
        closed = True
        raise
    except:
        # Relies on core_execute_run logging all exceptions to the event log before raising
        pass
    finally:
        if not closed:
            run_event_handler(
                instance.report_engine_event(
                    "Process for run exited (pid: {pid}).".format(pid=pid),
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


def get_external_pipeline_subset_result(
    repo_def: RepositoryDefinition,
    job_name: str,
    solid_selection: Optional[Sequence[str]],
    asset_selection: Optional[Sequence[AssetKey]],
):
    try:
        definition = repo_def.get_maybe_subset_job_def(
            job_name,
            op_selection=solid_selection,
            asset_selection=frozenset(asset_selection) if asset_selection else None,
        )
    except Exception:
        return ExternalPipelineSubsetResult(
            success=False, error=serializable_error_info_from_exc_info(sys.exc_info())
        )
    external_pipeline_data = external_pipeline_data_from_def(definition)
    return ExternalPipelineSubsetResult(success=True, external_pipeline_data=external_pipeline_data)


def get_external_schedule_execution(
    repo_def: RepositoryDefinition,
    instance_ref: Optional[InstanceRef],
    schedule_name: str,
    scheduled_execution_timestamp: float,
    scheduled_execution_timezone: str,
):
    schedule_def = repo_def.get_schedule_def(schedule_name)
    scheduled_execution_time = (
        pendulum.from_timestamp(
            scheduled_execution_timestamp,
            tz=scheduled_execution_timezone,
        )
        if scheduled_execution_timestamp
        else None
    )

    with ScheduleEvaluationContext(
        instance_ref, scheduled_execution_time, repo_def.name, schedule_name
    ) as schedule_context:
        try:
            with user_code_error_boundary(
                ScheduleExecutionError,
                lambda: "Error occurred during the execution function for schedule "
                "{schedule_name}".format(schedule_name=schedule_def.name),
            ):
                return schedule_def.evaluate_tick(schedule_context)
        except Exception:
            return ExternalScheduleExecutionErrorData(
                serializable_error_info_from_exc_info(sys.exc_info())
            )


def get_external_sensor_execution(
    repo_def: RepositoryDefinition,
    instance_ref: Optional[InstanceRef],
    sensor_name: str,
    last_completion_timestamp: Optional[float],
    last_run_key: Optional[str],
    cursor: Optional[str],
):
    sensor_def = repo_def.get_sensor_def(sensor_name)

    with ExitStack() as stack:
        sensor_context = stack.enter_context(
            SensorEvaluationContext(
                instance_ref,
                last_completion_time=last_completion_timestamp,
                last_run_key=last_run_key,
                cursor=cursor,
                repository_name=repo_def.name,
                repository_def=repo_def,
                sensor_name=sensor_name,
            )
        )

        try:
            with user_code_error_boundary(
                SensorExecutionError,
                lambda: "Error occurred during the execution of evaluation_fn for sensor "
                "{sensor_name}".format(sensor_name=sensor_def.name),
            ):
                return sensor_def.evaluate_tick(sensor_context)
        except Exception:
            return ExternalSensorExecutionErrorData(
                serializable_error_info_from_exc_info(sys.exc_info())
            )


def get_partition_config(
    repo_def: RepositoryDefinition,
    partition_set_name: str,
    partition_name: str,
):

    partition_set_def = repo_def.get_partition_set_def(partition_set_name)
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
    except Exception:
        return ExternalPartitionExecutionErrorData(
            serializable_error_info_from_exc_info(sys.exc_info())
        )


def _get_target_for_partition_execution_error(partition_set_def):
    if partition_set_def.job_name:
        return f"partitioned config on job '{partition_set_def.job_name}'"
    else:
        return f"partition set '{partition_set_def.name}'"


def get_partition_names(
    repo_def: RepositoryDefinition,
    partition_set_name: str,
):
    partition_set_def = repo_def.get_partition_set_def(partition_set_name)
    try:
        with user_code_error_boundary(
            PartitionExecutionError,
            lambda: f"Error occurred during the execution of the partition generation function for "
            f"{_get_target_for_partition_execution_error(partition_set_def)}",
        ):
            return ExternalPartitionNamesData(
                partition_names=partition_set_def.get_partition_names()
            )
    except Exception:
        return ExternalPartitionExecutionErrorData(
            serializable_error_info_from_exc_info(sys.exc_info())
        )


def get_partition_tags(
    repo_def: RepositoryDefinition,
    partition_set_name: str,
    partition_name: str,
):
    partition_set_def = repo_def.get_partition_set_def(partition_set_name)
    partition = partition_set_def.get_partition(partition_name)
    try:
        with user_code_error_boundary(
            PartitionExecutionError,
            lambda: "Error occurred during the evaluation of the `tags_for_partition` function for "
            f"{_get_target_for_partition_execution_error(partition_set_def)}",
        ):
            tags = partition_set_def.tags_for_partition(partition)
            return ExternalPartitionTagsData(name=partition.name, tags=tags)
    except Exception:
        return ExternalPartitionExecutionErrorData(
            serializable_error_info_from_exc_info(sys.exc_info())
        )


def get_external_execution_plan_snapshot(
    repo_def: RepositoryDefinition,
    job_name: str,
    args: ExecutionPlanSnapshotArgs,
):
    try:
        job_def = repo_def.get_maybe_subset_job_def(
            job_name,
            op_selection=args.solid_selection,
            asset_selection=args.asset_selection,
        )

        return snapshot_from_execution_plan(
            create_execution_plan(
                job_def,
                run_config=args.run_config,
                mode=args.mode,
                step_keys_to_execute=args.step_keys_to_execute,
                known_state=args.known_state,
                instance_ref=args.instance_ref,
                repository_load_data=repo_def.repository_load_data,
            ),
            args.pipeline_snapshot_id,
        )
    except:
        return ExecutionPlanSnapshotErrorData(
            error=serializable_error_info_from_exc_info(sys.exc_info())
        )


def get_partition_set_execution_param_data(
    repo_definition: RepositoryDefinition,
    partition_set_name: str,
    partition_names: Sequence[str],
) -> Union[ExternalPartitionSetExecutionParamData, ExternalPartitionExecutionErrorData]:
    partition_set_def = repo_definition.get_partition_set_def(partition_set_name)
    try:
        with user_code_error_boundary(
            PartitionExecutionError,
            lambda: "Error occurred during the partition generation for "
            f"{_get_target_for_partition_execution_error(partition_set_def)}",
        ):
            all_partitions = partition_set_def.get_partitions()
        partitions = [
            partition for partition in all_partitions if partition.name in partition_names
        ]

        partition_data = []
        for partition in partitions:

            def _error_message_fn(partition_name):
                return lambda: (
                    "Error occurred during the partition config and tag generation for "
                    f"'{partition_name}' in {_get_target_for_partition_execution_error(partition_set_def)}"
                )

            with user_code_error_boundary(
                PartitionExecutionError, _error_message_fn(partition.name)
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

    except Exception:
        return ExternalPartitionExecutionErrorData(
            serializable_error_info_from_exc_info(sys.exc_info())
        )


def get_notebook_data(notebook_path):
    check.str_param(notebook_path, "notebook_path")

    if not notebook_path.endswith(".ipynb"):
        raise Exception(
            "unexpected file extension for notebooks. Please provide a path that ends with '.ipynb'."
        )

    with open(os.path.abspath(notebook_path), "rb") as f:
        content = f.read()
        return content
