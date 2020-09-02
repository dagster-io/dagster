from contextlib import contextmanager

from dagster import check
from dagster.core.definitions import ExecutablePipeline, PipelineDefinition, SystemStorageData
from dagster.core.definitions.executable import InMemoryExecutablePipeline
from dagster.core.definitions.pipeline import PipelineSubsetDefinition
from dagster.core.errors import DagsterInvariantViolationError
from dagster.core.events import DagsterEvent
from dagster.core.execution.context.system import SystemPipelineExecutionContext
from dagster.core.execution.plan.execute_plan import inner_plan_execution_iterator
from dagster.core.execution.plan.plan import ExecutionPlan
from dagster.core.execution.retries import Retries
from dagster.core.instance import DagsterInstance
from dagster.core.selector import parse_step_selection
from dagster.core.storage.pipeline_run import PipelineRun, PipelineRunStatus
from dagster.core.system_config.objects import EnvironmentConfig
from dagster.core.telemetry import log_repo_stats, telemetry_wrapper
from dagster.core.utils import str_format_set
from dagster.utils import merge_dicts
from dagster.utils.backcompat import canonicalize_backcompat_args

from .context_creation_pipeline import (
    ExecutionContextManager,
    PipelineExecutionContextManager,
    PlanExecutionContextManager,
    scoped_pipeline_context,
)
from .results import PipelineExecutionResult

## Brief guide to the execution APIs
# | function name               | operates over      | sync  | supports    | creates new PipelineRun |
# |                             |                    |       | reexecution | in instance             |
# | --------------------------- | ------------------ | ----- | ----------- | ----------------------- |
# | execute_pipeline_iterator   | ExecutablePipeline | async | no          | yes                     |
# | execute_pipeline            | ExecutablePipeline | sync  | no          | yes                     |
# | execute_run_iterator        | PipelineRun        | async | (1)         | no                      |
# | execute_run                 | PipelineRun        | sync  | (1)         | no                      |
# | execute_plan_iterator       | ExecutionPlan      | async | (2)         | no                      |
# | execute_plan                | ExecutionPlan      | sync  | (2)         | no                      |
# | reexecute_pipeline          | ExecutablePipeline | sync  | yes         | yes                     |
# | reexecute_pipeline_iterator | ExecutablePipeline | async | yes         | yes                     |
#
# Notes on reexecution support:
# (1) The appropriate bits must be set on the PipelineRun passed to this function. Specifically,
#     parent_run_id and root_run_id must be set and consistent, and if a solids_to_execute or
#     step_keys_to_execute are set they must be consistent with the parent and root runs.
# (2) As for (1), but the ExecutionPlan passed must also agree in all relevant bits.


def execute_run_iterator(pipeline, pipeline_run, instance):
    check.inst_param(pipeline, "pipeline", ExecutablePipeline)
    check.inst_param(pipeline_run, "pipeline_run", PipelineRun)
    check.inst_param(instance, "instance", DagsterInstance)
    check.invariant(pipeline_run.status == PipelineRunStatus.NOT_STARTED)

    if pipeline_run.solids_to_execute:
        pipeline_def = pipeline.get_definition()
        if isinstance(pipeline_def, PipelineSubsetDefinition):
            check.invariant(
                pipeline_run.solids_to_execute == pipeline.solids_to_execute,
                "Cannot execute PipelineRun with solids_to_execute {solids_to_execute} that conflicts "
                "with pipeline subset {pipeline_solids_to_execute}.".format(
                    pipeline_solids_to_execute=str_format_set(pipeline.solids_to_execute),
                    solids_to_execute=str_format_set(pipeline_run.solids_to_execute),
                ),
            )
        else:
            # when `execute_run_iterator` is directly called, the sub pipeline hasn't been created
            # note that when we receive the solids to execute via PipelineRun, it won't support
            # solid selection query syntax
            pipeline = pipeline.subset_for_execution_from_existing_pipeline(
                pipeline_run.solids_to_execute
            )
    execution_plan = create_execution_plan(
        pipeline,
        run_config=pipeline_run.run_config,
        mode=pipeline_run.mode,
        step_keys_to_execute=pipeline_run.step_keys_to_execute,
    )

    return iter(
        _ExecuteRunWithPlanIterable(
            execution_plan=execution_plan,
            iterator=_pipeline_execution_iterator,
            execution_context_manager=PipelineExecutionContextManager(
                execution_plan=execution_plan,
                pipeline_run=pipeline_run,
                instance=instance,
                run_config=pipeline_run.run_config,
                raise_on_error=False,
            ),
        )
    )


def execute_run(pipeline, pipeline_run, instance, raise_on_error=False):
    """Executes an existing pipeline run synchronously.

    Synchronous version of execute_run_iterator.

    Args:
        pipeline (ExecutablePipeline): The pipeline to execute.
        pipeline_run (PipelineRun): The run to execute
        instance (DagsterInstance): The instance in which the run has been created.
        raise_on_error (Optional[bool]): Whether or not to raise exceptions when they occur.
            Defaults to ``False``.

    Returns:
        PipelineExecutionResult: The result of the execution.
    """
    if isinstance(pipeline, PipelineDefinition):
        raise DagsterInvariantViolationError(
            "execute_run requires an ExecutablePipeline but received a PipelineDefinition "
            "directly instead. To support hand-off to other processes provide a "
            "ReconstructablePipeline which can be done using reconstructable(). For in "
            "process only execution you can use InMemoryExecutablePipeline."
        )

    check.inst_param(pipeline, "pipeline", ExecutablePipeline)
    check.inst_param(pipeline_run, "pipeline_run", PipelineRun)
    check.inst_param(instance, "instance", DagsterInstance)
    check.invariant(pipeline_run.status == PipelineRunStatus.NOT_STARTED)

    pipeline_def = pipeline.get_definition()
    if pipeline_run.solids_to_execute:
        if isinstance(pipeline_def, PipelineSubsetDefinition):
            check.invariant(
                pipeline_run.solids_to_execute == pipeline.solids_to_execute,
                "Cannot execute PipelineRun with solids_to_execute {solids_to_execute} that "
                "conflicts with pipeline subset {pipeline_solids_to_execute}.".format(
                    pipeline_solids_to_execute=str_format_set(pipeline.solids_to_execute),
                    solids_to_execute=str_format_set(pipeline_run.solids_to_execute),
                ),
            )
        else:
            # when `execute_run` is directly called, the sub pipeline hasn't been created
            # note that when we receive the solids to execute via PipelineRun, it won't support
            # solid selection query syntax
            pipeline = pipeline.subset_for_execution_from_existing_pipeline(
                pipeline_run.solids_to_execute
            )

    execution_plan = create_execution_plan(
        pipeline,
        run_config=pipeline_run.run_config,
        mode=pipeline_run.mode,
        step_keys_to_execute=pipeline_run.step_keys_to_execute,
    )

    _execute_run_iterable = _ExecuteRunWithPlanIterable(
        execution_plan=execution_plan,
        iterator=_pipeline_execution_iterator,
        execution_context_manager=PipelineExecutionContextManager(
            execution_plan=execution_plan,
            pipeline_run=pipeline_run,
            instance=instance,
            run_config=pipeline_run.run_config,
            raise_on_error=raise_on_error,
        ),
    )
    event_list = list(_execute_run_iterable)
    pipeline_context = _execute_run_iterable.pipeline_context

    return PipelineExecutionResult(
        pipeline.get_definition(),
        pipeline_run.run_id,
        event_list,
        lambda: scoped_pipeline_context(
            execution_plan,
            pipeline_run.run_config,
            pipeline_run,
            instance,
            intermediate_storage=pipeline_context.intermediate_storage,
            system_storage_data=SystemStorageData(
                intermediate_storage=pipeline_context.intermediate_storage,
                file_manager=pipeline_context.file_manager,
            ),
        ),
    )


def execute_pipeline_iterator(
    pipeline,
    run_config=None,
    mode=None,
    preset=None,
    tags=None,
    solid_selection=None,
    instance=None,
):
    """Execute a pipeline iteratively.

    Rather than package up the result of running a pipeline into a single object, like
    :py:func:`execute_pipeline`, this function yields the stream of events resulting from pipeline
    execution.

    This is intended to allow the caller to handle these events on a streaming basis in whatever
    way is appropriate.

    Parameters:
        pipeline (Union[ExecutablePipeline, PipelineDefinition]): The pipeline to execute.
        run_config (Optional[dict]): The environment configuration that parametrizes this run,
            as a dict.
        mode (Optional[str]): The name of the pipeline mode to use. You may not set both ``mode``
            and ``preset``.
        preset (Optional[str]): The name of the pipeline preset to use. You may not set both
            ``mode`` and ``preset``.
        tags (Optional[Dict[str, Any]]): Arbitrary key-value pairs that will be added to pipeline
            logs.
        solid_selection (Optional[List[str]]): A list of solid selection queries (including single
            solid names) to execute. For example:
            - ['some_solid']: select "some_solid" itself.
            - ['*some_solid']: select "some_solid" and all its ancestors (upstream dependencies).
            - ['*some_solid+++']: select "some_solid", all its ancestors, and its descendants
                (downstream dependencies) within 3 levels down.
            - ['*some_solid', 'other_solid_a', 'other_solid_b+']: select "some_solid" and all its
                ancestors, "other_solid_a" itself, and "other_solid_b" and its direct child solids.
        instance (Optional[DagsterInstance]): The instance to execute against. If this is ``None``,
            an ephemeral instance will be used, and no artifacts will be persisted from the run.

    Returns:
      Iterator[DagsterEvent]: The stream of events resulting from pipeline execution.
    """

    with _ephemeral_instance_if_missing(instance) as execute_instance:
        (
            pipeline,
            run_config,
            mode,
            tags,
            solids_to_execute,
            solid_selection,
        ) = _check_execute_pipeline_args(
            pipeline=pipeline,
            run_config=run_config,
            mode=mode,
            preset=preset,
            tags=tags,
            solid_selection=solid_selection,
        )

        pipeline_run = execute_instance.create_run_for_pipeline(
            pipeline_def=pipeline.get_definition(),
            run_config=run_config,
            mode=mode,
            solid_selection=solid_selection,
            solids_to_execute=solids_to_execute,
            tags=tags,
        )

        return execute_run_iterator(pipeline, pipeline_run, execute_instance)


@contextmanager
def _ephemeral_instance_if_missing(instance):
    if instance:
        yield instance
    else:
        with DagsterInstance.ephemeral() as ephemeral_instance:
            yield ephemeral_instance


def execute_pipeline(
    pipeline,
    run_config=None,
    mode=None,
    preset=None,
    tags=None,
    solid_selection=None,
    instance=None,
    raise_on_error=True,
):
    """Execute a pipeline synchronously.

    Users will typically call this API when testing pipeline execution, or running standalone
    scripts.

    Parameters:
        pipeline (Union[ExecutablePipeline, PipelineDefinition]): The pipeline to execute.
        run_config (Optional[dict]): The environment configuration that parametrizes this run,
            as a dict.
        mode (Optional[str]): The name of the pipeline mode to use. You may not set both ``mode``
            and ``preset``.
        preset (Optional[str]): The name of the pipeline preset to use. You may not set both
            ``mode`` and ``preset``.
        tags (Optional[Dict[str, Any]]): Arbitrary key-value pairs that will be added to pipeline
            logs.
        instance (Optional[DagsterInstance]): The instance to execute against. If this is ``None``,
            an ephemeral instance will be used, and no artifacts will be persisted from the run.
        raise_on_error (Optional[bool]): Whether or not to raise exceptions when they occur.
            Defaults to ``True``, since this is the most useful behavior in test.
        solid_selection (Optional[List[str]]): A list of solid selection queries (including single
            solid names) to execute. For example:
            - ['some_solid']: select "some_solid" itself.
            - ['*some_solid']: select "some_solid" and all its ancestors (upstream dependencies).
            - ['*some_solid+++']: select "some_solid", all its ancestors, and its descendants
                (downstream dependencies) within 3 levels down.
            - ['*some_solid', 'other_solid_a', 'other_solid_b+']: select "some_solid" and all its
                ancestors, "other_solid_a" itself, and "other_solid_b" and its direct child solids.

    Returns:
      :py:class:`PipelineExecutionResult`: The result of pipeline execution.

    For the asynchronous version, see :py:func:`execute_pipeline_iterator`.

    This is the entrypoint for dagster CLI execution. For the dagster-graphql entrypoint, see
    ``dagster.core.execution.api.execute_plan()``.
    """

    with _ephemeral_instance_if_missing(instance) as execute_instance:
        return _logged_execute_pipeline(
            pipeline,
            instance=execute_instance,
            run_config=run_config,
            mode=mode,
            preset=preset,
            tags=tags,
            solid_selection=solid_selection,
            raise_on_error=raise_on_error,
        )


@telemetry_wrapper
def _logged_execute_pipeline(
    pipeline,
    instance,
    run_config=None,
    mode=None,
    preset=None,
    tags=None,
    solid_selection=None,
    raise_on_error=True,
):
    check.inst_param(instance, "instance", DagsterInstance)
    (
        pipeline,
        run_config,
        mode,
        tags,
        solids_to_execute,
        solid_selection,
    ) = _check_execute_pipeline_args(
        pipeline=pipeline,
        run_config=run_config,
        mode=mode,
        preset=preset,
        tags=tags,
        solid_selection=solid_selection,
    )

    log_repo_stats(instance=instance, pipeline=pipeline, source="execute_pipeline")

    pipeline_run = instance.create_run_for_pipeline(
        pipeline_def=pipeline.get_definition(),
        run_config=run_config,
        mode=mode,
        solid_selection=solid_selection,
        solids_to_execute=solids_to_execute,
        tags=tags,
    )

    return execute_run(pipeline, pipeline_run, instance, raise_on_error=raise_on_error)


def reexecute_pipeline(
    pipeline,
    parent_run_id,
    run_config=None,
    step_selection=None,
    mode=None,
    preset=None,
    tags=None,
    instance=None,
    raise_on_error=True,
    step_keys_to_execute=None,
):
    """Reexecute an existing pipeline run.

    Users will typically call this API when testing pipeline reexecution, or running standalone
    scripts.

    Parameters:
        pipeline (Union[ExecutablePipeline, PipelineDefinition]): The pipeline to execute.
        parent_run_id (str): The id of the previous run to reexecute. The run must exist in the
            instance.
        run_config (Optional[dict]): The environment configuration that parametrizes this run,
            as a dict.
        step_selection (Optional[List[str]]): A list of step selection queries (including single
            step keys) to execute. For example:
            - ['some_solid.compute']: select the execution step "some_solid.compute" itself.
            - ['*some_solid.compute']: select the step "some_solid.compute" and all its ancestors
                (upstream dependencies).
            - ['*some_solid.compute+++']: select the step "some_solid.compute", all its ancestors,
                and its descendants (downstream dependencies) within 3 levels down.
            - ['*some_solid.compute', 'other_solid_a.compute', 'other_solid_b.compute+']: select
                "some_solid.compute" and all its ancestors, "other_solid_a.compute" itself, and
                "other_solid_b.compute" and its direct child execution steps.
        mode (Optional[str]): The name of the pipeline mode to use. You may not set both ``mode``
            and ``preset``.
        preset (Optional[str]): The name of the pipeline preset to use. You may not set both
            ``mode`` and ``preset``.
        tags (Optional[Dict[str, Any]]): Arbitrary key-value pairs that will be added to pipeline
            logs.
        instance (Optional[DagsterInstance]): The instance to execute against. If this is ``None``,
            an ephemeral instance will be used, and no artifacts will be persisted from the run.
        raise_on_error (Optional[bool]): Whether or not to raise exceptions when they occur.
            Defaults to ``True``, since this is the most useful behavior in test.

    Returns:
      :py:class:`PipelineExecutionResult`: The result of pipeline execution.

    For the asynchronous version, see :py:func:`reexecute_pipeline_iterator`.
    """

    step_selection = canonicalize_backcompat_args(
        step_selection, "step_selection", step_keys_to_execute, "step_keys_to_execute", "0.10.0",
    )
    check.opt_list_param(step_selection, "step_selection", of_type=str)

    check.str_param(parent_run_id, "parent_run_id")

    with _ephemeral_instance_if_missing(instance) as execute_instance:
        (pipeline, run_config, mode, tags, _, _) = _check_execute_pipeline_args(
            pipeline=pipeline, run_config=run_config, mode=mode, preset=preset, tags=tags,
        )

        parent_pipeline_run = execute_instance.get_run_by_id(parent_run_id)
        check.invariant(
            parent_pipeline_run,
            "No parent run with id {parent_run_id} found in instance.".format(
                parent_run_id=parent_run_id
            ),
        )

        # resolve step selection DSL queries using parent execution plan snapshot
        if step_selection:
            parent_execution_plan_snapshot = instance.get_execution_plan_snapshot(
                parent_pipeline_run.execution_plan_snapshot_id
            )
            step_keys_to_execute = parse_step_selection(
                parent_execution_plan_snapshot.step_deps, step_selection
            )
        else:
            step_keys_to_execute = None

        pipeline_run = execute_instance.create_run_for_pipeline(
            pipeline_def=pipeline.get_definition(),
            run_config=run_config,
            mode=mode,
            tags=tags,
            solid_selection=parent_pipeline_run.solid_selection,
            solids_to_execute=parent_pipeline_run.solids_to_execute,
            # convert to frozenset https://github.com/dagster-io/dagster/issues/2914
            step_keys_to_execute=list(step_keys_to_execute) if step_keys_to_execute else None,
            root_run_id=parent_pipeline_run.root_run_id or parent_pipeline_run.run_id,
            parent_run_id=parent_pipeline_run.run_id,
        )

        return execute_run(pipeline, pipeline_run, execute_instance, raise_on_error=raise_on_error)


def reexecute_pipeline_iterator(
    pipeline,
    parent_run_id,
    run_config=None,
    step_selection=None,
    mode=None,
    preset=None,
    tags=None,
    instance=None,
    step_keys_to_execute=None,
):
    """Reexecute a pipeline iteratively.

    Rather than package up the result of running a pipeline into a single object, like
    :py:func:`reexecute_pipeline`, this function yields the stream of events resulting from pipeline
    reexecution.

    This is intended to allow the caller to handle these events on a streaming basis in whatever
    way is appropriate.

    Parameters:
        pipeline (Union[ExecutablePipeline, PipelineDefinition]): The pipeline to execute.
        parent_run_id (str): The id of the previous run to reexecute. The run must exist in the
            instance.
        run_config (Optional[dict]): The environment configuration that parametrizes this run,
            as a dict.
        step_selection (Optional[List[str]]): A list of step selection queries (including single
            step keys) to execute. For example:
            - ['some_solid.compute']: select the execution step "some_solid.compute" itself.
            - ['*some_solid.compute']: select the step "some_solid.compute" and all its ancestors
                (upstream dependencies).
            - ['*some_solid.compute+++']: select the step "some_solid.compute", all its ancestors,
                and its descendants (downstream dependencies) within 3 levels down.
            - ['*some_solid.compute', 'other_solid_a.compute', 'other_solid_b.compute+']: select
                "some_solid.compute" and all its ancestors, "other_solid_a.compute" itself, and
                "other_solid_b.compute" and its direct child execution steps.
        mode (Optional[str]): The name of the pipeline mode to use. You may not set both ``mode``
            and ``preset``.
        preset (Optional[str]): The name of the pipeline preset to use. You may not set both
            ``mode`` and ``preset``.
        tags (Optional[Dict[str, Any]]): Arbitrary key-value pairs that will be added to pipeline
            logs.
        instance (Optional[DagsterInstance]): The instance to execute against. If this is ``None``,
            an ephemeral instance will be used, and no artifacts will be persisted from the run.

    Returns:
      Iterator[DagsterEvent]: The stream of events resulting from pipeline reexecution.
    """

    step_selection = canonicalize_backcompat_args(
        step_selection, "step_selection", step_keys_to_execute, "step_keys_to_execute", "0.10.0",
    )
    check.opt_list_param(step_selection, "step_selection", of_type=str)

    check.str_param(parent_run_id, "parent_run_id")

    with _ephemeral_instance_if_missing(instance) as execute_instance:
        (pipeline, run_config, mode, tags, _, _) = _check_execute_pipeline_args(
            pipeline=pipeline,
            run_config=run_config,
            mode=mode,
            preset=preset,
            tags=tags,
            solid_selection=None,
        )
        parent_pipeline_run = execute_instance.get_run_by_id(parent_run_id)
        check.invariant(
            parent_pipeline_run,
            "No parent run with id {parent_run_id} found in instance.".format(
                parent_run_id=parent_run_id
            ),
        )

        # resolve step selection DSL queries using parent execution plan snapshot
        if step_selection:
            parent_execution_plan_snapshot = instance.get_execution_plan_snapshot(
                parent_pipeline_run.execution_plan_snapshot_id
            )
            step_keys_to_execute = parse_step_selection(
                parent_execution_plan_snapshot.step_deps, step_selection
            )
        else:
            step_keys_to_execute = None

        pipeline_run = execute_instance.create_run_for_pipeline(
            pipeline_def=pipeline.get_definition(),
            run_config=run_config,
            mode=mode,
            tags=tags,
            solid_selection=parent_pipeline_run.solid_selection,
            solids_to_execute=parent_pipeline_run.solids_to_execute,
            # convert to frozenset https://github.com/dagster-io/dagster/issues/2914
            step_keys_to_execute=list(step_keys_to_execute) if step_keys_to_execute else None,
            root_run_id=parent_pipeline_run.root_run_id or parent_pipeline_run.run_id,
            parent_run_id=parent_pipeline_run.run_id,
        )

        return execute_run_iterator(pipeline, pipeline_run, execute_instance)


def execute_plan_iterator(
    execution_plan, pipeline_run, instance, retries=None, run_config=None,
):
    check.inst_param(execution_plan, "execution_plan", ExecutionPlan)
    check.inst_param(pipeline_run, "pipeline_run", PipelineRun)
    check.inst_param(instance, "instance", DagsterInstance)
    retries = check.opt_inst_param(retries, "retries", Retries, Retries.disabled_mode())
    run_config = check.opt_dict_param(run_config, "run_config")

    return iter(
        _ExecuteRunWithPlanIterable(
            execution_plan=execution_plan,
            iterator=inner_plan_execution_iterator,
            execution_context_manager=PlanExecutionContextManager(
                retries=retries,
                execution_plan=execution_plan,
                run_config=run_config,
                pipeline_run=pipeline_run,
                instance=instance,
                raise_on_error=False,
            ),
        )
    )


def execute_plan(
    execution_plan, instance, pipeline_run, run_config=None, retries=None,
):
    """This is the entry point of dagster-graphql executions. For the dagster CLI entry point, see
    execute_pipeline() above.
    """
    check.inst_param(execution_plan, "execution_plan", ExecutionPlan)
    check.inst_param(instance, "instance", DagsterInstance)
    check.inst_param(pipeline_run, "pipeline_run", PipelineRun)
    run_config = check.opt_dict_param(run_config, "run_config")
    check.opt_inst_param(retries, "retries", Retries)

    return list(
        execute_plan_iterator(
            execution_plan=execution_plan,
            run_config=run_config,
            pipeline_run=pipeline_run,
            instance=instance,
            retries=retries,
        )
    )


def _check_pipeline(pipeline):
    # backcompat
    if isinstance(pipeline, PipelineDefinition):
        pipeline = InMemoryExecutablePipeline(pipeline)

    check.inst_param(pipeline, "pipeline", ExecutablePipeline)
    return pipeline


def create_execution_plan(pipeline, run_config=None, mode=None, step_keys_to_execute=None):
    pipeline = _check_pipeline(pipeline)
    pipeline_def = pipeline.get_definition()
    check.inst_param(pipeline_def, "pipeline_def", PipelineDefinition)

    run_config = check.opt_dict_param(run_config, "run_config", key_type=str)
    mode = check.opt_str_param(mode, "mode", default=pipeline_def.get_default_mode_name())
    check.opt_list_param(step_keys_to_execute, "step_keys_to_execute", of_type=str)

    environment_config = EnvironmentConfig.build(pipeline_def, run_config, mode=mode)

    return ExecutionPlan.build(
        pipeline, environment_config, mode=mode, step_keys_to_execute=step_keys_to_execute
    )


class BoolRef:
    def __init__(self, value):
        self.value = value


def _core_execution_iterator(pipeline_context, execution_plan, steps_started, pipeline_success_ref):
    try:
        for event in pipeline_context.executor.execute(pipeline_context, execution_plan):
            if event.is_step_start:
                steps_started.add(event.step_key)
            if event.is_step_success:
                if event.step_key not in steps_started:
                    pipeline_success_ref.value = False
                else:
                    steps_started.remove(event.step_key)
            if event.is_step_failure:
                pipeline_success_ref.value = False
            yield event
    except (Exception, KeyboardInterrupt):
        pipeline_success_ref.value = False
        raise  # finally block will run before this is re-raised


def _pipeline_execution_iterator(pipeline_context, execution_plan):
    """A complete execution of a pipeline. Yields pipeline start, success,
    and failure events.

    Args:
        pipeline_context (SystemPipelineExecutionContext):
        execution_plan (ExecutionPlan):
    """
    check.inst_param(pipeline_context, "pipeline_context", SystemPipelineExecutionContext)
    check.inst_param(execution_plan, "execution_plan", ExecutionPlan)

    yield DagsterEvent.pipeline_start(pipeline_context)

    steps_started = set([])
    pipeline_success_ref = BoolRef(True)
    generator_closed = False
    try:
        for event in _core_execution_iterator(
            pipeline_context, execution_plan, steps_started, pipeline_success_ref
        ):
            yield event
    except GeneratorExit:
        # Shouldn't happen, but avoid runtime-exception in case this generator gets GC-ed
        # (see https://amir.rachum.com/blog/2017/03/03/generator-cleanup/).
        generator_closed = True
        pipeline_success_ref.value = False
        raise
    finally:
        if steps_started:
            pipeline_success_ref.value = False
        if pipeline_success_ref.value:
            event = DagsterEvent.pipeline_success(pipeline_context)
        else:
            event = DagsterEvent.pipeline_failure(pipeline_context)
        if not generator_closed:
            yield event


class _ExecuteRunWithPlanIterable(object):
    """Utility class to consolidate execution logic.

    This is a class and not a function because, e.g., in constructing a `scoped_pipeline_context`
    for `PipelineExecutionResult`, we need to pull out the `pipeline_context` after we're done
    yielding events. This broadly follows a pattern we make use of in other places,
    cf. `dagster.utils.EventGenerationManager`.
    """

    def __init__(self, execution_plan, iterator, execution_context_manager):
        self.execution_plan = check.inst_param(execution_plan, "execution_plan", ExecutionPlan)
        self.iterator = check.callable_param(iterator, "iterator")
        self.execution_context_manager = check.inst_param(
            execution_context_manager, "execution_context_manager", ExecutionContextManager
        )

        self.pipeline_context = None

    def __iter__(self):

        for event in self.execution_context_manager.prepare_context():
            yield event
        self.pipeline_context = self.execution_context_manager.get_context()
        generator_closed = False
        try:
            if self.pipeline_context:  # False if we had a pipeline init failure
                for event in self.iterator(
                    execution_plan=self.execution_plan, pipeline_context=self.pipeline_context,
                ):
                    yield event
        except GeneratorExit:
            # Shouldn't happen, but avoid runtime-exception in case this generator gets GC-ed
            # (see https://amir.rachum.com/blog/2017/03/03/generator-cleanup/).
            generator_closed = True
            raise
        finally:
            for event in self.execution_context_manager.shutdown_context():
                if not generator_closed:
                    yield event


def _check_execute_pipeline_args(pipeline, run_config, mode, preset, tags, solid_selection=None):
    pipeline = _check_pipeline(pipeline)
    pipeline_def = pipeline.get_definition()
    check.inst_param(pipeline_def, "pipeline_def", PipelineDefinition)

    run_config = check.opt_dict_param(run_config, "run_config")
    check.opt_str_param(mode, "mode")
    check.opt_str_param(preset, "preset")
    check.invariant(
        not (mode is not None and preset is not None),
        "You may set only one of `mode` (got {mode}) or `preset` (got {preset}).".format(
            mode=mode, preset=preset
        ),
    )

    tags = check.opt_dict_param(tags, "tags", key_type=str)
    check.opt_list_param(solid_selection, "solid_selection", of_type=str)

    if preset is not None:
        pipeline_preset = pipeline_def.get_preset(preset)

        if pipeline_preset.run_config is not None:
            check.invariant(
                (not run_config) or (pipeline_preset.run_config == run_config),
                "The environment set in preset '{preset}' does not agree with the environment "
                "passed in the `run_config` argument.".format(preset=preset),
            )

            run_config = pipeline_preset.run_config

        # load solid_selection from preset
        if pipeline_preset.solid_selection is not None:
            check.invariant(
                solid_selection is None or solid_selection == pipeline_preset.solid_selection,
                "The solid_selection set in preset '{preset}', {preset_subset}, does not agree with "
                "the `solid_selection` argument: {solid_selection}".format(
                    preset=preset,
                    preset_subset=pipeline_preset.solid_selection,
                    solid_selection=solid_selection,
                ),
            )
            solid_selection = pipeline_preset.solid_selection

        check.invariant(
            mode is None or mode == pipeline_preset.mode,
            "Mode {mode} does not agree with the mode set in preset '{preset}': "
            "('{preset_mode}')".format(preset=preset, preset_mode=pipeline_preset.mode, mode=mode),
        )

        mode = pipeline_preset.mode

        tags = merge_dicts(pipeline_preset.tags, tags)

    if mode is not None:
        if not pipeline_def.has_mode_definition(mode):
            raise DagsterInvariantViolationError(
                (
                    "You have attempted to execute pipeline {name} with mode {mode}. "
                    "Available modes: {modes}"
                ).format(
                    name=pipeline_def.name, mode=mode, modes=pipeline_def.available_modes,
                )
            )
    else:
        if pipeline_def.is_multi_mode:
            raise DagsterInvariantViolationError(
                (
                    "Pipeline {name} has multiple modes (Available modes: {modes}) and you have "
                    "attempted to execute it without specifying a mode. Set "
                    "mode property on the PipelineRun object."
                ).format(name=pipeline_def.name, modes=pipeline_def.available_modes)
            )
        mode = pipeline_def.get_default_mode_name()

    tags = merge_dicts(pipeline_def.tags, tags)

    # generate pipeline subset from the given solid_selection
    if solid_selection:
        pipeline = pipeline.subset_for_execution(solid_selection)

    return (
        pipeline,
        run_config,
        mode,
        tags,
        pipeline.solids_to_execute,
        solid_selection,
    )
