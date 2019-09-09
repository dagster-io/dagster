'''
Naming conventions:

For public functions:

execute_*

These represent functions which do purely in-memory compute. They will evaluate expectations the
core compute function, and exercise all logging and metrics tracking (outside of outputs), but they
will not invoke *any* outputs (and their APIs don't allow the user to).
'''
from dagster import check
from dagster.core.definitions import PipelineDefinition, SystemStorageData
from dagster.core.errors import (
    DagsterExecutionStepNotFoundError,
    DagsterInvariantViolationError,
    DagsterRunNotFoundError,
    DagsterStepOutputNotFoundError,
)
from dagster.core.events import DagsterEvent, DagsterEventType
from dagster.core.execution.context.system import SystemPipelineExecutionContext
from dagster.core.execution.plan.plan import ExecutionPlan
from dagster.core.instance import DagsterInstance
from dagster.core.storage.pipeline_run import PipelineRun, PipelineRunStatus
from dagster.utils import ensure_gen

from .config import RunConfig
from .context_creation_pipeline import create_environment_config, scoped_pipeline_context
from .results import PipelineExecutionResult


def check_run_config_param(run_config, pipeline_def):
    check.inst_param(pipeline_def, 'pipeline_def', PipelineDefinition)
    check.opt_inst_param(run_config, 'run_config', RunConfig)

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
    run_config = check.opt_inst_param(run_config, 'run_config', RunConfig, RunConfig())

    environment_config = create_environment_config(pipeline, environment_dict, run_config)

    return ExecutionPlan.build(
        pipeline, environment_config, pipeline.get_mode_definition(run_config.mode)
    )


def _pipeline_execution_iterator(
    pipeline_context, execution_plan, run_config, step_keys_to_execute
):
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
            pipeline_context,
            execution_plan=execution_plan,
            run_config=run_config,
            step_keys_to_execute=step_keys_to_execute,
        ):
            if event.is_step_failure:
                pipeline_success = False
            yield event

    finally:
        if pipeline_success:
            yield DagsterEvent.pipeline_success(pipeline_context)

        else:
            yield DagsterEvent.pipeline_failure(pipeline_context)


def execute_run_iterator(pipeline, pipeline_run, instance):
    check.inst_param(pipeline, 'pipeline', PipelineDefinition)
    instance = check.inst_param(instance, 'instance', DagsterInstance)
    check.invariant(pipeline_run.status == PipelineRunStatus.NOT_STARTED)

    # https://github.com/dagster-io/dagster/issues/1745
    run_config = RunConfig(
        run_id=pipeline_run.run_id,
        tags=pipeline_run.tags,
        reexecution_config=pipeline_run.reexecution_config,
        step_keys_to_execute=pipeline_run.step_keys_to_execute,
        mode=pipeline_run.mode,
    )

    execution_plan = create_execution_plan(
        pipeline, environment_dict=pipeline_run.environment_dict, run_config=run_config
    )

    with scoped_pipeline_context(
        pipeline, pipeline_run.environment_dict, run_config, instance
    ) as pipeline_context:

        for event in _pipeline_execution_iterator(
            pipeline_context,
            execution_plan,
            run_config=run_config,
            step_keys_to_execute=run_config.step_keys_to_execute,
        ):
            yield event


def execute_pipeline_iterator(pipeline, environment_dict=None, run_config=None, instance=None):
    '''Returns iterator that yields :py:class:`SolidExecutionResult` for each
    solid executed in the pipeline.

    This is intended to allow the caller to do things between each executed
    node. For the 'synchronous' API, see :py:func:`execute_pipeline`.

    Parameters:
      pipeline (PipelineDefinition): Pipeline to run
      environment_dict (dict): The enviroment configuration that parameterizes this run
      run_config (RunConfig): Configuration for how this pipeline will be executed

    Returns:
      Iterator[DagsterEvent]
    '''
    check.inst_param(pipeline, 'pipeline', PipelineDefinition)
    environment_dict = check.opt_dict_param(environment_dict, 'environment_dict')
    instance = check.opt_inst_param(
        instance, 'instance', DagsterInstance, DagsterInstance.ephemeral()
    )
    run_config = check_run_config_param(run_config, pipeline)

    run = _create_run(instance, pipeline, run_config, environment_dict)

    return execute_run_iterator(pipeline, run, instance)


def execute_pipeline(pipeline, environment_dict=None, run_config=None, instance=None):
    '''
    "Synchronous" version of :py:func:`execute_pipeline_iterator`.

    This is the entry point for dagster CLI and dagit execution. For the dagster-graphql entry
    point, see execute_plan() below.

    Parameters:
        pipeline (PipelineDefinition): Pipeline to run
        environment_dict (dict):
            The enviroment configuration that parameterizes this run
        run_config (RunConfig):
            Configuration for how this pipeline will be executed
        instance (DagsterInstance):
            The instance to execute against, defaults to ephemeral (no artifacts persisted)

    Returns:
      :py:class:`PipelineExecutionResult`
    '''

    check.inst_param(pipeline, 'pipeline', PipelineDefinition)
    environment_dict = check.opt_dict_param(environment_dict, 'environment_dict')
    run_config = check_run_config_param(run_config, pipeline)

    check.opt_inst_param(instance, 'instance', DagsterInstance)
    instance = instance or DagsterInstance.ephemeral()

    execution_plan = create_execution_plan(pipeline, environment_dict, run_config)

    # run should be used and threaded through here
    # https://github.com/dagster-io/dagster/issues/1745
    _run = _create_run(instance, pipeline, run_config, environment_dict)

    with scoped_pipeline_context(
        pipeline, environment_dict, run_config, instance
    ) as pipeline_context:
        event_list = list(
            _pipeline_execution_iterator(
                pipeline_context,
                execution_plan=execution_plan,
                run_config=run_config,
                step_keys_to_execute=run_config.step_keys_to_execute,
            )
        )

        return PipelineExecutionResult(
            pipeline,
            run_config.run_id,
            event_list,
            lambda: scoped_pipeline_context(
                pipeline,
                environment_dict,
                run_config,
                instance,
                system_storage_data=SystemStorageData(
                    intermediates_manager=pipeline_context.intermediates_manager,
                    file_manager=pipeline_context.file_manager,
                ),
            ),
        )


def execute_pipeline_with_preset(pipeline, preset_name, run_config=None, instance=None):
    '''Runs :py:func:`execute_pipeline` with the given preset for the pipeline.

    The preset will optionally provide environment_dict and/or build a pipeline from
    a solid subset. If a run_config is not provied, one which only sets the
    mode as defined by the preset will be used.
    '''

    check.inst_param(pipeline, 'pipeline', PipelineDefinition)
    check.str_param(preset_name, 'preset_name')
    check.opt_inst_param(run_config, 'run_config', RunConfig)
    check.opt_inst_param(instance, 'instance', DagsterInstance)
    instance = instance or DagsterInstance.ephemeral()

    preset = pipeline.get_preset(preset_name)

    pipeline = pipeline
    if preset.solid_subset is not None:
        pipeline = pipeline.build_sub_pipeline(preset.solid_subset)

    if run_config:
        run_config = run_config.with_mode(preset.mode)
    else:
        run_config = RunConfig(mode=preset.mode)

    return execute_pipeline(pipeline, preset.environment_dict, run_config, instance)


def _invoke_executor_on_plan(pipeline_context, execution_plan, step_keys_to_execute=None):
    if step_keys_to_execute:
        for step_key in step_keys_to_execute:
            if not execution_plan.has_step(step_key):
                raise DagsterExecutionStepNotFoundError(step_key=step_key)

    # Engine execution returns a generator of yielded events, so returning here means this function
    # also returns a generator

    return pipeline_context.executor_config.get_engine().execute(
        pipeline_context, execution_plan, step_keys_to_execute
    )


def _check_reexecution_config(pipeline_context, execution_plan, run_config):
    if not pipeline_context.intermediates_manager.is_persistent:
        raise DagsterInvariantViolationError(
            'Cannot perform reexecution with non persistent intermediates manager.'
        )

    previous_run_id = run_config.reexecution_config.previous_run_id

    if not pipeline_context.instance.has_run(previous_run_id):
        raise DagsterRunNotFoundError(
            'Run id {} set as previous run id was not found in instance'.format(previous_run_id),
            invalid_run_id=previous_run_id,
        )

    check.invariant(
        run_config.run_id != previous_run_id,
        'Run id {} is identical to previous run id'.format(run_config.run_id),
    )

    for step_output_handle in run_config.reexecution_config.step_output_handles:
        if not execution_plan.has_step(step_output_handle.step_key):
            raise DagsterExecutionStepNotFoundError(
                (
                    'Step {step_key} was specified as a step from a previous run. '
                    'It does not exist.'
                ).format(step_key=step_output_handle.step_key),
                step_key=step_output_handle.step_key,
            )

        step = execution_plan.get_step_by_key(step_output_handle.step_key)
        if not step.has_step_output(step_output_handle.output_name):
            raise DagsterStepOutputNotFoundError(
                (
                    'You specified a step_output_handle in the ReexecutionConfig that does '
                    'not exist: Step {step_key} does not have output {output_name}.'
                ).format(
                    step_key=step_output_handle.step_key, output_name=step_output_handle.output_name
                ),
                step_key=step_output_handle.step_key,
                output_name=step_output_handle.output_name,
            )


def _steps_execution_iterator(pipeline_context, execution_plan, run_config, step_keys_to_execute):
    '''Iterates over execution of individual steps yielding the associated events.
    Does not yield pipeline level events asside from init failure when the context fails to construct.
    '''
    check.inst_param(
        pipeline_context, 'pipeline_context', (DagsterEvent, SystemPipelineExecutionContext)
    )
    check.inst_param(execution_plan, 'execution_plan', ExecutionPlan)
    check.inst_param(run_config, 'run_config', RunConfig)
    check.opt_list_param(step_keys_to_execute, 'step_keys_to_execute', of_type=str)

    if (
        isinstance(pipeline_context, DagsterEvent)
        and pipeline_context.event_type  # pylint: disable=no-member
        == DagsterEventType.PIPELINE_INIT_FAILURE
    ):
        return ensure_gen(pipeline_context)

    if not step_keys_to_execute:
        step_keys_to_execute = [step.key for step in execution_plan.topological_steps()]

    if not step_keys_to_execute:
        pipeline_context.log.debug(
            'Pipeline {pipeline} has no steps to execute and no execution will happen'.format(
                pipeline=pipeline_context.pipeline_def.display_name
            )
        )
        return ensure_gen(DagsterEvent.pipeline_success(pipeline_context))
    else:
        for step_key in step_keys_to_execute:
            if not execution_plan.has_step(step_key):
                raise DagsterExecutionStepNotFoundError(
                    'Execution plan does not contain step \'{}\''.format(step_key),
                    step_key=step_key,
                )

    _setup_reexecution(run_config, pipeline_context, execution_plan)

    return _invoke_executor_on_plan(pipeline_context, execution_plan, step_keys_to_execute)


def execute_plan_iterator(
    execution_plan, environment_dict=None, run_config=None, step_keys_to_execute=None, instance=None
):
    check.inst_param(execution_plan, 'execution_plan', ExecutionPlan)
    environment_dict = check.opt_dict_param(environment_dict, 'environment_dict')
    run_config = check_run_config_param(run_config, execution_plan.pipeline_def)
    check.opt_list_param(step_keys_to_execute, 'step_keys_to_execute', of_type=str)
    instance = check.opt_inst_param(instance, 'instance', DagsterInstance)

    instance = instance or DagsterInstance.ephemeral()

    with scoped_pipeline_context(
        execution_plan.pipeline_def, environment_dict, run_config, instance
    ) as pipeline_context:

        return _steps_execution_iterator(
            pipeline_context,
            execution_plan=execution_plan,
            run_config=run_config,
            step_keys_to_execute=step_keys_to_execute,
        )


def execute_plan(
    execution_plan, instance, environment_dict=None, run_config=None, step_keys_to_execute=None
):
    '''This is the entry point of dagster-graphql executions. For the dagster CLI entry point, see
    execute_pipeline() above.
    '''
    check.inst_param(execution_plan, 'execution_plan', ExecutionPlan)
    check.inst_param(instance, 'instance', DagsterInstance)
    environment_dict = check.opt_dict_param(environment_dict, 'environment_dict')
    run_config = check_run_config_param(run_config, execution_plan.pipeline_def)
    check.opt_list_param(step_keys_to_execute, 'step_keys_to_execute', of_type=str)

    if step_keys_to_execute is None:
        step_keys_to_execute = [step.key for step in execution_plan.topological_steps()]

    return list(
        execute_plan_iterator(
            execution_plan=execution_plan,
            environment_dict=environment_dict,
            run_config=run_config,
            step_keys_to_execute=step_keys_to_execute,
            instance=instance,
        )
    )


def _setup_reexecution(run_config, pipeline_context, execution_plan):
    if run_config.reexecution_config:
        _check_reexecution_config(pipeline_context, execution_plan, run_config)

        for step_output_handle in run_config.reexecution_config.step_output_handles:
            pipeline_context.intermediates_manager.copy_intermediate_from_prev_run(
                pipeline_context, run_config.reexecution_config.previous_run_id, step_output_handle
            )


def step_output_event_filter(pipe_iterator):
    for step_event in pipe_iterator:
        if step_event.is_successful_output:
            yield step_event


def _create_run(instance, pipeline_def, run_config, environment_dict):
    return instance.create_run(
        PipelineRun(
            pipeline_name=pipeline_def.name,
            run_id=run_config.run_id,
            environment_dict=environment_dict,
            mode=run_config.mode,
            selector=pipeline_def.selector,
            reexecution_config=run_config.reexecution_config,
            step_keys_to_execute=run_config.step_keys_to_execute,
            tags=run_config.tags,
            status=PipelineRunStatus.NOT_STARTED,
        )
    )
