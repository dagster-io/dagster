import sys
from typing import Callable, Optional

from dagster import check
from dagster.config.validate import process_config
from dagster.core.definitions.environment_configs import def_config_field
from dagster.core.definitions.executor import ExecutorDefinition, check_cross_process_constraints
from dagster.core.definitions.reconstructable import ReconstructablePipeline
from dagster.core.errors import (
    DagsterError,
    DagsterInvalidConfigError,
    DagsterInvariantViolationError,
)
from dagster.core.events import DagsterEvent, PipelineInitFailureData
from dagster.core.execution.plan.plan import ExecutionPlan
from dagster.core.executor.init import InitExecutorContext
from dagster.core.instance import DagsterInstance
from dagster.core.log_manager import DagsterLogManager
from dagster.core.storage.pipeline_run import PipelineRun, PipelineRunStatus
from dagster.loggers import default_system_loggers
from dagster.utils import ensure_single_item
from dagster.utils.error import serializable_error_info_from_exc_info

from .api import ExecuteRunWithPlanIterable, pipeline_execution_iterator
from .context.logger import InitLoggerContext
from .context.system import PlanData, PlanOrchestrationContext
from .context_creation_pipeline import PlanOrchestrationContextManager, get_logging_tags


def _get_host_mode_executor(recon_pipeline, run_config, get_executor_def_fn, instance):
    execution_config = run_config.get("execution")
    if execution_config:
        executor_name, executor_config = ensure_single_item(execution_config)
    else:
        executor_name = None
        executor_config = {}

    executor_def = get_executor_def_fn(executor_name)

    executor_config_type = def_config_field(executor_def).config_type

    config_evr = process_config(executor_config_type, executor_config)
    if not config_evr.success:
        raise DagsterInvalidConfigError(
            "Error in executor config for executor {}".format(executor_def.name),
            config_evr.errors,
            executor_config,
        )
    executor_config_value = config_evr.value

    init_context = InitExecutorContext(
        pipeline=recon_pipeline,
        executor_def=executor_def,
        executor_config=executor_config_value["config"],
        instance=instance,
    )
    check_cross_process_constraints(init_context)
    return executor_def.executor_creation_fn(init_context)


def _default_get_executor_def_fn(executor_name):
    if executor_name == "in_process":
        from dagster.core.definitions.executor import in_process_executor

        return in_process_executor
    elif executor_name == "multiprocess":
        from dagster.core.definitions.executor import multiprocess_executor

        return multiprocess_executor
    elif executor_name:
        raise DagsterInvariantViolationError(f"Unexpected executor {executor_name}")
    else:
        from dagster.core.definitions.executor import in_process_executor

        return in_process_executor


def host_mode_execution_context_event_generator(
    pipeline,
    execution_plan,
    run_config,
    pipeline_run,
    instance,
    raise_on_error,
    get_executor_def_fn,
    output_capture,
):
    check.inst_param(execution_plan, "execution_plan", ExecutionPlan)
    check.inst_param(pipeline, "pipeline", ReconstructablePipeline)

    check.dict_param(run_config, "run_config", key_type=str)
    check.inst_param(pipeline_run, "pipeline_run", PipelineRun)
    check.inst_param(instance, "instance", DagsterInstance)
    get_executor_def_fn = check.opt_callable_param(
        get_executor_def_fn, "get_executor_def_fn", _default_get_executor_def_fn
    )
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

    loggers.append(instance.get_logger())

    log_manager = DagsterLogManager(
        run_id=pipeline_run.run_id,
        logging_tags=get_logging_tags(pipeline_run),
        loggers=loggers,
    )

    try:
        executor = _get_host_mode_executor(pipeline, run_config, get_executor_def_fn, instance)
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
        )

        yield execution_context

    except DagsterError as dagster_error:
        if execution_context is None:
            user_facing_exc_info = (
                # pylint does not know original_exc_info exists is is_user_code_error is true
                # pylint: disable=no-member
                dagster_error.original_exc_info
                if dagster_error.is_user_code_error
                else sys.exc_info()
            )
            error_info = serializable_error_info_from_exc_info(user_facing_exc_info)

            yield DagsterEvent.pipeline_init_failure(
                pipeline_name=pipeline_run.pipeline_name,
                failure_data=PipelineInitFailureData(error=error_info),
                log_manager=log_manager,
            )
        else:
            # pipeline teardown failure
            raise dagster_error

        if raise_on_error:
            raise dagster_error


def execute_run_host_mode(
    pipeline: ReconstructablePipeline,
    pipeline_run: PipelineRun,
    instance: DagsterInstance,
    get_executor_def_fn: Callable[[Optional[str]], ExecutorDefinition] = None,
    raise_on_error: bool = False,
):
    check.inst_param(pipeline, "pipeline", ReconstructablePipeline)
    check.inst_param(pipeline_run, "pipeline_run", PipelineRun)
    check.inst_param(instance, "instance", DagsterInstance)
    check.opt_callable_param(get_executor_def_fn, "get_executor_def_fn")

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

    if pipeline_run.solids_to_execute:
        pipeline = pipeline.subset_for_execution_from_existing_pipeline(
            pipeline_run.solids_to_execute
        )

    execution_plan_snapshot = instance.get_execution_plan_snapshot(
        pipeline_run.execution_plan_snapshot_id
    )
    execution_plan = ExecutionPlan.rebuild_from_snapshot(
        pipeline_run.pipeline_name,
        execution_plan_snapshot,
    )

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
            get_executor_def_fn=get_executor_def_fn,
            output_capture=None,
        ),
    )
    event_list = list(_execute_run_iterable)
    return event_list
