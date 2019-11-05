import time

from dagster import check
from dagster.core.definitions import PipelineDefinition, SystemStorageData
from dagster.core.errors import DagsterInvariantViolationError
from dagster.core.events import DagsterEvent, DagsterEventType
from dagster.core.execution.context.system import SystemPipelineExecutionContext
from dagster.core.execution.memoization import validate_retry_memoization
from dagster.core.execution.plan.plan import ExecutionPlan
from dagster.core.instance import DagsterInstance
from dagster.core.storage.pipeline_run import PipelineRun, PipelineRunStatus
from dagster.core.system_config.objects import EnvironmentConfig
from dagster.utils import ensure_gen, merge_dicts

from .config import EXECUTION_TIME_KEY, IRunConfig, RunConfig
from .context_creation_pipeline import scoped_pipeline_context
from .results import PipelineExecutionResult


def check_run_config_param(run_config, pipeline_def):
    check.inst_param(pipeline_def, 'pipeline_def', PipelineDefinition)
    check.opt_inst_param(run_config, 'run_config', IRunConfig)

    if run_config and run_config.mode:
        if not pipeline_def.has_mode_definition(run_config.mode):
            raise DagsterInvariantViolationError(
                (
                    'You have attempted to execute pipeline {name} with mode {mode}. '
                    'Available modes: {modes}'
                ).format(
                    name=pipeline_def.name, mode=run_config.mode, modes=pipeline_def.available_modes
                )
            )
        return run_config

    else:
        if not pipeline_def.is_single_mode:
            raise DagsterInvariantViolationError(
                (
                    'Pipeline {name} has multiple modes (Available modes: {modes}) and you have '
                    'attempted to execute it without specifying a mode. Set '
                    'mode property on the RunConfig object.'
                ).format(name=pipeline_def.name, modes=pipeline_def.available_modes)
            )

    return (
        run_config.with_mode(pipeline_def.get_default_mode_name())
        if run_config
        else RunConfig(mode=pipeline_def.get_default_mode_name())
    )


def create_execution_plan(pipeline, environment_dict=None, run_config=None):
    check.inst_param(pipeline, 'pipeline', PipelineDefinition)
    environment_dict = check.opt_dict_param(environment_dict, 'environment_dict', key_type=str)
    run_config = check.opt_inst_param(run_config, 'run_config', IRunConfig, RunConfig())

    environment_config = EnvironmentConfig.build(pipeline, environment_dict, run_config)

    return ExecutionPlan.build(pipeline, environment_config, run_config)


def _pipeline_execution_iterator(pipeline_context, execution_plan, pipeline_run):
    '''A complete execution of a pipeline. Yields pipeline start, success,
    and failure events. Defers to _steps_execution_iterator for step execution.
    '''
    if (
        isinstance(pipeline_context, DagsterEvent)
        and pipeline_context.event_type  # pylint: disable=no-member
        == DagsterEventType.PIPELINE_INIT_FAILURE
    ):
        yield pipeline_context
        return

    yield DagsterEvent.pipeline_start(pipeline_context)

    pipeline_success = True
    try:
        for event in _steps_execution_iterator(
            pipeline_context, execution_plan=execution_plan, pipeline_run=pipeline_run
        ):
            if event.is_step_failure:
                pipeline_success = False
            yield event
    except (Exception, KeyboardInterrupt):
        pipeline_success = False
        raise  # finally block will run before this is re-raised
    finally:
        if pipeline_success:
            yield DagsterEvent.pipeline_success(pipeline_context)

        else:
            yield DagsterEvent.pipeline_failure(pipeline_context)


def execute_run_iterator(pipeline, pipeline_run, instance):
    check.inst_param(pipeline, 'pipeline', PipelineDefinition)
    instance = check.inst_param(instance, 'instance', DagsterInstance)
    check.invariant(pipeline_run.status == PipelineRunStatus.NOT_STARTED)

    execution_plan = create_execution_plan(
        pipeline, environment_dict=pipeline_run.environment_dict, run_config=pipeline_run
    )

    with scoped_pipeline_context(
        pipeline, pipeline_run.environment_dict, pipeline_run, instance
    ) as pipeline_context:
        for event in _pipeline_execution_iterator(pipeline_context, execution_plan, pipeline_run):
            yield event


def execute_pipeline_iterator(pipeline, environment_dict=None, run_config=None, instance=None):
    '''Execute a pipeline iteratively.

    Rather than package up the result of running a pipeline into a single object, like
    :py:func:`execute_pipeline`, this function yields the stream of events resulting from pipeline
    execution.

    This is intended to allow the caller to handle these events on a streaming basis in whatever
    way is appropriate.

    Parameters:
        pipeline (PipelineDefinition): The pipeline to execute.
        environment_dict (Optional[dict]): The enviroment configuration that parameterizes this run,
            as a dict.
        run_config (Optional[RunConfig]): Optionally specifies additional config options for
            pipeline execution.
        instance (Optional[DagsterInstance]): The instance to execute against. If this is ``None``,
            an ephemeral instance will be used, and no artifacts will be persisted from the run.

    Returns:
      Iterator[DagsterEvent]: The stream of events resulting from pipeline execution.
    '''
    check.inst_param(pipeline, 'pipeline', PipelineDefinition)
    environment_dict = check.opt_dict_param(environment_dict, 'environment_dict')
    instance = check.opt_inst_param(
        instance, 'instance', DagsterInstance, DagsterInstance.ephemeral()
    )
    run_config = check_run_config_param(run_config, pipeline)

    run = _create_run(instance, pipeline, run_config, environment_dict)

    return execute_run_iterator(pipeline, run, instance)


def execute_pipeline(
    pipeline, environment_dict=None, run_config=None, instance=None, raise_on_error=True
):
    '''Execute a pipeline synchronously.

    Users will typically call this API when testing pipeline execution, or running standalone
    scripts.

    Parameters:
        pipeline (PipelineDefinition): The pipeline to execute.
        environment_dict (Optional[dict]): The enviroment configuration that parameterizes this run,
            as a dict.
        run_config (Optional[RunConfig]): Optionally specifies additional config options for
            pipeline execution.
        instance (Optional[DagsterInstance]): The instance to execute against. If this is ``None``,
            an ephemeral instance will be used, and no artifacts will be persisted from the run.
        raise_on_error (Optional[bool]): Whether or not to raise exceptions when they occur.
            Defaults to ``True``, since this is the most useful behavior in test.

    Returns:
      :py:class:`PipelineExecutionResult`: The result of pipeline execution.

    For the asynchronous version, see :py:func:`execute_pipeline_iterator`.

    This is the entrypoint for dagster CLI execution. For the dagster-graphql entrypoint, see
    ``dagster.core.execution.api.execute_plan()``.
    '''

    check.inst_param(pipeline, 'pipeline', PipelineDefinition)
    environment_dict = check.opt_dict_param(environment_dict, 'environment_dict')
    run_config = check_run_config_param(run_config, pipeline)

    check.opt_inst_param(instance, 'instance', DagsterInstance)
    instance = instance or DagsterInstance.ephemeral()

    execution_plan = create_execution_plan(pipeline, environment_dict, run_config)

    pipeline_run = _create_run(instance, pipeline, run_config, environment_dict)

    with scoped_pipeline_context(
        pipeline, environment_dict, pipeline_run, instance, raise_on_error=raise_on_error
    ) as pipeline_context:
        event_list = list(
            _pipeline_execution_iterator(pipeline_context, execution_plan, pipeline_run)
        )

        return PipelineExecutionResult(
            pipeline,
            run_config.run_id,
            event_list,
            lambda: scoped_pipeline_context(
                pipeline,
                environment_dict,
                pipeline_run,
                instance,
                system_storage_data=SystemStorageData(
                    intermediates_manager=pipeline_context.intermediates_manager,
                    file_manager=pipeline_context.file_manager,
                ),
            ),
        )


def execute_pipeline_with_preset(
    pipeline, preset_name, run_config=None, instance=None, raise_on_error=True
):
    '''Execute a pipeline synchronously, with the given preset.

    Parameters:
        pipeline (PipelineDefinition): The pipeline to execute.
        preset_name (str): The preset to use.
        run_config (Optional[RunConfig]): Optionally specifies additional config options for
            pipeline execution. (default: ``None``)
        instance (Optional[DagsterInstance]): The instance to execute against. If this is ``None``,
            an ephemeral instance will be used, and no artifacts will be persisted from the run.
            (default: ``None``)
        raise_on_error (Optional[bool]): Whether or not to raise exceptions when they occur.
            Default is ``True``, since this is the most useful behavior in test.

    Returns:
      :py:class:`PipelineExecutionResult`: The result of pipeline execution.
    '''

    check.inst_param(pipeline, 'pipeline', PipelineDefinition)
    check.str_param(preset_name, 'preset_name')
    check.opt_inst_param(run_config, 'run_config', RunConfig)
    check.opt_inst_param(instance, 'instance', DagsterInstance)
    instance = instance or DagsterInstance.ephemeral()

    preset = pipeline.get_preset(preset_name)

    if preset.solid_subset is not None:
        pipeline = pipeline.build_sub_pipeline(preset.solid_subset)

    if run_config:
        run_config = run_config.with_mode(preset.mode)
    else:
        run_config = RunConfig(mode=preset.mode)

    return execute_pipeline(
        pipeline, preset.environment_dict, run_config, instance, raise_on_error=raise_on_error
    )


def _steps_execution_iterator(pipeline_context, execution_plan, pipeline_run):
    '''Iterates over execution of individual steps yielding the associated events.
    '''
    check.inst_param(
        pipeline_context, 'pipeline_context', (DagsterEvent, SystemPipelineExecutionContext)
    )
    check.inst_param(execution_plan, 'execution_plan', ExecutionPlan)
    check.inst_param(pipeline_run, 'pipeline_run', PipelineRun)

    if (
        isinstance(pipeline_context, DagsterEvent)
        # pylint: disable=no-member
        and pipeline_context.event_type == DagsterEventType.PIPELINE_INIT_FAILURE
    ):
        return ensure_gen(pipeline_context)

    if execution_plan.previous_run_id:
        validate_retry_memoization(pipeline_context, execution_plan)

    return pipeline_context.executor_config.get_engine().execute(pipeline_context, execution_plan)


def execute_plan_iterator(execution_plan, pipeline_run, environment_dict=None, instance=None):
    check.inst_param(execution_plan, 'execution_plan', ExecutionPlan)
    check.inst_param(pipeline_run, 'pipeline_run', PipelineRun)
    environment_dict = check.opt_dict_param(environment_dict, 'environment_dict')
    instance = check.inst_param(instance, 'instance', DagsterInstance)

    with scoped_pipeline_context(
        execution_plan.pipeline_def, environment_dict, pipeline_run, instance
    ) as pipeline_context:
        return _steps_execution_iterator(
            pipeline_context, execution_plan=execution_plan, pipeline_run=pipeline_run
        )

    check.failed('Unexpected state, should be unreachable')


def execute_plan(execution_plan, instance, pipeline_run, environment_dict=None):
    '''This is the entry point of dagster-graphql executions. For the dagster CLI entry point, see
    execute_pipeline() above.
    '''
    check.inst_param(execution_plan, 'execution_plan', ExecutionPlan)
    check.inst_param(instance, 'instance', DagsterInstance)
    check.inst_param(pipeline_run, 'pipeline_run', PipelineRun)
    environment_dict = check.opt_dict_param(environment_dict, 'environment_dict')

    return list(
        execute_plan_iterator(
            execution_plan=execution_plan,
            environment_dict=environment_dict,
            pipeline_run=pipeline_run,
            instance=instance,
        )
    )


def step_output_event_filter(pipe_iterator):
    for step_event in pipe_iterator:
        if step_event.is_successful_output:
            yield step_event


def _create_run(instance, pipeline_def, run_config, environment_dict):
    tags = _add_execution_time_tag(run_config.tags)
    return instance.create_run(
        PipelineRun(
            pipeline_name=pipeline_def.name,
            run_id=run_config.run_id,
            environment_dict=environment_dict,
            mode=run_config.mode,
            selector=pipeline_def.selector,
            reexecution_config=run_config.reexecution_config,
            step_keys_to_execute=run_config.step_keys_to_execute,
            tags=tags,
            status=PipelineRunStatus.NOT_STARTED,
            previous_run_id=run_config.previous_run_id,
        )
    )


def _add_execution_time_tag(tags):
    if not tags:
        return {EXECUTION_TIME_KEY: time.time()}

    if EXECUTION_TIME_KEY in tags:
        # execution_epoch_time expected to be able to be cast to float
        # can be passed in as a string from airflow integration
        execution_time = float(tags[EXECUTION_TIME_KEY])
    else:
        execution_time = time.time()

    return merge_dicts(tags, {EXECUTION_TIME_KEY: execution_time})
