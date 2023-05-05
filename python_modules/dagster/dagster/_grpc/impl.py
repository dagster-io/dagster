"""Workhorse functions for individual API requests."""

import os
import sys
from contextlib import contextmanager
from typing import Any, Generator, Iterator, Optional, Sequence, Tuple, Union

import pendulum

import dagster._check as check
from dagster._core.definitions import ScheduleEvaluationContext
from dagster._core.definitions.events import AssetKey
from dagster._core.definitions.job_definition import JobDefinition
from dagster._core.definitions.multi_dimensional_partitions import MultiPartitionsDefinition
from dagster._core.definitions.partition import (
    DynamicPartitionsDefinition,
    PartitionedConfig,
    PartitionsDefinition,
)
from dagster._core.definitions.reconstruct import ReconstructableJob
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
from dagster._core.host_representation import external_job_data_from_def
from dagster._core.host_representation.external_data import (
    ExternalJobSubsetResult,
    ExternalPartitionConfigData,
    ExternalPartitionExecutionErrorData,
    ExternalPartitionExecutionParamData,
    ExternalPartitionNamesData,
    ExternalPartitionSetExecutionParamData,
    ExternalPartitionTagsData,
    ExternalScheduleExecutionErrorData,
    ExternalSensorExecutionErrorData,
    job_name_for_external_partition_set_name,
)
from dagster._core.instance import DagsterInstance
from dagster._core.instance.ref import InstanceRef
from dagster._core.snap.execution_plan_snapshot import (
    ExecutionPlanSnapshotErrorData,
    snapshot_from_execution_plan,
)
from dagster._core.storage.dagster_run import DagsterRun
from dagster._grpc.types import ExecutionPlanSnapshotArgs
from dagster._serdes import deserialize_value
from dagster._serdes.ipc import IPCErrorMessage
from dagster._seven import nullcontext
from dagster._utils import start_termination_thread
from dagster._utils.error import serializable_error_info_from_exc_info
from dagster._utils.interrupts import capture_interrupts

from .types import ExecuteExternalJobArgs


class RunInSubprocessComplete:
    """Sentinel passed over multiprocessing Queue when subprocess is complete."""


class StartRunInSubprocessSuccessful:
    """Sentinel passed over multiprocessing Queue when launch is successful in subprocess."""


def _report_run_failed_if_not_finished(
    instance: DagsterInstance, pipeline_run_id: str
) -> Generator[DagsterEvent, None, None]:
    check.inst_param(instance, "instance", DagsterInstance)
    dagster_run = instance.get_run_by_id(pipeline_run_id)
    if dagster_run and (not dagster_run.is_finished):
        yield instance.report_run_failed(dagster_run)


def core_execute_run(
    recon_job: ReconstructableJob,
    dagster_run: DagsterRun,
    instance: DagsterInstance,
    inject_env_vars: bool,
    resume_from_failure: bool = False,
) -> Generator[DagsterEvent, None, None]:
    check.inst_param(recon_job, "recon_job", ReconstructableJob)
    check.inst_param(dagster_run, "pipeline_run", DagsterRun)
    check.inst_param(instance, "instance", DagsterInstance)

    if inject_env_vars:
        try:
            location_name = (
                dagster_run.external_job_origin.location_name
                if dagster_run.external_job_origin
                else None
            )

            instance.inject_env_vars(location_name)
        except Exception:
            yield instance.report_engine_event(
                "Error while loading environment variables.",
                dagster_run,
                EngineEventData.engine_error(serializable_error_info_from_exc_info(sys.exc_info())),
            )
            yield from _report_run_failed_if_not_finished(instance, dagster_run.run_id)
            raise

    # try to load the pipeline definition early
    try:
        # add in cached metadata to load repository more efficiently
        if dagster_run.has_repository_load_data:
            execution_plan_snapshot = instance.get_execution_plan_snapshot(
                check.not_none(dagster_run.execution_plan_snapshot_id)
            )
            recon_job = recon_job.with_repository_load_data(
                execution_plan_snapshot.repository_load_data,
            )
        recon_job.get_definition()
    except Exception:
        yield instance.report_engine_event(
            "Could not load pipeline definition.",
            dagster_run,
            EngineEventData.engine_error(serializable_error_info_from_exc_info(sys.exc_info())),
        )
        yield from _report_run_failed_if_not_finished(instance, dagster_run.run_id)
        raise

    # Reload the run to verify that its status didn't change while the pipeline was loaded
    dagster_run = check.not_none(
        instance.get_run_by_id(dagster_run.run_id),
        f"Pipeline run with id '{dagster_run.run_id}' was deleted after the run worker started.",
    )

    try:
        yield from execute_run_iterator(
            recon_job, dagster_run, instance, resume_from_failure=resume_from_failure
        )
    except (KeyboardInterrupt, DagsterExecutionInterruptedError):
        yield from _report_run_failed_if_not_finished(instance, dagster_run.run_id)
        yield instance.report_engine_event(
            message="Run execution terminated by interrupt",
            dagster_run=dagster_run,
        )
        raise
    except Exception:
        yield instance.report_engine_event(
            (
                "An exception was thrown during execution that is likely a framework error, "
                "rather than an error in user code."
            ),
            dagster_run,
            EngineEventData.engine_error(serializable_error_info_from_exc_info(sys.exc_info())),
        )
        yield from _report_run_failed_if_not_finished(instance, dagster_run.run_id)
        raise


@contextmanager
def _instance_from_ref_for_dynamic_partitions(
    instance_ref: Optional[InstanceRef], partitions_def: PartitionsDefinition
) -> Iterator[Optional[DagsterInstance]]:
    # Certain gRPC servers do not have access to the instance, so we only attempt to instantiate
    # the instance when necessary for dynamic partitions: https://github.com/dagster-io/dagster/issues/12440

    with DagsterInstance.from_ref(instance_ref) if (
        instance_ref and (_partitions_def_contains_dynamic_partitions_def(partitions_def))
    ) else nullcontext() as instance:
        yield instance


def _run_in_subprocess(
    serialized_execute_run_args: str,
    recon_pipeline: ReconstructableJob,
    termination_event: Any,
    subprocess_status_handler,
    run_event_handler,
) -> None:
    start_termination_thread(termination_event)
    try:
        execute_run_args = deserialize_value(serialized_execute_run_args, ExecuteExternalJobArgs)

        with (
            DagsterInstance.from_ref(execute_run_args.instance_ref)
            if execute_run_args.instance_ref
            else nullcontext()
        ) as instance:
            instance = check.not_none(instance)  # noqa: PLW2901
            dagster_run = instance.get_run_by_id(execute_run_args.run_id)

            if not dagster_run:
                raise DagsterRunNotFoundError(
                    "gRPC server could not load run {run_id} in order to execute it. Make sure that"
                    " the gRPC server has access to your run storage.".format(
                        run_id=execute_run_args.run_id
                    ),
                    invalid_run_id=execute_run_args.run_id,
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
            f"Started process for run (pid: {pid}).",
            dagster_run,
            EngineEventData.in_process(pid),
        )
    )

    # This is so nasty but seemingly unavoidable
    # https://amir.rachum.com/blog/2017/03/03/generator-cleanup/
    closed = False
    try:
        for event in core_execute_run(recon_pipeline, dagster_run, instance, inject_env_vars=False):
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
                    f"Process for run exited (pid: {pid}).",
                    dagster_run,
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
        external_job_data = external_job_data_from_def(definition)
        return ExternalJobSubsetResult(success=True, external_job_data=external_job_data)
    except Exception:
        return ExternalJobSubsetResult(
            success=False, error=serializable_error_info_from_exc_info(sys.exc_info())
        )


def get_external_schedule_execution(
    repo_def: RepositoryDefinition,
    instance_ref: Optional[InstanceRef],
    schedule_name: str,
    scheduled_execution_timestamp: Optional[float],
    scheduled_execution_timezone: Optional[str],
):
    from dagster._core.execution.resources_init import get_transitive_required_resource_keys

    try:
        schedule_def = repo_def.get_schedule_def(schedule_name)
        scheduled_execution_time = (
            pendulum.from_timestamp(
                scheduled_execution_timestamp,
                tz=check.not_none(scheduled_execution_timezone),
            )
            if scheduled_execution_timestamp
            else None
        )

        required_resource_keys = get_transitive_required_resource_keys(
            schedule_def.required_resource_keys, repo_def.get_top_level_resources()
        )
        resources_to_build = {
            k: v
            for k, v in repo_def.get_top_level_resources().items()
            if k in required_resource_keys
        }
        with ScheduleEvaluationContext(
            instance_ref,
            scheduled_execution_time,
            repo_def.name,
            schedule_name,
            resources=resources_to_build,
            repository_def=repo_def,
        ) as schedule_context:
            with user_code_error_boundary(
                ScheduleExecutionError,
                lambda: "Error occurred during the execution function for schedule {schedule_name}".format(
                    schedule_name=schedule_def.name
                ),
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
    from dagster._core.execution.resources_init import get_transitive_required_resource_keys

    try:
        sensor_def = repo_def.get_sensor_def(sensor_name)

        required_resource_keys = get_transitive_required_resource_keys(
            sensor_def.required_resource_keys, repo_def.get_top_level_resources()
        )
        resources_to_build = {
            k: v
            for k, v in repo_def.get_top_level_resources().items()
            if k in required_resource_keys
        }

        with SensorEvaluationContext(
            instance_ref,
            last_completion_time=last_completion_timestamp,
            last_run_key=last_run_key,
            cursor=cursor,
            repository_name=repo_def.name,
            repository_def=repo_def,
            sensor_name=sensor_name,
            resources=resources_to_build,
        ) as sensor_context:
            with user_code_error_boundary(
                SensorExecutionError,
                lambda: "Error occurred during the execution of evaluation_fn for sensor {sensor_name}".format(
                    sensor_name=sensor_def.name
                ),
            ):
                return sensor_def.evaluate_tick(sensor_context)
    except Exception:
        return ExternalSensorExecutionErrorData(
            serializable_error_info_from_exc_info(sys.exc_info())
        )


def _partitions_def_contains_dynamic_partitions_def(partitions_def: PartitionsDefinition) -> bool:
    if isinstance(partitions_def, DynamicPartitionsDefinition):
        return True
    if isinstance(partitions_def, MultiPartitionsDefinition):
        return any(
            _partitions_def_contains_dynamic_partitions_def(dimension.partitions_def)
            for dimension in partitions_def.partitions_defs
        )
    return False


def _get_job_partitions_and_config_for_partition_set_name(
    repo_def: RepositoryDefinition,
    partition_set_name: str,
) -> Tuple[JobDefinition, PartitionsDefinition, PartitionedConfig]:
    job_name = job_name_for_external_partition_set_name(partition_set_name)
    job_def = repo_def.get_job(job_name)
    assert job_def.partitions_def and job_def.partitioned_config, (
        f"Job {job_def.name} corresponding to external partition set {partition_set_name} does not"
        " have a partitions_def"
    )
    return job_def, job_def.partitions_def, job_def.partitioned_config


def get_partition_config(
    repo_def: RepositoryDefinition,
    partition_set_name: str,
    partition_key: str,
    instance_ref: Optional[InstanceRef] = None,
) -> Union[ExternalPartitionConfigData, ExternalPartitionExecutionErrorData]:
    try:
        (
            _,
            partitions_def,
            partitioned_config,
        ) = _get_job_partitions_and_config_for_partition_set_name(repo_def, partition_set_name)

        with _instance_from_ref_for_dynamic_partitions(instance_ref, partitions_def) as instance:
            with user_code_error_boundary(
                PartitionExecutionError,
                lambda: f"Error occurred during the evaluation of the `run_config_for_partition` function for partition set {partition_set_name}",
            ):
                partitions_def.validate_partition_key(
                    partition_key, dynamic_partitions_store=instance
                )
                run_config = partitioned_config.get_run_config_for_partition_key(partition_key)
                return ExternalPartitionConfigData(name=partition_key, run_config=run_config)
    except Exception:
        return ExternalPartitionExecutionErrorData(
            serializable_error_info_from_exc_info(sys.exc_info())
        )


def get_partition_names(
    repo_def: RepositoryDefinition,
    partition_set_name: str,
) -> Union[ExternalPartitionNamesData, ExternalPartitionExecutionErrorData]:
    try:
        (
            job_def,
            partitions_def,
            _,
        ) = _get_job_partitions_and_config_for_partition_set_name(repo_def, partition_set_name)

        with user_code_error_boundary(
            PartitionExecutionError,
            lambda: f"Error occurred during the execution of the partition generation function for partitioned config on job '{job_def.name}'",
        ):
            return ExternalPartitionNamesData(partition_names=partitions_def.get_partition_keys())
    except Exception:
        return ExternalPartitionExecutionErrorData(
            serializable_error_info_from_exc_info(sys.exc_info())
        )


def get_partition_tags(
    repo_def: RepositoryDefinition,
    partition_set_name: str,
    partition_name: str,
    instance_ref: Optional[InstanceRef] = None,
):
    try:
        (
            job_def,
            partitions_def,
            partitioned_config,
        ) = _get_job_partitions_and_config_for_partition_set_name(repo_def, partition_set_name)

        # Certain gRPC servers do not have access to the instance, so we only attempt to instantiate
        # the instance when necessary for dynamic partitions: https://github.com/dagster-io/dagster/issues/12440

        with _instance_from_ref_for_dynamic_partitions(instance_ref, partitions_def) as instance:
            with user_code_error_boundary(
                PartitionExecutionError,
                lambda: f"Error occurred during the evaluation of the `tags_for_partition` function for partitioned config on job '{job_def.name}'",
            ):
                partitions_def.validate_partition_key(
                    partition_name, dynamic_partitions_store=instance
                )
                tags = partitioned_config.get_tags_for_partition_key(
                    partition_name, job_name=job_def.name
                )
                return ExternalPartitionTagsData(name=partition_name, tags=tags)

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
                step_keys_to_execute=args.step_keys_to_execute,
                known_state=args.known_state,
                instance_ref=args.instance_ref,
                repository_load_data=repo_def.repository_load_data,
            ),
            args.job_snapshot_id,
        )
    except:
        return ExecutionPlanSnapshotErrorData(
            error=serializable_error_info_from_exc_info(sys.exc_info())
        )


def get_partition_set_execution_param_data(
    repo_def: RepositoryDefinition,
    partition_set_name: str,
    partition_names: Sequence[str],
    instance_ref: Optional[InstanceRef] = None,
) -> Union[ExternalPartitionSetExecutionParamData, ExternalPartitionExecutionErrorData]:
    (
        job_def,
        partitions_def,
        partitioned_config,
    ) = _get_job_partitions_and_config_for_partition_set_name(repo_def, partition_set_name)

    try:
        with _instance_from_ref_for_dynamic_partitions(instance_ref, partitions_def) as instance:
            with user_code_error_boundary(
                PartitionExecutionError,
                lambda: f"Error occurred during the partition generation for partitioned config on job '{job_def.name}'",
            ):
                all_partition_keys = partitions_def.get_partition_keys(
                    dynamic_partitions_store=instance
                )
                partition_keys = [key for key in all_partition_keys if key in partition_names]

            partition_data = []
            for key in partition_keys:

                def _error_message_fn(partition_name: str):
                    return (
                        lambda: f"Error occurred during the partition config and tag generation for '{partition_name}' in partitioned config on job '{job_def.name}'"
                    )

                with user_code_error_boundary(PartitionExecutionError, _error_message_fn(key)):
                    run_config = partitioned_config.get_run_config_for_partition_key(key)
                    tags = partitioned_config.get_tags_for_partition_key(key, job_name=job_def.name)

                partition_data.append(
                    ExternalPartitionExecutionParamData(
                        name=key,
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
            "unexpected file extension for notebooks. Please provide a path that ends with"
            " '.ipynb'."
        )

    with open(os.path.abspath(notebook_path), "rb") as f:
        content = f.read()
        return content
