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
from dagster.core.execution.plan.plan import ExecutionPlan

from .context_creation_pipeline import create_environment_config, scoped_pipeline_context
from .config import RunConfig, InProcessExecutorConfig
from .context.system import SystemPipelineExecutionContext
from .results import PipelineExecutionResult


def check_run_config_param(run_config, pipeline_def):
    check.inst_param(pipeline_def, 'pipeline_def', PipelineDefinition)

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
        check.inst_param(run_config, 'run_config', RunConfig)
        if run_config
        else RunConfig(
            executor_config=InProcessExecutorConfig(), mode=pipeline_def.get_default_mode_name()
        )
    )


def create_execution_plan(pipeline, environment_dict=None, run_config=None):
    check.inst_param(pipeline, 'pipeline', PipelineDefinition)
    environment_dict = check.opt_dict_param(environment_dict, 'environment_dict', key_type=str)
    run_config = check.opt_inst_param(run_config, 'run_config', RunConfig, RunConfig())

    environment_config = create_environment_config(pipeline, environment_dict, run_config)

    return ExecutionPlan.build(
        pipeline, environment_config, pipeline.get_mode_definition(run_config.mode)
    )


def _execute_pipeline_iterator(context_or_failure_event):
    # Due to use of context managers, if the user land code in context or resource init fails
    # we can get either a pipeline_context or the failure event here.
    if (
        isinstance(context_or_failure_event, DagsterEvent)
        and context_or_failure_event.event_type == DagsterEventType.PIPELINE_INIT_FAILURE
    ):
        yield context_or_failure_event
        return

    pipeline_context = context_or_failure_event
    check.inst_param(pipeline_context, 'pipeline_context', SystemPipelineExecutionContext)
    yield DagsterEvent.pipeline_start(pipeline_context)

    execution_plan = ExecutionPlan.build(
        pipeline_context.pipeline_def,
        pipeline_context.environment_config,
        pipeline_context.mode_def,
    )

    steps = execution_plan.topological_steps()

    if not steps:
        pipeline_context.log.debug(
            'Pipeline {pipeline} has no nodes and no execution will happen'.format(
                pipeline=pipeline_context.pipeline_def.display_name
            )
        )
        yield DagsterEvent.pipeline_success(pipeline_context)
        return

    _setup_reexecution(pipeline_context.run_config, pipeline_context, execution_plan)

    check.invariant(
        len([step_input for step_input in steps[0].step_inputs if step_input.is_from_output]) == 0
    )

    pipeline_success = True

    try:
        for event in invoke_executor_on_plan(
            pipeline_context, execution_plan, pipeline_context.run_config.step_keys_to_execute
        ):
            if event.is_step_failure:
                pipeline_success = False
            yield event
    finally:
        if pipeline_success:
            yield DagsterEvent.pipeline_success(pipeline_context)
        else:
            yield DagsterEvent.pipeline_failure(pipeline_context)


def execute_pipeline_iterator(pipeline, environment_dict=None, run_config=None):
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
    run_config = check_run_config_param(run_config, pipeline)

    with scoped_pipeline_context(pipeline, environment_dict, run_config) as pipeline_context:
        return _execute_pipeline_iterator(pipeline_context)


def execute_pipeline(pipeline, environment_dict=None, run_config=None):
    '''
    "Synchronous" version of :py:func:`execute_pipeline_iterator`.

    This is the entry point for dagster CLI and dagit execution. For the dagster-graphql entry
    point, see execute_plan() below.

    Note: raise_on_error is very useful in testing contexts when not testing for error
    conditions

    Parameters:
      pipeline (PipelineDefinition): Pipeline to run
      environment_dict (dict): The enviroment configuration that parameterizes this run
      run_config (RunConfig): Configuration for how this pipeline will be executed

    Returns:
      :py:class:`PipelineExecutionResult`
    '''

    check.inst_param(pipeline, 'pipeline', PipelineDefinition)
    environment_dict = check.opt_dict_param(environment_dict, 'environment_dict')
    run_config = check_run_config_param(run_config, pipeline)

    with scoped_pipeline_context(pipeline, environment_dict, run_config) as pipeline_context:
        event_list = list(_execute_pipeline_iterator(pipeline_context))

        return PipelineExecutionResult(
            pipeline,
            run_config.run_id,
            event_list,
            lambda: scoped_pipeline_context(
                pipeline,
                environment_dict,
                run_config,
                system_storage_data=SystemStorageData(
                    run_storage=pipeline_context.run_storage,
                    intermediates_manager=pipeline_context.intermediates_manager,
                    file_manager=pipeline_context.file_manager,
                ),
            ),
        )


def execute_pipeline_with_preset(pipeline, preset_name, run_config=None):
    '''Runs :py:func:`execute_pipeline` with the given preset for the pipeline.

    The preset will optionally provide environment_dict and/or build a pipeline from
    a solid subset. If a run_config is not provied, one which only sets the
    mode as defined by the preset will be used.
    '''

    check.inst_param(pipeline, 'pipeline', PipelineDefinition)
    check.str_param(preset_name, 'preset_name')
    check.opt_inst_param(run_config, 'run_config', RunConfig)
    preset = pipeline.get_preset(preset_name)

    return execute_pipeline(
        pipeline=preset['pipeline'],
        environment_dict=preset['environment_dict'],
        run_config=run_config if run_config is not None else preset['run_config'],
    )


def invoke_executor_on_plan(pipeline_context, execution_plan, step_keys_to_execute=None):
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
    check.invariant(pipeline_context.run_storage)

    if not pipeline_context.run_storage.is_persistent:
        raise DagsterInvariantViolationError(
            'Cannot perform reexecution with non persistent run storage.'
        )

    previous_run_id = run_config.reexecution_config.previous_run_id

    if not pipeline_context.run_storage.has_run(previous_run_id):
        raise DagsterRunNotFoundError(
            'Run id {} set as previous run id was not found in run storage'.format(previous_run_id),
            invalid_run_id=previous_run_id,
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


def execute_plan(execution_plan, environment_dict=None, run_config=None, step_keys_to_execute=None):
    '''This is the entry point of dagster-graphql executions. For the dagster CLI entry point, see
    execute_pipeline() above.
    '''
    check.inst_param(execution_plan, 'execution_plan', ExecutionPlan)
    environment_dict = check.opt_dict_param(environment_dict, 'environment_dict')
    run_config = check_run_config_param(run_config, execution_plan.pipeline_def)
    check.opt_list_param(step_keys_to_execute, 'step_keys_to_execute', of_type=str)

    if step_keys_to_execute:
        for step_key in step_keys_to_execute:
            if not execution_plan.has_step(step_key):
                raise DagsterExecutionStepNotFoundError(
                    'Execution plan does not contain step "{}"'.format(step_key), step_key=step_key
                )

    with scoped_pipeline_context(
        execution_plan.pipeline_def, environment_dict, run_config
    ) as pipeline_context:

        _setup_reexecution(run_config, pipeline_context, execution_plan)

        return list(invoke_executor_on_plan(pipeline_context, execution_plan, step_keys_to_execute))


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


class ExecutionSelector(object):
    def __init__(self, name, solid_subset=None):
        self.name = check.str_param(name, 'name')
        if solid_subset is None:
            self.solid_subset = None
        else:
            self.solid_subset = check.opt_list_param(solid_subset, 'solid_subset', of_type=str)
