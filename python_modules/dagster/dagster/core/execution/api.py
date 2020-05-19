import time
import warnings

from dagster import check
from dagster.core.definitions import (
    ExecutablePipeline,
    PartitionSetDefinition,
    PipelineDefinition,
    SystemStorageData,
)
from dagster.core.definitions.executable import InMemoryExecutablePipeline
from dagster.core.errors import DagsterInvariantViolationError
from dagster.core.events import DagsterEvent
from dagster.core.execution.context.system import SystemPipelineExecutionContext
from dagster.core.execution.plan.execute_plan import inner_plan_execution_iterator
from dagster.core.execution.plan.plan import ExecutionPlan
from dagster.core.execution.retries import Retries
from dagster.core.instance import DagsterInstance
from dagster.core.storage.pipeline_run import PipelineRun, PipelineRunStatus
from dagster.core.system_config.objects import EnvironmentConfig
from dagster.core.telemetry import telemetry_wrapper
from dagster.core.utils import make_new_backfill_id, make_new_run_id
from dagster.utils import merge_dicts

from .config import RunConfig
from .context_creation_pipeline import pipeline_initialization_manager, scoped_pipeline_context
from .results import PipelineExecutionResult


def create_execution_plan(pipeline, environment_dict=None, mode=None, step_keys_to_execute=None):
    # backcompat
    if isinstance(pipeline, PipelineDefinition):
        pipeline = InMemoryExecutablePipeline(pipeline)

    check.inst_param(pipeline, 'pipeline', ExecutablePipeline)
    pipeline_def = pipeline.get_definition()

    environment_dict = check.opt_dict_param(environment_dict, 'environment_dict', key_type=str)
    mode = check.opt_str_param(mode, 'mode', default=pipeline_def.get_default_mode_name())
    check.opt_list_param(step_keys_to_execute, 'step_keys_to_execute', of_type=str)

    environment_config = EnvironmentConfig.build(pipeline_def, environment_dict, mode=mode)

    return ExecutionPlan.build(
        pipeline, environment_config, mode=mode, step_keys_to_execute=step_keys_to_execute
    )


def _pipeline_execution_iterator(pipeline_context, execution_plan, retries=None):
    '''A complete execution of a pipeline. Yields pipeline start, success,
    and failure events.

    Args:
        pipeline_context (SystemPipelineExecutionContext):
        execution_plan (ExecutionPlan):
        retries (None): Must be None. This is to align the signature of
            `_pipeline_execution_iterator` with that of
            `dagster.core.execution.plan.execute_plan.inner_plan_execution_iterator` so the same
            machinery in _ExecuteRunWithPlanIterable can call them without unpleasant workarounds.
            (Default: None)
    '''
    check.inst_param(pipeline_context, 'pipeline_context', SystemPipelineExecutionContext)
    check.inst_param(execution_plan, 'execution_plan', ExecutionPlan)
    check.invariant(
        retries is None, 'Programming error: Retries not supported in _pipeline_execution_iterator'
    )
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
    check.inst_param(pipeline, 'pipeline', ExecutablePipeline)
    check.inst_param(pipeline_run, 'pipeline_run', PipelineRun)
    check.inst_param(instance, 'instance', DagsterInstance)
    check.invariant(pipeline_run.status == PipelineRunStatus.NOT_STARTED)

    execution_plan = create_execution_plan(
        pipeline,
        environment_dict=pipeline_run.environment_dict,
        mode=pipeline_run.mode,
        step_keys_to_execute=pipeline_run.step_keys_to_execute,
    )

    return iter(
        _ExecuteRunWithPlanIterable(
            execution_plan=execution_plan,
            pipeline_run=pipeline_run,
            instance=instance,
            iterator=_pipeline_execution_iterator,
            environment_dict=pipeline_run.environment_dict,
            retries=None,
            raise_on_error=False,
        )
    )


def execute_run(pipeline, pipeline_run, instance, raise_on_error=False):
    '''Executes an existing pipeline run synchronously.

    Synchronous version of execute_run_iterator.

    Args:
        pipeline (Union[ExecutablePipeline, PipelineDefinition]): The pipeline to execute.
        pipeline_run (PipelineRun): The run to execute
        instance (DagsterInstance): The instance in which the run has been created.
        raise_on_error (Optional[bool]): Whether or not to raise exceptions when they occur.
            Defaults to ``False``.

    Returns:
        PipelineExecutionResult: The result of the execution.
    '''
    if isinstance(pipeline, PipelineDefinition):
        pipeline = InMemoryExecutablePipeline(pipeline)

    check.inst_param(pipeline, 'pipeline', ExecutablePipeline)
    pipeline_def = pipeline.get_definition()

    check.inst_param(pipeline_run, 'pipeline_run', PipelineRun)
    check.inst_param(instance, 'instance', DagsterInstance)
    check.invariant(pipeline_run.status == PipelineRunStatus.NOT_STARTED)

    execution_plan = create_execution_plan(
        pipeline,
        environment_dict=pipeline_run.environment_dict,
        mode=pipeline_run.mode,
        step_keys_to_execute=pipeline_run.step_keys_to_execute,
    )

    _execute_run_iterable = _ExecuteRunWithPlanIterable(
        execution_plan=execution_plan,
        pipeline_run=pipeline_run,
        instance=instance,
        iterator=_pipeline_execution_iterator,
        environment_dict=pipeline_run.environment_dict,
        retries=None,
        raise_on_error=raise_on_error,
    )
    event_list = list(_execute_run_iterable)
    pipeline_context = _execute_run_iterable.pipeline_context

    return PipelineExecutionResult(
        pipeline_def,
        pipeline_run.run_id,
        event_list,
        lambda: scoped_pipeline_context(
            execution_plan,
            pipeline_run.environment_dict,
            pipeline_run,
            instance,
            system_storage_data=SystemStorageData(
                intermediates_manager=pipeline_context.intermediates_manager,
                file_manager=pipeline_context.file_manager,
            ),
        ),
    )


class _ExecuteRunWithPlanIterable(object):
    '''Utility class to consolidate execution logic.

    This is a class and not a function because, e.g., in constructing a `scoped_pipeline_context`
    for `PipelineExecutionResult`, we need to pull out the `pipeline_context` after we're done
    yielding events. This broadly follows a pattern we make use of in other places,
    cf. `dagster.utils.EventGenerationManager`.
    '''

    def __init__(
        self,
        execution_plan,
        pipeline_run,
        instance,
        iterator,
        environment_dict,
        retries,
        raise_on_error,
    ):
        self.execution_plan = check.inst_param(execution_plan, 'execution_plan', ExecutionPlan)
        self.pipeline_run = check.inst_param(pipeline_run, 'pipeline_run', PipelineRun)
        self.instance = check.inst_param(instance, 'instance', DagsterInstance)
        self.iterator = check.callable_param(iterator, 'iterator')
        self.environment_dict = (
            check.opt_dict_param(environment_dict, 'environment_dict')
            or self.pipeline_run.environment_dict
        )
        self.retries = check.opt_inst_param(retries, 'retries', Retries)
        self.raise_on_error = check.bool_param(raise_on_error, 'raise_on_error')
        self.pipeline_context = None

    def __iter__(self):
        initialization_manager = pipeline_initialization_manager(
            self.execution_plan,
            self.environment_dict,
            self.pipeline_run,
            self.instance,
            raise_on_error=self.raise_on_error,
        )
        for event in initialization_manager.generate_setup_events():
            yield event
        self.pipeline_context = initialization_manager.get_object()
        generator_closed = False
        try:
            if self.pipeline_context:  # False if we had a pipeline init failure
                for event in self.iterator(
                    execution_plan=self.execution_plan,
                    pipeline_context=self.pipeline_context,
                    retries=self.retries,
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


def _check_execute_pipeline_args(
    fn_name, pipeline, environment_dict, mode, preset, tags, run_config, instance
):
    # backcompat
    if isinstance(pipeline, PipelineDefinition):
        pipeline = InMemoryExecutablePipeline(pipeline)

    check.inst_param(pipeline, 'pipeline', ExecutablePipeline)
    pipeline_def = pipeline.get_definition()

    environment_dict = check.opt_dict_param(environment_dict, 'environment_dict')

    check.opt_str_param(mode, 'mode')
    check.opt_str_param(preset, 'preset')
    check.invariant(
        not (mode is not None and preset is not None),
        'You may set only one of `mode` (got {mode}) or `preset` (got {preset}).'.format(
            mode=mode, preset=preset
        ),
    )

    tags = check.opt_dict_param(tags, 'tags', key_type=str)

    run_config = check.opt_inst_param(run_config, 'run_config', RunConfig, default=RunConfig())

    if preset is not None:
        pipeline_preset = pipeline_def.get_preset(preset)

        check.invariant(
            run_config.mode is None or pipeline_preset.mode == run_config.mode,
            'The mode set in preset \'{preset}\' (\'{preset_mode}\') does not agree with the mode '
            'set in the `run_config` (\'{run_config_mode}\')'.format(
                preset=preset, preset_mode=pipeline_preset.mode, run_config_mode=run_config.mode
            ),
        )

        if pipeline_preset.environment_dict is not None:
            check.invariant(
                (not environment_dict) or (pipeline_preset.environment_dict == environment_dict),
                'The environment set in preset \'{preset}\' does not agree with the environment '
                'passed in the `environment_dict` argument.'.format(preset=preset),
            )

            environment_dict = pipeline_preset.environment_dict

        if pipeline_preset.solid_subset is not None:
            pipeline = pipeline.build_sub_pipeline(pipeline_preset.solid_subset)

        check.invariant(
            mode is None or mode == pipeline_preset.mode,
            'Mode {mode} does not agree with the mode set in preset \'{preset}\': '
            '(\'{preset_mode}\')'.format(
                preset=preset, preset_mode=pipeline_preset.mode, mode=mode
            ),
        )

        mode = pipeline_preset.mode

    if run_config.mode is not None or run_config.tags:
        warnings.warn(
            (
                'In 0.8.0, the use of `run_config` to set pipeline mode and tags will be '
                'deprecated. Please use the `mode` and `tags` arguments to `{fn_name}` '
                'instead.'
            ).format(fn_name=fn_name)
        )

    if run_config.mode is not None:
        if mode is not None:
            check.invariant(
                run_config.mode == mode,
                'Mode \'{mode}\' does not agree with the mode set in the `run_config`: '
                '\'{run_config_mode}\''.format(mode=mode, run_config_mode=run_config.mode),
            )
        mode = run_config.mode

    if mode is not None:
        if not pipeline_def.has_mode_definition(mode):
            raise DagsterInvariantViolationError(
                (
                    'You have attempted to execute pipeline {name} with mode {mode}. '
                    'Available modes: {modes}'
                ).format(
                    name=pipeline_def.name, mode=mode, modes=pipeline_def.available_modes,
                )
            )
    else:
        if pipeline_def.is_multi_mode:
            raise DagsterInvariantViolationError(
                (
                    'Pipeline {name} has multiple modes (Available modes: {modes}) and you have '
                    'attempted to execute it without specifying a mode. Set '
                    'mode property on the PipelineRun object.'
                ).format(name=pipeline_def.name, modes=pipeline_def.available_modes)
            )
        mode = pipeline_def.get_default_mode_name()

    tags = merge_dicts(merge_dicts(pipeline_def.tags, run_config.tags or {}), tags)

    check.opt_inst_param(instance, 'instance', DagsterInstance)
    instance = instance or DagsterInstance.ephemeral()

    return pipeline, environment_dict, instance, mode, tags, run_config


def execute_pipeline_iterator(
    pipeline,
    environment_dict=None,
    mode=None,
    preset=None,
    tags=None,
    run_config=None,
    instance=None,
):
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
        mode (Optional[str]): The name of the pipeline mode to use. You may not set both ``mode``
            and ``preset``.
        preset (Optional[str]): The name of the pipeline preset to use. You may not set both
            ``mode`` and ``preset``.
        tags (Optional[Dict[str, Any]]): Arbitrary key-value pairs that will be added to pipeline
            logs.
        run_config (Optional[RunConfig]): Optionally specifies additional config options for
            pipeline execution.

            Deprecation notice:  In 0.8.0, the use of `run_config` to set mode, tags, and step keys
            will be deprecated. In the interim, if you set a mode using `run_config`, this must
            match any mode set using `mode` or `preset`. If you set tags using `run_config`, any
            tags set using `tags` will take precedence. If you set step keys, these must be
            compatible with any solid subset specified using `preset`.
        instance (Optional[DagsterInstance]): The instance to execute against. If this is ``None``,
            an ephemeral instance will be used, and no artifacts will be persisted from the run.

    Returns:
      Iterator[DagsterEvent]: The stream of events resulting from pipeline execution.
    '''
    (pipeline, environment_dict, instance, mode, tags, run_config,) = _check_execute_pipeline_args(
        'execute_pipeline_iterator',
        pipeline=pipeline,
        environment_dict=environment_dict,
        mode=mode,
        preset=preset,
        tags=tags,
        run_config=run_config,
        instance=instance,
    )

    pipeline_run = instance.create_run_for_pipeline(
        pipeline_def=pipeline.get_definition(),
        run_id=run_config.run_id,
        environment_dict=environment_dict,
        mode=mode,
        solid_subset=pipeline.get_definition().selector.solid_subset,
        step_keys_to_execute=run_config.step_keys_to_execute,
        tags=tags,
        root_run_id=run_config.previous_run_id,
        parent_run_id=run_config.previous_run_id,
    )

    return execute_run_iterator(pipeline, pipeline_run, instance)


@telemetry_wrapper
def execute_pipeline(
    pipeline,
    environment_dict=None,
    mode=None,
    preset=None,
    tags=None,
    run_config=None,
    instance=None,
    raise_on_error=True,
):
    '''Execute a pipeline synchronously.

    Users will typically call this API when testing pipeline execution, or running standalone
    scripts.

    Parameters:
        pipeline (PipelineDefinition): The pipeline to execute.
        environment_dict (Optional[dict]): The environment configuration that parametrizes this run,
            as a dict.
        mode (Optional[str]): The name of the pipeline mode to use. You may not set both ``mode``
            and ``preset``.
        preset (Optional[str]): The name of the pipeline preset to use. You may not set both
            ``mode`` and ``preset``.
        tags (Optional[Dict[str, Any]]): Arbitrary key-value pairs that will be added to pipeline
            logs.
        run_config (Optional[RunConfig]): Optionally specifies additional config options for
            pipeline execution.

            Deprecation notice: In 0.8.0, the use of `run_config` to set mode, tags, and step keys
            will be deprecated. In the interim, if you set a mode using `run_config`, this must
            match any mode set using `mode` or `preset`. If you set tags using `run_config`, any
            tags set using `tags` will take precedence. If you set step keys, these must be
            compatible with any solid subset specified using `preset`.
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
    (pipeline, environment_dict, instance, mode, tags, run_config,) = _check_execute_pipeline_args(
        'execute_pipeline',
        pipeline=pipeline,
        environment_dict=environment_dict,
        mode=mode,
        preset=preset,
        tags=tags,
        run_config=run_config,
        instance=instance,
    )

    pipeline_def = pipeline.get_definition()

    pipeline_run = instance.create_run_for_pipeline(
        pipeline_def=pipeline_def,
        run_id=run_config.run_id,
        environment_dict=environment_dict,
        mode=mode,
        solid_subset=pipeline_def.selector.solid_subset,
        step_keys_to_execute=run_config.step_keys_to_execute,
        tags=tags,
        root_run_id=run_config.previous_run_id,
        parent_run_id=run_config.previous_run_id,
    )

    return execute_run(pipeline, pipeline_run, instance, raise_on_error=raise_on_error)


def execute_plan_iterator(
    execution_plan, pipeline_run, instance, retries=None, environment_dict=None,
):
    check.inst_param(execution_plan, 'execution_plan', ExecutionPlan)
    check.inst_param(pipeline_run, 'pipeline_run', PipelineRun)
    check.inst_param(instance, 'instance', DagsterInstance)
    retries = check.opt_inst_param(retries, 'retries', Retries, Retries.disabled_mode())
    environment_dict = check.opt_dict_param(environment_dict, 'environment_dict')

    return iter(
        _ExecuteRunWithPlanIterable(
            execution_plan=execution_plan,
            environment_dict=environment_dict,
            pipeline_run=pipeline_run,
            instance=instance,
            retries=retries,
            iterator=inner_plan_execution_iterator,
            raise_on_error=False,
        )
    )


def execute_plan(
    execution_plan, instance, pipeline_run, environment_dict=None, retries=None,
):
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
            environment_dict=partition_set.environment_dict_for_partition(partition),
            mode='default',
            tags=merge_dicts(
                PipelineRun.tags_for_backfill_id(make_new_backfill_id()),
                partition_set.tags_for_partition(partition),
            ),
            status=PipelineRunStatus.NOT_STARTED,
        )

        # Remove once we can handle synchronous execution... currently limited by sqlite
        time.sleep(0.1)

        instance.launch_run(run.run_id)
