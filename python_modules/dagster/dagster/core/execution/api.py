import sys
from contextlib import contextmanager
from typing import Any, Dict, FrozenSet, Iterator, List, Mapping, Optional, Tuple, Union

import dagster._check as check
from dagster.core.definitions import IPipeline, JobDefinition, PipelineDefinition
from dagster.core.definitions.pipeline_base import InMemoryPipeline
from dagster.core.definitions.pipeline_definition import PipelineSubsetDefinition
from dagster.core.definitions.reconstruct import ReconstructablePipeline
from dagster.core.errors import DagsterExecutionInterruptedError, DagsterInvariantViolationError
from dagster.core.events import DagsterEvent, EngineEventData
from dagster.core.execution.context.system import PlanOrchestrationContext
from dagster.core.execution.plan.execute_plan import inner_plan_execution_iterator
from dagster.core.execution.plan.outputs import StepOutputHandle
from dagster.core.execution.plan.plan import ExecutionPlan
from dagster.core.execution.plan.state import KnownExecutionState
from dagster.core.execution.retries import RetryMode
from dagster.core.instance import DagsterInstance, InstanceRef
from dagster.core.selector import parse_step_selection
from dagster.core.storage.pipeline_run import PipelineRun, PipelineRunStatus
from dagster.core.system_config.objects import ResolvedRunConfig
from dagster.core.telemetry import log_repo_stats, telemetry_wrapper
from dagster.core.utils import str_format_set
from dagster.utils import merge_dicts
from dagster.utils.error import serializable_error_info_from_exc_info
from dagster.utils.interrupts import capture_interrupts

from .context_creation_pipeline import (
    ExecutionContextManager,
    PlanExecutionContextManager,
    PlanOrchestrationContextManager,
    orchestration_context_event_generator,
    scoped_pipeline_context,
)
from .results import PipelineExecutionResult

## Brief guide to the execution APIs
# | function name               | operates over      | sync  | supports    | creates new PipelineRun |
# |                             |                    |       | reexecution | in instance             |
# | --------------------------- | ------------------ | ----- | ----------- | ----------------------- |
# | execute_pipeline_iterator   | IPipeline          | async | no          | yes                     |
# | execute_pipeline            | IPipeline          | sync  | no          | yes                     |
# | execute_run_iterator        | PipelineRun        | async | (1)         | no                      |
# | execute_run                 | PipelineRun        | sync  | (1)         | no                      |
# | execute_plan_iterator       | ExecutionPlan      | async | (2)         | no                      |
# | execute_plan                | ExecutionPlan      | sync  | (2)         | no                      |
# | reexecute_pipeline          | IPipeline          | sync  | yes         | yes                     |
# | reexecute_pipeline_iterator | IPipeline          | async | yes         | yes                     |
#
# Notes on reexecution support:
# (1) The appropriate bits must be set on the PipelineRun passed to this function. Specifically,
#     parent_run_id and root_run_id must be set and consistent, and if a solids_to_execute or
#     step_keys_to_execute are set they must be consistent with the parent and root runs.
# (2) As for (1), but the ExecutionPlan passed must also agree in all relevant bits.


def execute_run_iterator(
    pipeline: IPipeline,
    pipeline_run: PipelineRun,
    instance: DagsterInstance,
    resume_from_failure: bool = False,
) -> Iterator[DagsterEvent]:
    check.inst_param(pipeline, "pipeline", IPipeline)
    check.inst_param(pipeline_run, "pipeline_run", PipelineRun)
    check.inst_param(instance, "instance", DagsterInstance)

    if pipeline_run.status == PipelineRunStatus.CANCELED:
        # This can happen if the run was force-terminated while it was starting
        def gen_execute_on_cancel():
            yield instance.report_engine_event(
                "Not starting execution since the run was canceled before execution could start",
                pipeline_run,
            )

        return gen_execute_on_cancel()

    if not resume_from_failure:
        if pipeline_run.status not in (PipelineRunStatus.NOT_STARTED, PipelineRunStatus.STARTING):
            if instance.run_monitoring_enabled:
                # This can happen if the pod was unexpectedly restarted by the cluster - ignore it since
                # the run monitoring daemon will also spin up a new pod
                def gen_ignore_duplicate_run_worker():
                    yield instance.report_engine_event(
                        "Ignoring a duplicate run that was started from somewhere other than the run monitor daemon",
                        pipeline_run,
                    )

                return gen_ignore_duplicate_run_worker()
            elif pipeline_run.is_finished:

                def gen_ignore_duplicate_run_worker():
                    yield instance.report_engine_event(
                        "Ignoring a run worker that started after the run had already finished.",
                        pipeline_run,
                    )

                return gen_ignore_duplicate_run_worker()
            else:

                def gen_fail_restarted_run_worker():
                    yield instance.report_engine_event(
                        f"{pipeline_run.pipeline_name} ({pipeline_run.run_id}) started "
                        f"a new run worker while the run was already in state {pipeline_run.status}. "
                        "This most frequently happens when the run worker unexpectedly stops and is "
                        "restarted by the cluster. Marking the run as failed.",
                        pipeline_run,
                    )
                    yield instance.report_run_failed(pipeline_run)

                return gen_fail_restarted_run_worker()

    else:
        check.invariant(
            pipeline_run.status == PipelineRunStatus.STARTED
            or pipeline_run.status == PipelineRunStatus.STARTING,
            desc="Run of {} ({}) in state {}, expected STARTED or STARTING because it's "
            "resuming from a run worker failure".format(
                pipeline_run.pipeline_name, pipeline_run.run_id, pipeline_run.status
            ),
        )

    if pipeline_run.solids_to_execute or pipeline_run.asset_selection:
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
                frozenset(pipeline_run.solids_to_execute)
                if pipeline_run.solids_to_execute
                else None,
                asset_selection=pipeline_run.asset_selection,
            )

    execution_plan = _get_execution_plan_from_run(pipeline, pipeline_run, instance)

    return iter(
        ExecuteRunWithPlanIterable(
            execution_plan=execution_plan,
            iterator=pipeline_execution_iterator,
            execution_context_manager=PlanOrchestrationContextManager(
                context_event_generator=orchestration_context_event_generator,
                pipeline=pipeline,
                execution_plan=execution_plan,
                pipeline_run=pipeline_run,
                instance=instance,
                run_config=pipeline_run.run_config,
                raise_on_error=False,
                executor_defs=None,
                output_capture=None,
                resume_from_failure=resume_from_failure,
            ),
        )
    )


def execute_run(
    pipeline: IPipeline,
    pipeline_run: PipelineRun,
    instance: DagsterInstance,
    raise_on_error: bool = False,
) -> PipelineExecutionResult:
    """Executes an existing pipeline run synchronously.

    Synchronous version of execute_run_iterator.

    Args:
        pipeline (IPipeline): The pipeline to execute.
        pipeline_run (PipelineRun): The run to execute
        instance (DagsterInstance): The instance in which the run has been created.
        raise_on_error (Optional[bool]): Whether or not to raise exceptions when they occur.
            Defaults to ``False``.

    Returns:
        PipelineExecutionResult: The result of the execution.
    """
    if isinstance(pipeline, PipelineDefinition):
        if isinstance(pipeline, JobDefinition):
            error = "execute_run requires a reconstructable job but received job definition directly instead."
        else:
            error = (
                "execute_run requires a reconstructable pipeline but received pipeline definition "
                "directly instead."
            )
        raise DagsterInvariantViolationError(
            f"{error} To support hand-off to other processes please wrap your definition in "
            "a call to reconstructable(). Learn more about reconstructable here: https://docs.dagster.io/_apidocs/execution#dagster.reconstructable"
        )

    check.inst_param(pipeline, "pipeline", IPipeline)
    check.inst_param(pipeline_run, "pipeline_run", PipelineRun)
    check.inst_param(instance, "instance", DagsterInstance)

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
        desc="Run {} ({}) in state {}, expected NOT_STARTED or STARTING".format(
            pipeline_run.pipeline_name, pipeline_run.run_id, pipeline_run.status
        ),
    )
    pipeline_def = pipeline.get_definition()
    if pipeline_run.solids_to_execute or pipeline_run.asset_selection:
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
                frozenset(pipeline_run.solids_to_execute)
                if pipeline_run.solids_to_execute
                else None,
                pipeline_run.asset_selection,
            )

    execution_plan = _get_execution_plan_from_run(pipeline, pipeline_run, instance)
    output_capture: Optional[Dict[StepOutputHandle, Any]] = {}

    _execute_run_iterable = ExecuteRunWithPlanIterable(
        execution_plan=execution_plan,
        iterator=pipeline_execution_iterator,
        execution_context_manager=PlanOrchestrationContextManager(
            context_event_generator=orchestration_context_event_generator,
            pipeline=pipeline,
            execution_plan=execution_plan,
            pipeline_run=pipeline_run,
            instance=instance,
            run_config=pipeline_run.run_config,
            raise_on_error=raise_on_error,
            executor_defs=None,
            output_capture=output_capture,
        ),
    )
    event_list = list(_execute_run_iterable)

    return PipelineExecutionResult(
        pipeline.get_definition(),
        pipeline_run.run_id,
        event_list,
        lambda: scoped_pipeline_context(
            execution_plan,
            pipeline,
            pipeline_run.run_config,
            pipeline_run,
            instance,
        ),
        output_capture=output_capture,
    )


def execute_pipeline_iterator(
    pipeline: Union[PipelineDefinition, IPipeline],
    run_config: Optional[dict] = None,
    mode: Optional[str] = None,
    preset: Optional[str] = None,
    tags: Optional[Dict[str, Any]] = None,
    solid_selection: Optional[List[str]] = None,
    instance: Optional[DagsterInstance] = None,
) -> Iterator[DagsterEvent]:
    """Execute a pipeline iteratively.

    Rather than package up the result of running a pipeline into a single object, like
    :py:func:`execute_pipeline`, this function yields the stream of events resulting from pipeline
    execution.

    This is intended to allow the caller to handle these events on a streaming basis in whatever
    way is appropriate.

    Parameters:
        pipeline (Union[IPipeline, PipelineDefinition]): The pipeline to execute.
        run_config (Optional[dict]): The configuration that parametrizes this run,
            as a dict.
        mode (Optional[str]): The name of the pipeline mode to use. You may not set both ``mode``
            and ``preset``.
        preset (Optional[str]): The name of the pipeline preset to use. You may not set both
            ``mode`` and ``preset``.
        tags (Optional[Dict[str, Any]]): Arbitrary key-value pairs that will be added to pipeline
            logs.
        solid_selection (Optional[List[str]]): A list of solid selection queries (including single
            solid names) to execute. For example:

            - ``['some_solid']``: selects ``some_solid`` itself.
            - ``['*some_solid']``: select ``some_solid`` and all its ancestors (upstream dependencies).
            - ``['*some_solid+++']``: select ``some_solid``, all its ancestors, and its descendants
              (downstream dependencies) within 3 levels down.
            - ``['*some_solid', 'other_solid_a', 'other_solid_b+']``: select ``some_solid`` and all its
              ancestors, ``other_solid_a`` itself, and ``other_solid_b`` and its direct child solids.
        instance (Optional[DagsterInstance]): The instance to execute against. If this is ``None``,
            an ephemeral instance will be used, and no artifacts will be persisted from the run.

    Returns:
      Iterator[DagsterEvent]: The stream of events resulting from pipeline execution.
    """

    with ephemeral_instance_if_missing(instance) as execute_instance:
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
def ephemeral_instance_if_missing(
    instance: Optional[DagsterInstance],
) -> Iterator[DagsterInstance]:
    if instance:
        yield instance
    else:
        with DagsterInstance.ephemeral() as ephemeral_instance:
            yield ephemeral_instance


def execute_pipeline(
    pipeline: Union[PipelineDefinition, IPipeline],
    run_config: Optional[dict] = None,
    mode: Optional[str] = None,
    preset: Optional[str] = None,
    tags: Optional[Dict[str, Any]] = None,
    solid_selection: Optional[List[str]] = None,
    instance: Optional[DagsterInstance] = None,
    raise_on_error: bool = True,
) -> PipelineExecutionResult:
    """Execute a pipeline synchronously.

    Users will typically call this API when testing pipeline execution, or running standalone
    scripts.

    Parameters:
        pipeline (Union[IPipeline, PipelineDefinition]): The pipeline to execute.
        run_config (Optional[dict]): The configuration that parametrizes this run,
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

            - ``['some_solid']``: selects ``some_solid`` itself.
            - ``['*some_solid']``: select ``some_solid`` and all its ancestors (upstream dependencies).
            - ``['*some_solid+++']``: select ``some_solid``, all its ancestors, and its descendants
              (downstream dependencies) within 3 levels down.
            - ``['*some_solid', 'other_solid_a', 'other_solid_b+']``: select ``some_solid`` and all its
              ancestors, ``other_solid_a`` itself, and ``other_solid_b`` and its direct child solids.

    Returns:
      :py:class:`PipelineExecutionResult`: The result of pipeline execution.

    For the asynchronous version, see :py:func:`execute_pipeline_iterator`.
    """

    with ephemeral_instance_if_missing(instance) as execute_instance:
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
    pipeline: Union[IPipeline, PipelineDefinition],
    instance: DagsterInstance,
    run_config: Optional[dict] = None,
    mode: Optional[str] = None,
    preset: Optional[str] = None,
    tags: Optional[Dict[str, Any]] = None,
    solid_selection: Optional[List[str]] = None,
    raise_on_error: bool = True,
) -> PipelineExecutionResult:
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
        pipeline_code_origin=(
            pipeline.get_python_origin() if isinstance(pipeline, ReconstructablePipeline) else None
        ),
    )

    return execute_run(
        pipeline,
        pipeline_run,
        instance,
        raise_on_error=raise_on_error,
    )


def reexecute_pipeline(
    pipeline: Union[IPipeline, PipelineDefinition],
    parent_run_id: str,
    run_config: Optional[dict] = None,
    step_selection: Optional[List[str]] = None,
    mode: Optional[str] = None,
    preset: Optional[str] = None,
    tags: Optional[Dict[str, Any]] = None,
    instance: Optional[DagsterInstance] = None,
    raise_on_error: bool = True,
) -> PipelineExecutionResult:
    """Reexecute an existing pipeline run.

    Users will typically call this API when testing pipeline reexecution, or running standalone
    scripts.

    Parameters:
        pipeline (Union[IPipeline, PipelineDefinition]): The pipeline to execute.
        parent_run_id (str): The id of the previous run to reexecute. The run must exist in the
            instance.
        run_config (Optional[dict]): The configuration that parametrizes this run,
            as a dict.
        solid_selection (Optional[List[str]]): A list of solid selection queries (including single
            solid names) to execute. For example:

            - ``['some_solid']``: selects ``some_solid`` itself.
            - ``['*some_solid']``: select ``some_solid`` and all its ancestors (upstream dependencies).
            - ``['*some_solid+++']``: select ``some_solid``, all its ancestors, and its descendants
              (downstream dependencies) within 3 levels down.
            - ``['*some_solid', 'other_solid_a', 'other_solid_b+']``: select ``some_solid`` and all its
              ancestors, ``other_solid_a`` itself, and ``other_solid_b`` and its direct child solids.

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

    check.opt_list_param(step_selection, "step_selection", of_type=str)

    check.str_param(parent_run_id, "parent_run_id")

    with ephemeral_instance_if_missing(instance) as execute_instance:
        (pipeline, run_config, mode, tags, _, _) = _check_execute_pipeline_args(
            pipeline=pipeline,
            run_config=run_config,
            mode=mode,
            preset=preset,
            tags=tags,
        )

        parent_pipeline_run = execute_instance.get_run_by_id(parent_run_id)
        if parent_pipeline_run is None:
            check.failed(
                "No parent run with id {parent_run_id} found in instance.".format(
                    parent_run_id=parent_run_id
                ),
            )

        execution_plan: Optional[ExecutionPlan] = None
        # resolve step selection DSL queries using parent execution information
        if step_selection:
            execution_plan = _resolve_reexecute_step_selection(
                execute_instance,
                pipeline,
                mode,
                run_config,
                parent_pipeline_run,
                step_selection,
            )

        if parent_pipeline_run.asset_selection:
            pipeline = pipeline.subset_for_execution(
                solid_selection=None, asset_selection=parent_pipeline_run.asset_selection
            )

        pipeline_run = execute_instance.create_run_for_pipeline(
            pipeline_def=pipeline.get_definition(),
            execution_plan=execution_plan,
            run_config=run_config,
            mode=mode,
            tags=tags,
            solid_selection=parent_pipeline_run.solid_selection,
            asset_selection=parent_pipeline_run.asset_selection,
            solids_to_execute=parent_pipeline_run.solids_to_execute,
            root_run_id=parent_pipeline_run.root_run_id or parent_pipeline_run.run_id,
            parent_run_id=parent_pipeline_run.run_id,
        )

        return execute_run(
            pipeline,
            pipeline_run,
            execute_instance,
            raise_on_error=raise_on_error,
        )


def reexecute_pipeline_iterator(
    pipeline: Union[IPipeline, PipelineDefinition],
    parent_run_id: str,
    run_config: Optional[dict] = None,
    step_selection: Optional[List[str]] = None,
    mode: Optional[str] = None,
    preset: Optional[str] = None,
    tags: Optional[Dict[str, Any]] = None,
    instance: Optional[DagsterInstance] = None,
) -> Iterator[DagsterEvent]:
    """Reexecute a pipeline iteratively.

    Rather than package up the result of running a pipeline into a single object, like
    :py:func:`reexecute_pipeline`, this function yields the stream of events resulting from pipeline
    reexecution.

    This is intended to allow the caller to handle these events on a streaming basis in whatever
    way is appropriate.

    Parameters:
        pipeline (Union[IPipeline, PipelineDefinition]): The pipeline to execute.
        parent_run_id (str): The id of the previous run to reexecute. The run must exist in the
            instance.
        run_config (Optional[dict]): The configuration that parametrizes this run,
            as a dict.
        solid_selection (Optional[List[str]]): A list of solid selection queries (including single
            solid names) to execute. For example:

            - ``['some_solid']``: selects ``some_solid`` itself.
            - ``['*some_solid']``: select ``some_solid`` and all its ancestors (upstream dependencies).
            - ``['*some_solid+++']``: select ``some_solid``, all its ancestors, and its descendants
              (downstream dependencies) within 3 levels down.
            - ``['*some_solid', 'other_solid_a', 'other_solid_b+']``: select ``some_solid`` and all its
              ancestors, ``other_solid_a`` itself, and ``other_solid_b`` and its direct child solids.

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

    check.opt_list_param(step_selection, "step_selection", of_type=str)

    check.str_param(parent_run_id, "parent_run_id")

    with ephemeral_instance_if_missing(instance) as execute_instance:
        (pipeline, run_config, mode, tags, _, _) = _check_execute_pipeline_args(
            pipeline=pipeline,
            run_config=run_config,
            mode=mode,
            preset=preset,
            tags=tags,
            solid_selection=None,
        )
        parent_pipeline_run = execute_instance.get_run_by_id(parent_run_id)
        if parent_pipeline_run is None:
            check.failed(
                "No parent run with id {parent_run_id} found in instance.".format(
                    parent_run_id=parent_run_id
                ),
            )

        execution_plan: Optional[ExecutionPlan] = None
        # resolve step selection DSL queries using parent execution information
        if step_selection:
            execution_plan = _resolve_reexecute_step_selection(
                execute_instance,
                pipeline,
                mode,
                run_config,
                parent_pipeline_run,
                step_selection,
            )

        pipeline_run = execute_instance.create_run_for_pipeline(
            pipeline_def=pipeline.get_definition(),
            run_config=run_config,
            execution_plan=execution_plan,
            mode=mode,
            tags=tags,
            solid_selection=parent_pipeline_run.solid_selection,
            solids_to_execute=parent_pipeline_run.solids_to_execute,
            root_run_id=parent_pipeline_run.root_run_id or parent_pipeline_run.run_id,
            parent_run_id=parent_pipeline_run.run_id,
        )

        return execute_run_iterator(pipeline, pipeline_run, execute_instance)


def execute_plan_iterator(
    execution_plan: ExecutionPlan,
    pipeline: IPipeline,
    pipeline_run: PipelineRun,
    instance: DagsterInstance,
    retry_mode: Optional[RetryMode] = None,
    run_config: Optional[Mapping[str, object]] = None,
) -> Iterator[DagsterEvent]:
    check.inst_param(execution_plan, "execution_plan", ExecutionPlan)
    check.inst_param(pipeline, "pipeline", IPipeline)
    check.inst_param(pipeline_run, "pipeline_run", PipelineRun)
    check.inst_param(instance, "instance", DagsterInstance)
    retry_mode = check.opt_inst_param(retry_mode, "retry_mode", RetryMode, RetryMode.DISABLED)
    run_config = check.opt_mapping_param(run_config, "run_config")

    return iter(
        ExecuteRunWithPlanIterable(
            execution_plan=execution_plan,
            iterator=inner_plan_execution_iterator,
            execution_context_manager=PlanExecutionContextManager(
                pipeline=pipeline,
                retry_mode=retry_mode,
                execution_plan=execution_plan,
                run_config=run_config,
                pipeline_run=pipeline_run,
                instance=instance,
            ),
        )
    )


def execute_plan(
    execution_plan: ExecutionPlan,
    pipeline: IPipeline,
    instance: DagsterInstance,
    pipeline_run: PipelineRun,
    run_config: Optional[Dict] = None,
    retry_mode: Optional[RetryMode] = None,
) -> List[DagsterEvent]:
    """This is the entry point of dagster-graphql executions. For the dagster CLI entry point, see
    execute_pipeline() above.
    """
    check.inst_param(execution_plan, "execution_plan", ExecutionPlan)
    check.inst_param(pipeline, "pipeline", IPipeline)
    check.inst_param(instance, "instance", DagsterInstance)
    check.inst_param(pipeline_run, "pipeline_run", PipelineRun)
    run_config = check.opt_dict_param(run_config, "run_config")
    check.opt_inst_param(retry_mode, "retry_mode", RetryMode)

    return list(
        execute_plan_iterator(
            execution_plan=execution_plan,
            pipeline=pipeline,
            run_config=run_config,
            pipeline_run=pipeline_run,
            instance=instance,
            retry_mode=retry_mode,
        )
    )


def _check_pipeline(pipeline: Union[PipelineDefinition, IPipeline]) -> IPipeline:
    # backcompat
    if isinstance(pipeline, PipelineDefinition):
        pipeline = InMemoryPipeline(pipeline)

    check.inst_param(pipeline, "pipeline", IPipeline)
    return pipeline


def _get_execution_plan_from_run(
    pipeline: IPipeline, pipeline_run: PipelineRun, instance: DagsterInstance
) -> ExecutionPlan:
    if (
        # need to rebuild execution plan so it matches the subsetted graph
        pipeline.solids_to_execute is None
        and pipeline_run.execution_plan_snapshot_id
    ):
        execution_plan_snapshot = instance.get_execution_plan_snapshot(
            pipeline_run.execution_plan_snapshot_id
        )
        if execution_plan_snapshot.can_reconstruct_plan:
            return ExecutionPlan.rebuild_from_snapshot(
                pipeline_run.pipeline_name,
                execution_plan_snapshot,
            )
    return create_execution_plan(
        pipeline,
        run_config=pipeline_run.run_config,
        mode=pipeline_run.mode,
        step_keys_to_execute=pipeline_run.step_keys_to_execute,
        instance_ref=instance.get_ref() if instance.is_persistent else None,
    )


def create_execution_plan(
    pipeline: Union[IPipeline, PipelineDefinition],
    run_config: Optional[Mapping[str, object]] = None,
    mode: Optional[str] = None,
    step_keys_to_execute: Optional[List[str]] = None,
    known_state: Optional[KnownExecutionState] = None,
    instance_ref: Optional[InstanceRef] = None,
    tags: Optional[Dict[str, str]] = None,
) -> ExecutionPlan:
    pipeline = _check_pipeline(pipeline)
    pipeline_def = pipeline.get_definition()
    check.inst_param(pipeline_def, "pipeline_def", PipelineDefinition)
    run_config = check.opt_mapping_param(run_config, "run_config", key_type=str)
    mode = check.opt_str_param(mode, "mode", default=pipeline_def.get_default_mode_name())
    check.opt_nullable_list_param(step_keys_to_execute, "step_keys_to_execute", of_type=str)
    check.opt_inst_param(instance_ref, "instance_ref", InstanceRef)
    tags = check.opt_dict_param(tags, "tags", key_type=str, value_type=str)

    resolved_run_config = ResolvedRunConfig.build(pipeline_def, run_config, mode=mode)

    return ExecutionPlan.build(
        pipeline,
        resolved_run_config,
        step_keys_to_execute=step_keys_to_execute,
        known_state=known_state,
        instance_ref=instance_ref,
        tags=tags,
    )


def pipeline_execution_iterator(
    pipeline_context: PlanOrchestrationContext, execution_plan: ExecutionPlan
) -> Iterator[DagsterEvent]:
    """A complete execution of a pipeline. Yields pipeline start, success,
    and failure events.

    Args:
        pipeline_context (PlanOrchestrationContext):
        execution_plan (ExecutionPlan):
    """

    # TODO: restart event?
    if not pipeline_context.resume_from_failure:
        yield DagsterEvent.pipeline_start(pipeline_context)

    pipeline_exception_info = None
    pipeline_canceled_info = None
    failed_steps = []
    generator_closed = False
    try:
        for event in pipeline_context.executor.execute(pipeline_context, execution_plan):
            if event.is_step_failure:
                failed_steps.append(event.step_key)

            yield event
    except GeneratorExit:
        # Shouldn't happen, but avoid runtime-exception in case this generator gets GC-ed
        # (see https://amir.rachum.com/blog/2017/03/03/generator-cleanup/).
        generator_closed = True
        pipeline_exception_info = serializable_error_info_from_exc_info(sys.exc_info())
        if pipeline_context.raise_on_error:
            raise
    except (KeyboardInterrupt, DagsterExecutionInterruptedError):
        pipeline_canceled_info = serializable_error_info_from_exc_info(sys.exc_info())
        if pipeline_context.raise_on_error:
            raise
    except BaseException:
        pipeline_exception_info = serializable_error_info_from_exc_info(sys.exc_info())
        if pipeline_context.raise_on_error:
            raise  # finally block will run before this is re-raised
    finally:
        if pipeline_canceled_info:
            reloaded_run = pipeline_context.instance.get_run_by_id(pipeline_context.run_id)
            if reloaded_run and reloaded_run.status == PipelineRunStatus.CANCELING:
                event = DagsterEvent.pipeline_canceled(pipeline_context, pipeline_canceled_info)
            elif reloaded_run and reloaded_run.status == PipelineRunStatus.CANCELED:
                # This happens if the run was force-terminated but was still able to send
                # a cancellation request
                event = DagsterEvent.engine_event(
                    pipeline_context,
                    "Computational resources were cleaned up after the run was forcibly marked as canceled.",
                    EngineEventData(),
                )
            elif pipeline_context.instance.run_will_resume(pipeline_context.run_id):
                event = DagsterEvent.engine_event(
                    pipeline_context,
                    "Execution was interrupted unexpectedly. "
                    "No user initiated termination request was found, not treating as failure because run will be resumed.",
                    EngineEventData(),
                )
            else:
                event = DagsterEvent.pipeline_failure(
                    pipeline_context,
                    "Execution was interrupted unexpectedly. "
                    "No user initiated termination request was found, treating as failure.",
                    pipeline_canceled_info,
                )
        elif pipeline_exception_info:
            event = DagsterEvent.pipeline_failure(
                pipeline_context,
                "An exception was thrown during execution.",
                pipeline_exception_info,
            )
        elif failed_steps:
            event = DagsterEvent.pipeline_failure(
                pipeline_context,
                "Steps failed: {}.".format(failed_steps),
            )
        else:
            event = DagsterEvent.pipeline_success(pipeline_context)
        if not generator_closed:
            yield event


class ExecuteRunWithPlanIterable:
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
        # Since interrupts can't be raised at arbitrary points safely, delay them until designated
        # checkpoints during the execution.
        # To be maximally certain that interrupts are always caught during an execution process,
        # you can safely add an additional `with capture_interrupts()` at the very beginning of the
        # process that performs the execution.
        with capture_interrupts():
            yield from self.execution_context_manager.prepare_context()
            self.pipeline_context = self.execution_context_manager.get_context()
            generator_closed = False
            try:
                if self.pipeline_context:  # False if we had a pipeline init failure
                    yield from self.iterator(
                        execution_plan=self.execution_plan,
                        pipeline_context=self.pipeline_context,
                    )
            except GeneratorExit:
                # Shouldn't happen, but avoid runtime-exception in case this generator gets GC-ed
                # (see https://amir.rachum.com/blog/2017/03/03/generator-cleanup/).
                generator_closed = True
                raise
            finally:
                for event in self.execution_context_manager.shutdown_context():
                    if not generator_closed:
                        yield event


def _check_execute_pipeline_args(
    pipeline: Union[PipelineDefinition, IPipeline],
    run_config: Optional[dict],
    mode: Optional[str],
    preset: Optional[str],
    tags: Optional[Dict[str, Any]],
    solid_selection: Optional[List[str]] = None,
) -> Tuple[
    IPipeline,
    Optional[dict],
    Optional[str],
    Dict[str, Any],
    Optional[FrozenSet[str]],
    Optional[List[str]],
]:
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
                    name=pipeline_def.name,
                    mode=mode,
                    modes=pipeline_def.available_modes,
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


def _resolve_reexecute_step_selection(
    instance: DagsterInstance,
    pipeline: IPipeline,
    mode: Optional[str],
    run_config: Optional[dict],
    parent_pipeline_run: PipelineRun,
    step_selection: List[str],
) -> ExecutionPlan:
    if parent_pipeline_run.solid_selection:
        pipeline = pipeline.subset_for_execution(parent_pipeline_run.solid_selection, None)

    parent_logs = instance.all_logs(parent_pipeline_run.run_id)
    parent_plan = create_execution_plan(
        pipeline,
        parent_pipeline_run.run_config,
        mode,
        known_state=KnownExecutionState.derive_from_logs(parent_logs),
    )
    step_keys_to_execute = parse_step_selection(parent_plan.get_all_step_deps(), step_selection)
    execution_plan = create_execution_plan(
        pipeline,
        run_config,
        mode,
        step_keys_to_execute=list(step_keys_to_execute),
        known_state=KnownExecutionState.for_reexecution(parent_logs, step_keys_to_execute),
        tags=parent_pipeline_run.tags,
    )
    return execution_plan
