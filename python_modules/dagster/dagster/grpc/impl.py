"""Workhorse functions for individual API requests."""

import os
import sys

import pendulum

from dagster import check
from dagster.core.definitions import JobContext, ScheduleExecutionContext
from dagster.core.definitions.reconstructable import (
    ReconstructablePipeline,
    ReconstructableRepository,
)
from dagster.core.errors import (
    DagsterInvalidSubsetError,
    DagsterRunNotFoundError,
    DagsterSubprocessError,
    JobError,
    PartitionExecutionError,
    ScheduleExecutionError,
    user_code_error_boundary,
)
from dagster.core.events import EngineEventData
from dagster.core.execution.api import create_execution_plan, execute_run_iterator
from dagster.core.host_representation import external_pipeline_data_from_def
from dagster.core.host_representation.external_data import (
    ExternalExecutionParamsData,
    ExternalExecutionParamsErrorData,
    ExternalPartitionConfigData,
    ExternalPartitionExecutionErrorData,
    ExternalPartitionExecutionParamData,
    ExternalPartitionNamesData,
    ExternalPartitionSetExecutionParamData,
    ExternalPartitionTagsData,
    ExternalPipelineSubsetResult,
    ExternalScheduleExecutionData,
    ExternalScheduleExecutionErrorData,
)
from dagster.core.instance import DagsterInstance
from dagster.core.snap.execution_plan_snapshot import (
    ExecutionPlanSnapshotErrorData,
    snapshot_from_execution_plan,
)
from dagster.core.storage.pipeline_run import PipelineRun
from dagster.grpc.types import (
    ExecutionPlanSnapshotArgs,
    ExternalJobArgs,
    ExternalScheduleExecutionArgs,
    PartitionArgs,
    PartitionNamesArgs,
    ScheduleExecutionDataMode,
)
from dagster.serdes import deserialize_json_to_dagster_namedtuple
from dagster.serdes.ipc import IPCErrorMessage
from dagster.utils import delay_interrupts, start_termination_thread
from dagster.utils.error import serializable_error_info_from_exc_info
from dagster.utils.hosted_user_process import recon_repository_from_origin

from .types import ExecuteRunArgs, ExternalScheduleExecutionArgs, PartitionSetExecutionParamArgs


class RunInSubprocessComplete:
    """Sentinel passed over multiprocessing Queue when subprocess is complete"""


class StartRunInSubprocessSuccessful:
    """Sentinel passed over multiprocessing Queue when launch is successful in subprocess."""


def _core_execute_run(recon_pipeline, pipeline_run, instance):
    check.inst_param(recon_pipeline, "recon_pipeline", ReconstructablePipeline)
    check.inst_param(pipeline_run, "pipeline_run", PipelineRun)
    check.inst_param(instance, "instance", DagsterInstance)

    try:
        for event in execute_run_iterator(recon_pipeline, pipeline_run, instance):
            yield event
    except DagsterSubprocessError as err:
        if not all(
            [err_info.cls_name == "KeyboardInterrupt" for err_info in err.subprocess_error_infos]
        ):
            yield instance.report_engine_event(
                "An exception was thrown during execution that is likely a framework error, "
                "rather than an error in user code.",
                pipeline_run,
                EngineEventData.engine_error(serializable_error_info_from_exc_info(sys.exc_info())),
            )
            instance.report_run_failed(pipeline_run)
    except Exception:  # pylint: disable=broad-except
        yield instance.report_engine_event(
            "An exception was thrown during execution that is likely a framework error, "
            "rather than an error in user code.",
            pipeline_run,
            EngineEventData.engine_error(serializable_error_info_from_exc_info(sys.exc_info())),
        )
        instance.report_run_failed(pipeline_run)


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
        check.inst_param(execute_run_args, "execute_run_args", ExecuteRunArgs)

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
        for event in _core_execute_run(recon_pipeline, pipeline_run, instance):
            run_event_handler(event)
    except KeyboardInterrupt:
        run_event_handler(
            instance.report_engine_event(
                message="Pipeline execution terminated by interrupt", pipeline_run=pipeline_run,
            )
        )
        raise
    except GeneratorExit:
        closed = True
        raise
    finally:
        if not closed:
            run_event_handler(
                instance.report_engine_event(
                    "Process for pipeline exited (pid: {pid}).".format(pid=pid), pipeline_run,
                )
            )
        subprocess_status_handler(RunInSubprocessComplete())
        instance.dispose()


def execute_run_in_subprocess(
    serialized_execute_run_args, recon_pipeline, event_queue, termination_event
):
    with delay_interrupts():
        _run_in_subprocess(
            serialized_execute_run_args,
            recon_pipeline,
            termination_event,
            subprocess_status_handler=event_queue.put,
            run_event_handler=event_queue.put,
        )


def start_run_in_subprocess(
    serialized_execute_run_args, recon_pipeline, event_queue, termination_event
):
    with delay_interrupts():
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


def get_external_schedule_execution(recon_repo, external_schedule_execution_args):
    check.inst_param(
        recon_repo, "recon_repo", ReconstructableRepository,
    )
    check.inst_param(
        external_schedule_execution_args,
        "external_schedule_execution_args",
        ExternalScheduleExecutionArgs,
    )

    definition = recon_repo.get_definition()
    schedule_def = definition.get_schedule_def(external_schedule_execution_args.schedule_name)
    with DagsterInstance.from_ref(external_schedule_execution_args.instance_ref) as instance:

        scheduled_execution_time = (
            pendulum.from_timestamp(
                external_schedule_execution_args.scheduled_execution_timestamp,
                tz=external_schedule_execution_args.scheduled_execution_timezone,
            )
            if external_schedule_execution_args.scheduled_execution_timestamp
            else None
        )

        schedule_context = ScheduleExecutionContext(instance, scheduled_execution_time)
        schedule_execution_data_mode = external_schedule_execution_args.schedule_execution_data_mode

        try:
            with user_code_error_boundary(
                ScheduleExecutionError,
                lambda: "Error occurred during the execution of should_execute for schedule "
                "{schedule_name}".format(schedule_name=schedule_def.name),
            ):
                should_execute = None
                if (
                    schedule_execution_data_mode
                    == ScheduleExecutionDataMode.LAUNCH_SCHEDULED_EXECUTION
                ):
                    should_execute = schedule_def.should_execute(schedule_context)
                    if not should_execute:
                        return ExternalScheduleExecutionData(
                            should_execute=False, run_config=None, tags=None
                        )

            with user_code_error_boundary(
                ScheduleExecutionError,
                lambda: "Error occurred during the execution of run_config_fn for schedule "
                "{schedule_name}".format(schedule_name=schedule_def.name),
            ):
                run_config = schedule_def.get_run_config(schedule_context)

            with user_code_error_boundary(
                ScheduleExecutionError,
                lambda: "Error occurred during the execution of tags_fn for schedule "
                "{schedule_name}".format(schedule_name=schedule_def.name),
            ):
                tags = schedule_def.get_tags(schedule_context)

            return ExternalScheduleExecutionData(
                run_config=run_config, tags=tags, should_execute=should_execute
            )
        except ScheduleExecutionError:
            return ExternalScheduleExecutionErrorData(
                serializable_error_info_from_exc_info(sys.exc_info())
            )


def get_external_job_params(recon_repo, external_job_args):
    check.inst_param(recon_repo, "recon_repo", ReconstructableRepository)
    check.inst_param(
        external_job_args, "external_job_args", ExternalJobArgs,
    )
    definition = recon_repo.get_definition()
    job_def = definition.get_job_def(external_job_args.name)
    with DagsterInstance.from_ref(external_job_args.instance_ref) as instance:
        context = JobContext(instance)

        try:
            with user_code_error_boundary(
                JobError,
                lambda: "Error occured during the execution of run_config_fn for triggered "
                "execution {name}".format(name=job_def.name),
            ):
                run_config = job_def.get_run_config(context)

            with user_code_error_boundary(
                JobError,
                lambda: "Error occured during the execution of tags_fn for triggered "
                "execution {name}".format(name=job_def.name),
            ):
                tags = job_def.get_tags(context)

            return ExternalExecutionParamsData(run_config=run_config, tags=tags)
        except JobError:
            return ExternalExecutionParamsErrorData(
                serializable_error_info_from_exc_info(sys.exc_info())
            )


def get_partition_config(args):
    check.inst_param(args, "args", PartitionArgs)
    recon_repo = recon_repository_from_origin(args.repository_origin)
    definition = recon_repo.get_definition()
    partition_set_def = definition.get_partition_set_def(args.partition_set_name)
    partition = partition_set_def.get_partition(args.partition_name)
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


def get_partition_names(args):
    check.inst_param(args, "args", PartitionNamesArgs)
    recon_repo = recon_repository_from_origin(args.repository_origin)
    definition = recon_repo.get_definition()
    partition_set_def = definition.get_partition_set_def(args.partition_set_name)
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


def get_partition_tags(args):
    check.inst_param(args, "args", PartitionArgs)
    recon_repo = recon_repository_from_origin(args.repository_origin)
    definition = recon_repo.get_definition()
    partition_set_def = definition.get_partition_set_def(args.partition_set_name)
    partition = partition_set_def.get_partition(args.partition_name)
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
            ),
            args.pipeline_snapshot_id,
        )
    except:  # pylint: disable=bare-except
        return ExecutionPlanSnapshotErrorData(
            error=serializable_error_info_from_exc_info(sys.exc_info())
        )


def get_partition_set_execution_param_data(args):
    check.inst_param(args, "args", PartitionSetExecutionParamArgs)
    recon_repo = recon_repository_from_origin(args.repository_origin)
    repo_definition = recon_repo.get_definition()
    partition_set_def = repo_definition.get_partition_set_def(args.partition_set_name)
    try:
        with user_code_error_boundary(
            PartitionExecutionError,
            lambda: "Error occurred during the partition generation for partition set "
            "{partition_set_name}".format(partition_set_name=partition_set_def.name),
        ):
            all_partitions = partition_set_def.get_partitions()
        partitions = [
            partition for partition in all_partitions if partition.name in args.partition_names
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
                    name=partition.name, tags=tags, run_config=run_config,
                )
            )

        return ExternalPartitionSetExecutionParamData(partition_data=partition_data)

    except PartitionExecutionError:
        return ExternalPartitionExecutionErrorData(
            serializable_error_info_from_exc_info(sys.exc_info())
        )
