import logging
import sys
from collections.abc import Iterator, Mapping, Sequence
from typing import Optional, Union

from dagster_shared.error import DagsterError

import dagster._check as check
from dagster._config import Field, process_config
from dagster._core.definitions.executor_definition import (
    ExecutorDefinition,
    check_cross_process_constraints,
    multi_or_in_process_executor,
)
from dagster._core.definitions.reconstruct import ReconstructableJob
from dagster._core.definitions.run_config import selector_for_named_defs
from dagster._core.errors import DagsterInvalidConfigError, DagsterInvariantViolationError
from dagster._core.events import DagsterEvent, RunFailureReason
from dagster._core.execution.api import ExecuteRunWithPlanIterable, job_execution_iterator
from dagster._core.execution.context.logger import InitLoggerContext
from dagster._core.execution.context.system import PlanData, PlanOrchestrationContext
from dagster._core.execution.context_creation_job import PlanOrchestrationContextManager
from dagster._core.execution.plan.plan import ExecutionPlan
from dagster._core.executor.base import Executor
from dagster._core.executor.init import InitExecutorContext
from dagster._core.instance import DagsterInstance
from dagster._core.storage.dagster_run import DagsterRun, DagsterRunStatus
from dagster._loggers import default_system_loggers
from dagster._utils import ensure_single_item
from dagster._utils.error import serializable_error_info_from_exc_info


def _get_host_mode_executor(
    recon_job: ReconstructableJob,
    run_config: Mapping[str, object],
    executor_defs: Sequence[ExecutorDefinition],
    instance: DagsterInstance,
) -> Executor:
    execution_config = run_config.get("execution", {})
    execution_config_type = Field(
        selector_for_named_defs(executor_defs), default_value={executor_defs[0].name: {}}
    ).config_type

    config_evr = process_config(execution_config_type, execution_config)  # type: ignore  # (config typing)
    if not config_evr.success:
        raise DagsterInvalidConfigError(
            f"Error processing execution config {execution_config}",
            config_evr.errors,
            execution_config,
        )

    execution_config_value = check.not_none(config_evr.value)

    executor_name, executor_config = ensure_single_item(execution_config_value)

    executor_defs_by_name = {executor_def.name: executor_def for executor_def in executor_defs}
    executor_def = executor_defs_by_name[executor_name]

    init_context = InitExecutorContext(
        job=recon_job,
        executor_def=executor_def,
        executor_config=executor_config["config"],
        instance=instance,
    )
    check_cross_process_constraints(init_context)
    return executor_def.executor_creation_fn(init_context)  # type: ignore  # (possible none)


def host_mode_execution_context_event_generator(
    pipeline: ReconstructableJob,
    execution_plan: ExecutionPlan,
    run_config: Mapping[str, object],
    pipeline_run: DagsterRun,
    instance: DagsterInstance,
    raise_on_error: bool,
    executor_defs: Sequence[ExecutorDefinition],
    output_capture: None,
    resume_from_failure: bool = False,
) -> Iterator[Union[PlanOrchestrationContext, DagsterEvent]]:
    from dagster._core.log_manager import DagsterLogManager

    check.inst_param(execution_plan, "execution_plan", ExecutionPlan)
    check.inst_param(pipeline, "pipeline", ReconstructableJob)

    check.dict_param(run_config, "run_config", key_type=str)
    check.inst_param(pipeline_run, "pipeline_run", DagsterRun)
    check.inst_param(instance, "instance", DagsterInstance)
    executor_defs = check.list_param(executor_defs, "executor_defs", of_type=ExecutorDefinition)
    check.bool_param(raise_on_error, "raise_on_error")
    check.invariant(output_capture is None)

    execution_context = None

    loggers = []

    for logger_def, logger_config in default_system_loggers(instance):
        loggers.append(
            logger_def.logger_fn(
                InitLoggerContext(
                    logger_config,
                    job_def=None,
                    logger_def=logger_def,
                    run_id=pipeline_run.run_id,
                )
            )
        )

    log_manager = DagsterLogManager.create(
        loggers=loggers, dagster_run=pipeline_run, instance=instance
    )

    try:
        executor = _get_host_mode_executor(pipeline, run_config, executor_defs, instance)
        execution_context = PlanOrchestrationContext(
            plan_data=PlanData(
                job=pipeline,
                dagster_run=pipeline_run,
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
                dagster_error.original_exc_info  # type: ignore
                if dagster_error.is_user_code_error
                else sys.exc_info()
            )
            error_info = serializable_error_info_from_exc_info(user_facing_exc_info)

            event = DagsterEvent.job_failure(
                job_context_or_name=pipeline_run.job_name,
                context_msg=(
                    "Pipeline failure during initialization for pipeline"
                    f' "{pipeline_run.job_name}". This may be due to a failure in initializing'
                    " the executor or one of the loggers."
                ),
                failure_reason=RunFailureReason.JOB_INITIALIZATION_FAILURE,
                error_info=error_info,
            )
            log_manager.log_dagster_event(
                level=logging.ERROR,
                msg=event.message,  # type: ignore
                dagster_event=event,
            )
            yield event
        else:
            # pipeline teardown failure
            raise dagster_error

        if raise_on_error:
            raise dagster_error


def execute_run_host_mode(
    recon_job: ReconstructableJob,
    dagster_run: DagsterRun,
    instance: DagsterInstance,
    executor_defs: Optional[Sequence[ExecutorDefinition]] = None,
    raise_on_error: bool = False,
) -> Sequence[DagsterEvent]:
    check.inst_param(recon_job, "recon_job", ReconstructableJob)
    check.inst_param(dagster_run, "dagster_run", DagsterRun)
    check.inst_param(instance, "instance", DagsterInstance)
    check.opt_sequence_param(executor_defs, "executor_defs", of_type=ExecutorDefinition)
    executor_defs = executor_defs if executor_defs is not None else [multi_or_in_process_executor]

    if dagster_run.status == DagsterRunStatus.CANCELED:
        message = "Not starting execution since the run was canceled before execution could start"
        instance.report_engine_event(
            message,
            dagster_run,
        )
        raise DagsterInvariantViolationError(message)

    check.invariant(
        dagster_run.status == DagsterRunStatus.NOT_STARTED
        or dagster_run.status == DagsterRunStatus.STARTING,
        desc=f"Pipeline run {dagster_run.job_name} ({dagster_run.run_id}) in state {dagster_run.status}, expected NOT_STARTED or STARTING",
    )

    recon_job = recon_job.get_subset(
        op_selection=dagster_run.resolved_op_selection,
        asset_selection=dagster_run.asset_selection,
    )

    execution_plan_snapshot = instance.get_execution_plan_snapshot(
        check.not_none(dagster_run.execution_plan_snapshot_id)
    )
    execution_plan = ExecutionPlan.rebuild_from_snapshot(
        dagster_run.job_name,
        execution_plan_snapshot,
    )
    recon_job = recon_job.with_repository_load_data(execution_plan.repository_load_data)

    _execute_run_iterable = ExecuteRunWithPlanIterable(
        execution_plan=execution_plan,
        iterator=job_execution_iterator,
        execution_context_manager=PlanOrchestrationContextManager(
            context_event_generator=host_mode_execution_context_event_generator,
            job=recon_job,
            execution_plan=execution_plan,
            run_config=dagster_run.run_config,
            dagster_run=dagster_run,
            instance=instance,
            raise_on_error=raise_on_error,
            executor_defs=executor_defs,
            output_capture=None,
        ),
    )
    event_list = list(_execute_run_iterable)
    return event_list
