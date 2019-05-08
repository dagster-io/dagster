'''
Naming conventions:

For public functions:

execute_*

These represent functions which do purely in-memory compute. They will evaluate expectations
the core transform, and exercise all logging and metrics tracking (outside of outputs), but they
will not invoke *any* outputs (and their APIs don't allow the user to).


'''

# too many lines
# pylint: disable=C0302

from dagster import check

from dagster.core.definitions import PipelineDefinition

from dagster.core.errors import (
    DagsterExecutionStepNotFoundError,
    DagsterInvariantViolationError,
    DagsterRunNotFoundError,
    DagsterStepOutputNotFoundError,
)

from dagster.core.events import DagsterEvent, DagsterEventType

from dagster.core.execution_plan.plan import ExecutionPlan
from dagster.core.engine.engine_multiprocessing import MultiprocessingEngine
from dagster.core.engine.engine_inprocess import InProcessEngine

from .context_creation_pipeline import (
    construct_intermediates_manager,
    create_environment_config,
    scoped_pipeline_context,
    yield_pipeline_execution_context,
)

from .execution_context import (
    RunConfig,
    InProcessExecutorConfig,
    MultiprocessExecutorConfig,
    SystemPipelineExecutionContext,
)


from .results import PipelineExecutionResult


def check_run_config_param(run_config, pipeline_def):
    check.inst_param(pipeline_def, 'pipeline_def', PipelineDefinition)

    if run_config and run_config.mode:
        if pipeline_def.is_modeless:
            raise DagsterInvariantViolationError(
                (
                    'You have attempted to execute pipeline {name} with mode {mode} '
                    'when it has no modes defined'
                ).format(name=pipeline_def.name, mode=run_config.mode)
            )

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
        if not (pipeline_def.is_modeless or pipeline_def.is_single_mode):
            raise DagsterInvariantViolationError(
                (
                    'Pipeline {name} has multiple modes (Avaiable modes: {modes}) and you have '
                    'attempted to execute it without specifying a mode. Set '
                    'mode property on the RunConfig object.'
                ).format(name=pipeline_def.name, modes=pipeline_def.available_modes)
            )

    return (
        check.inst_param(run_config, 'run_config', RunConfig)
        if run_config
        else RunConfig(executor_config=InProcessExecutorConfig())
    )


def create_execution_plan(pipeline, environment_dict=None, mode=None):
    check.inst_param(pipeline, 'pipeline', PipelineDefinition)
    environment_dict = check.opt_dict_param(environment_dict, 'environment_dict', key_type=str)
    check.opt_str_param(mode, 'mode')
    environment_config = create_environment_config(pipeline, environment_dict)
    return ExecutionPlan.build(pipeline, environment_config)


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
        pipeline_context.pipeline_def, pipeline_context.environment_config
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

    pipeline_context.log.debug(
        'About to execute the compute node graph in the following order {order}'.format(
            order=[step.key for step in steps]
        )
    )

    check.invariant(len(steps[0].step_inputs) == 0)

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
    environment_config = create_environment_config(pipeline, environment_dict)
    intermediates_manager = construct_intermediates_manager(
        run_config, environment_config, pipeline
    )

    with scoped_pipeline_context(
        pipeline, environment_config, run_config, intermediates_manager
    ) as pipeline_context:
        return _execute_pipeline_iterator(pipeline_context)


def execute_pipeline(pipeline, environment_dict=None, run_config=None):
    '''
    "Synchronous" version of :py:func:`execute_pipeline_iterator`.

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
    environment_config = create_environment_config(pipeline, environment_dict, run_config.mode)
    intermediates_manager = construct_intermediates_manager(
        run_config, environment_config, pipeline
    )

    with scoped_pipeline_context(
        pipeline, environment_config, run_config, intermediates_manager
    ) as pipeline_context:
        event_list = list(_execute_pipeline_iterator(pipeline_context))

    return PipelineExecutionResult(
        pipeline,
        run_config.run_id,
        event_list,
        lambda: scoped_pipeline_context(
            pipeline, environment_config, run_config, intermediates_manager
        ),
    )


def invoke_executor_on_plan(pipeline_context, execution_plan, step_keys_to_execute=None):
    if step_keys_to_execute:
        for step_key in step_keys_to_execute:
            if not execution_plan.has_step(step_key):
                raise DagsterExecutionStepNotFoundError(step_key=step_key)

    # Toggle engine based on executor config supplied by the pipeline context
    def get_engine_for_config(cfg):
        if isinstance(cfg, InProcessExecutorConfig):
            return InProcessEngine
        elif isinstance(cfg, MultiprocessExecutorConfig):
            return MultiprocessingEngine
        else:
            check.failed('Unsupported config {}'.format(cfg))

    # Engine execution returns a generator of yielded events, so returning here means this function
    # also returns a generator
    return get_engine_for_config(pipeline_context.executor_config).execute(
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

    with yield_pipeline_execution_context(
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
