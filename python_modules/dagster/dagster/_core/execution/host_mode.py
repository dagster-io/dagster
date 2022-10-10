import logging
import sys
from typing import List, Optional

import dagster._check as check
from dagster._config import Field, process_config
from dagster._core.definitions.executor_definition import (
    ExecutorDefinition,
    check_cross_process_constraints,
    default_executors,
)
from dagster._core.definitions.reconstruct import ReconstructablePipeline
from dagster._core.definitions.run_config import selector_for_named_defs
from dagster._core.errors import (
    DagsterError,
    DagsterInvalidConfigError,
    DagsterInvariantViolationError,
)
from dagster._core.events import DagsterEvent
from dagster._core.execution.plan.plan import ExecutionPlan
from dagster._core.executor.init import InitExecutorContext
from dagster._core.instance import DagsterInstance
from dagster._core.log_manager import DagsterLogManager
from dagster._core.storage.pipeline_run import PipelineRun, PipelineRunStatus
from dagster._loggers import default_system_loggers
from dagster._utils import ensure_single_item
from dagster._utils.error import serializable_error_info_from_exc_info

from .api import ExecuteRunWithPlanIterable, pipeline_execution_iterator
from .context.logger import InitLoggerContext
from .context.system import PlanData, PlanOrchestrationContext
from .context_creation_pipeline import PlanOrchestrationContextManager


def _get_host_mode_executor(recon_pipeline, run_config, executor_defs, instance):
    execution_config = run_config.get("execution", {})
    execution_config_type = Field(
        selector_for_named_defs(executor_defs), default_value={executor_defs[0].name: {}}
    ).config_type

    config_evr = process_config(execution_config_type, execution_config)
    if not config_evr.success:
        raise DagsterInvalidConfigError(
            "Error processing execution config {}".format(execution_config),
            config_evr.errors,
            execution_config,
        )

    execution_config_value = config_evr.value

    executor_name, executor_config = ensure_single_item(execution_config_value)

    executor_defs_by_name = {executor_def.name: executor_def for executor_def in executor_defs}
    executor_def = executor_defs_by_name[executor_name]

    init_context = InitExecutorContext(
        job=recon_pipeline,
        executor_def=executor_def,
        executor_config=executor_config["config"],
        instance=instance,
    )
    check_cross_process_constraints(init_context)
    return executor_def.executor_creation_fn(init_context)


def host_mode_execution_context_event_generator(
    pipeline,
    execution_plan,
    run_config,
    pipeline_run,
    instance,
    raise_on_error,
    executor_defs,
    output_capture,
    resume_from_failure: bool = False,
):
    check.inst_param(execution_plan, "execution_plan", ExecutionPlan)
    check.inst_param(pipeline, "pipeline", ReconstructablePipeline)

    check.dict_param(run_config, "run_config", key_type=str)
    check.inst_param(pipeline_run, "pipeline_run", PipelineRun)
    check.inst_param(instance, "instance", DagsterInstance)
    executor_defs = check.list_param(executor_defs, "executor_defs", of_type=ExecutorDefinition)
    check.bool_param(raise_on_error, "raise_on_error")
    check.invariant(output_capture is None)

    execution_context = None

    loggers = []

    for (logger_def, logger_config) in default_system_loggers():
        loggers.append(
            logger_def.logger_fn(
                InitLoggerContext(
                    logger_config,
                    pipeline_def=None,
                    logger_def=logger_def,
                    run_id=pipeline_run.run_id,
                )
            )
        )

    log_manager = DagsterLogManager.create(
        loggers=loggers, pipeline_run=pipeline_run, instance=instance
    )

    try:
        executor = _get_host_mode_executor(pipeline, run_config, executor_defs, instance)
        execution_context = PlanOrchestrationContext(
            plan_data=PlanData(
                pipeline=pipeline,
                pipeline_run=pipeline_run,
                instance=instance,
                execution_plan=execution_plan,
                raise_on_error=raise_on_error,
                retry_mode=executor.retries,
            ),
            log_manager=log_manager,
            executor=executor,
            output_capture=None,
            resume_from_failure=resume_from_failure,
        )

        yield execution_context

    except DagsterError as dagster_error:
        if execution_context is None:
            user_facing_exc_info = (
                # pylint does not know original_exc_info exists is is_user_code_error is true
                # pylint: disable=no-member
                dagster_error.original_exc_info  # type: ignore
                if dagster_error.is_user_code_error
                else sys.exc_info()
            )
            error_info = serializable_error_info_from_exc_info(user_facing_exc_info)

            event = DagsterEvent.pipeline_failure(
                pipeline_context_or_name=pipeline_run.pipeline_name,
                context_msg=(
                    f'Pipeline failure during initialization for pipeline "{pipeline_run.pipeline_name}". '
                    "This may be due to a failure in initializing the executor or one of the loggers."
                ),
                error_info=error_info,
            )
            log_manager.log_dagster_event(
                level=logging.ERROR, msg=event.message, dagster_event=event  # type: ignore
            )
            yield event
        else:
            # pipeline teardown failure
            raise dagster_error

        if raise_on_error:
            raise dagster_error


def execute_run_host_mode(
    pipeline: ReconstructablePipeline,
    pipeline_run: PipelineRun,
    instance: DagsterInstance,
    executor_defs: Optional[List[ExecutorDefinition]] = None,
    raise_on_error: bool = False,
):
    check.inst_param(pipeline, "pipeline", ReconstructablePipeline)
    check.inst_param(pipeline_run, "pipeline_run", PipelineRun)
    check.inst_param(instance, "instance", DagsterInstance)
    check.opt_list_param(executor_defs, "executor_defs", of_type=ExecutorDefinition)
    executor_defs = executor_defs if executor_defs != None else default_executors

    if pipeline_run.status == PipelineRunStatus.CANCELED:
        message = "Not starting execution since the run was canceled before execution could start"
        instance.report_engine_event(
            message,
            pipeline_run,
        )
        raise DagsterInvariantViolationError(message)

    check.invariant(
        pipeline_run.status == PipelineRunStatus.NOT_STARTED
        or pipeline_run.status == PipelineRunStatus.STARTING,
        desc="Pipeline run {} ({}) in state {}, expected NOT_STARTED or STARTING".format(
            pipeline_run.pipeline_name, pipeline_run.run_id, pipeline_run.status
        ),
    )

    pipeline = pipeline.subset_for_execution_from_existing_pipeline(
        solids_to_execute=frozenset(pipeline_run.solids_to_execute)
        if pipeline_run.solids_to_execute
        else None,
        asset_selection=pipeline_run.asset_selection,
    )

    execution_plan_snapshot = instance.get_execution_plan_snapshot(
        pipeline_run.execution_plan_snapshot_id
    )
    execution_plan = ExecutionPlan.rebuild_from_snapshot(
        pipeline_run.pipeline_name,
        execution_plan_snapshot,
    )
    pipeline = pipeline.with_repository_load_data(execution_plan.repository_load_data)

    _execute_run_iterable = ExecuteRunWithPlanIterable(
        execution_plan=execution_plan,
        iterator=pipeline_execution_iterator,
        execution_context_manager=PlanOrchestrationContextManager(
            context_event_generator=host_mode_execution_context_event_generator,
            pipeline=pipeline,
            execution_plan=execution_plan,
            run_config=pipeline_run.run_config,
            pipeline_run=pipeline_run,
            instance=instance,
            raise_on_error=raise_on_error,
            executor_defs=executor_defs,
            output_capture=None,
        ),
    )
    event_list = list(_execute_run_iterable)
    return event_list
