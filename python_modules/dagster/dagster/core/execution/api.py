import time

from dagster import check
from dagster.core.definitions import PartitionSetDefinition, PipelineDefinition, SystemStorageData
from dagster.core.definitions.pipeline import ExecutionSelector
from dagster.core.errors import DagsterInvariantViolationError
from dagster.core.events import DagsterEvent
from dagster.core.execution.context.system import SystemPipelineExecutionContext
from dagster.core.execution.plan.execute import inner_plan_execution_iterator
from dagster.core.execution.plan.plan import ExecutionPlan
from dagster.core.execution.retries import Retries
from dagster.core.instance import DagsterInstance
from dagster.core.storage.pipeline_run import PipelineRun, PipelineRunStatus
from dagster.core.system_config.objects import EnvironmentConfig
from dagster.core.telemetry import telemetry_wrapper
from dagster.core.utils import make_new_backfill_id, make_new_run_id
from dagster.utils import merge_dicts

from .config import IRunConfig, RunConfig
from .context_creation_pipeline import pipeline_initialization_manager, scoped_pipeline_context
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

    run_config = (
        run_config.with_mode(pipeline_def.get_default_mode_name())
        if run_config
        else RunConfig(mode=pipeline_def.get_default_mode_name())
    )

    if pipeline_def.tags:
        return run_config.with_tags(**merge_dicts(pipeline_def.tags, run_config.tags))

    return run_config


def create_execution_plan(pipeline, environment_dict=None, run_config=None):
    check.inst_param(pipeline, 'pipeline', PipelineDefinition)
    environment_dict = check.opt_dict_param(environment_dict, 'environment_dict', key_type=str)
    run_config = check.opt_inst_param(run_config, 'run_config', IRunConfig, RunConfig())

    environment_config = EnvironmentConfig.build(pipeline, environment_dict, run_config)

    return ExecutionPlan.build(pipeline, environment_config, run_config)


def _pipeline_execution_iterator(pipeline_context, execution_plan, pipeline_run):
    '''A complete execution of a pipeline. Yields pipeline start, success,
    and failure events.
    '''
    check.inst_param(pipeline_context, 'pipeline_context', SystemPipelineExecutionContext)
    check.inst_param(execution_plan, 'execution_plan', ExecutionPlan)
    check.inst_param(pipeline_run, 'pipeline_run', PipelineRun)
    yield DagsterEvent.pipeline_start(pipeline_context)

    pipeline_success = True
    generator_closed = False
    try:
        for event in pipeline_context.executor_config.get_engine().execute(
            pipeline_context, execution_plan
        ):
            if event.is_step_failure:
                pipeline_success = False
            yield event
    except GeneratorExit:
        # Shouldn't happen, but avoid runtime-exception in case this generator gets GC-ed
        # (see https://amir.rachum.com/blog/2017/03/03/generator-cleanup/).
        generator_closed = True
        pipeline_success = False
        raise
    except (Exception, KeyboardInterrupt):
        pipeline_success = False
        raise  # finally block will run before this is re-raised
    finally:
        if pipeline_success:
            event = DagsterEvent.pipeline_success(pipeline_context)
        else:
            event = DagsterEvent.pipeline_failure(pipeline_context)
        if not generator_closed:
            yield event


def execute_run_iterator(pipeline, pipeline_run, instance):
    check.inst_param(pipeline, 'pipeline', PipelineDefinition)
    instance = check.inst_param(instance, 'instance', DagsterInstance)
    check.invariant(pipeline_run.status == PipelineRunStatus.NOT_STARTED)

    execution_plan = create_execution_plan(
        pipeline, environment_dict=pipeline_run.environment_dict, run_config=pipeline_run
    )

    initialization_manager = pipeline_initialization_manager(
        pipeline, pipeline_run.environment_dict, pipeline_run, instance, execution_plan
    )
    for event in initialization_manager.generate_setup_events():
        yield event
    pipeline_context = initialization_manager.get_object()
    generator_closed = False
    try:
        if pipeline_context:
            for event in _pipeline_execution_iterator(
                pipeline_context, execution_plan, pipeline_run
            ):
                yield event
    except GeneratorExit:
        # Shouldn't happen, but avoid runtime-exception in case this generator gets GC-ed
        # (see https://amir.rachum.com/blog/2017/03/03/generator-cleanup/).
        generator_closed = True
        raise
    finally:
        for event in initialization_manager.generate_teardown_events():
            if not generator_closed:
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
        environment_dict (Optional[dict]): The environment configuration that parametrizes this run,
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


@telemetry_wrapper
def execute_pipeline(
    pipeline, environment_dict=None, run_config=None, instance=None, raise_on_error=True
):
    '''Execute a pipeline synchronously.

    Users will typically call this API when testing pipeline execution, or running standalone
    scripts.

    Parameters:
        pipeline (PipelineDefinition): The pipeline to execute.
        environment_dict (Optional[dict]): The environment configuration that parametrizes this run,
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

    initialization_manager = pipeline_initialization_manager(
        pipeline,
        environment_dict,
        pipeline_run,
        instance,
        execution_plan,
        raise_on_error=raise_on_error,
    )
    event_list = list(initialization_manager.generate_setup_events())
    pipeline_context = initialization_manager.get_object()
    try:
        if pipeline_context:
            event_list.extend(
                _pipeline_execution_iterator(pipeline_context, execution_plan, pipeline_run)
            )
    finally:
        event_list.extend(initialization_manager.generate_teardown_events())
    return PipelineExecutionResult(
        pipeline,
        run_config.run_id,
        event_list,
        lambda: scoped_pipeline_context(
            pipeline,
            environment_dict,
            pipeline_run,
            instance,
            execution_plan,
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


def execute_pipeline_with_mode(
    pipeline, mode, environment_dict=None, instance=None, raise_on_error=True
):
    '''Execute a pipeline synchronously, with the given mode.

    Parameters:
        pipeline (PipelineDefinition): The pipeline to execute.
        mode (str): The mode to use.
        environment_dict (Optional[dict]): The environment configuration that parametrizes this run,
            as a dict.
        instance (Optional[DagsterInstance]): The instance to execute against. If this is ``None``,
            an ephemeral instance will be used, and no artifacts will be persisted from the run.
            (default: ``None``)
        raise_on_error (Optional[bool]): Whether or not to raise exceptions when they occur.
            Default is ``True``, since this is the most useful behavior in test.

    Returns:
      :py:class:`PipelineExecutionResult`: The result of pipeline execution.
    '''
    check.inst_param(pipeline, 'pipeline', PipelineDefinition)
    check.str_param(mode, 'mode')
    check.opt_dict_param(environment_dict, 'environment_dict')
    check.opt_inst_param(instance, 'instance', DagsterInstance)
    return execute_pipeline(
        pipeline, environment_dict, RunConfig(mode=mode), instance, raise_on_error=raise_on_error,
    )


def execute_plan_iterator(
    execution_plan, pipeline_run, instance, retries=None, environment_dict=None
):
    check.inst_param(execution_plan, 'execution_plan', ExecutionPlan)
    check.inst_param(pipeline_run, 'pipeline_run', PipelineRun)
    check.inst_param(instance, 'instance', DagsterInstance)
    retries = check.opt_inst_param(retries, 'retries', Retries, Retries.disabled_mode())
    environment_dict = check.opt_dict_param(environment_dict, 'environment_dict')

    initialization_manager = pipeline_initialization_manager(
        execution_plan.pipeline_def, environment_dict, pipeline_run, instance, execution_plan
    )
    for event in initialization_manager.generate_setup_events():
        yield event

    pipeline_context = initialization_manager.get_object()

    generator_closed = False
    try:
        if pipeline_context:
            for event in inner_plan_execution_iterator(
                pipeline_context, execution_plan=execution_plan, retries=retries
            ):
                yield event
    except GeneratorExit:
        # Shouldn't happen, but avoid runtime-exception in case this generator gets GC-ed
        # (see https://amir.rachum.com/blog/2017/03/03/generator-cleanup/).
        generator_closed = True
        raise
    finally:
        for event in initialization_manager.generate_teardown_events():
            if not generator_closed:
                yield event


def execute_plan(execution_plan, instance, pipeline_run, environment_dict=None, retries=None):
    '''This is the entry point of dagster-graphql executions. For the dagster CLI entry point, see
    execute_pipeline() above.
    '''
    check.inst_param(execution_plan, 'execution_plan', ExecutionPlan)
    check.inst_param(instance, 'instance', DagsterInstance)
    check.inst_param(pipeline_run, 'pipeline_run', PipelineRun)
    environment_dict = check.opt_dict_param(environment_dict, 'environment_dict')
    check.opt_inst_param(retries, 'retries', Retries)

    return list(
        execute_plan_iterator(
            execution_plan=execution_plan,
            environment_dict=environment_dict,
            pipeline_run=pipeline_run,
            instance=instance,
            retries=retries,
        )
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
            step_keys_to_execute=run_config.step_keys_to_execute,
            tags=run_config.tags,
            status=PipelineRunStatus.NOT_STARTED,
            previous_run_id=run_config.previous_run_id,
        )
    )


def execute_partition_set(partition_set, partition_filter, instance=None):
    '''Programatically perform a backfill over a partition set

    Arguments:
        partition_set (PartitionSet): The base partition set to run the backfill over
        partition_filter (Callable[[List[Partition]]], List[Partition]): A function that takes
            a list of partitions and returns a filtered list of partitions to run the backfill
            over.
        instance (DagsterInstance): The instance to use to perform the backfill
    '''
    check.inst_param(partition_set, 'partition_set', PartitionSetDefinition)
    check.callable_param(partition_filter, 'partition_filter')
    check.inst_param(instance, 'instance', DagsterInstance)

    candidate_partitions = partition_set.get_partitions()
    partitions = partition_filter(candidate_partitions)

    instance = instance or DagsterInstance.ephemeral()

    for partition in partitions:
        run = PipelineRun(
            pipeline_name=partition_set.pipeline_name,
            run_id=make_new_run_id(),
            selector=ExecutionSelector(partition_set.pipeline_name),
            environment_dict=partition_set.environment_dict_for_partition(partition),
            mode='default',
            tags=merge_dicts(
                {'dagster/backfill': make_new_backfill_id()},
                partition_set.tags_for_partition(partition),
            ),
            status=PipelineRunStatus.NOT_STARTED,
        )

        # Remove once we can handle synchronous execution... currently limited by sqlite
        time.sleep(0.1)

        instance.launch_run(run)
