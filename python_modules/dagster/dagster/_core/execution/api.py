import sys
from collections.abc import Iterator, Mapping, Sequence
from contextlib import contextmanager
from typing import AbstractSet, Any, Callable, NamedTuple, Optional, Union, cast  # noqa: UP035

import dagster._check as check
from dagster._core.definitions import IJob, JobDefinition
from dagster._core.definitions.events import AssetKey
from dagster._core.definitions.job_base import InMemoryJob
from dagster._core.definitions.reconstruct import ReconstructableJob
from dagster._core.definitions.repository_definition import RepositoryLoadData
from dagster._core.errors import DagsterExecutionInterruptedError, DagsterInvariantViolationError
from dagster._core.events import DagsterEvent, EngineEventData, JobFailureData, RunFailureReason
from dagster._core.execution.context.system import PlanOrchestrationContext
from dagster._core.execution.context_creation_job import (
    ExecutionContextManager,
    PlanExecutionContextManager,
    PlanOrchestrationContextManager,
    orchestration_context_event_generator,
    scoped_job_context,
)
from dagster._core.execution.job_execution_result import JobExecutionResult
from dagster._core.execution.plan.execute_plan import inner_plan_execution_iterator
from dagster._core.execution.plan.plan import ExecutionPlan
from dagster._core.execution.plan.state import KnownExecutionState
from dagster._core.execution.retries import RetryMode
from dagster._core.instance import DagsterInstance, InstanceRef
from dagster._core.selector import parse_step_selection
from dagster._core.storage.dagster_run import DagsterRun, DagsterRunStatus
from dagster._core.system_config.objects import ResolvedRunConfig
from dagster._core.telemetry import log_dagster_event, log_repo_stats, telemetry_wrapper
from dagster._utils.error import serializable_error_info_from_exc_info
from dagster._utils.interrupts import capture_interrupts
from dagster._utils.merger import merge_dicts

## Brief guide to the execution APIs
# | function name               | operates over      | sync  | supports    | creates new DagsterRun  |
# |                             |                    |       | reexecution | in instance             |
# | --------------------------- | ------------------ | ----- | ----------- | ----------------------- |
# | execute_job                 | ReconstructableJob | sync  | yes         | yes                     |
# | execute_run_iterator        | DagsterRun         | async | (1)         | no                      |
# | execute_run                 | DagsterRun         | sync  | (1)         | no                      |
# | execute_plan_iterator       | ExecutionPlan      | async | (2)         | no                      |
# | execute_plan                | ExecutionPlan      | sync  | (2)         | no                      |
#
# Notes on reexecution support:
# (1) The appropriate bits must be set on the DagsterRun passed to this function. Specifically,
#     parent_run_id and root_run_id must be set and consistent, and if a resolved_op_selection or
#     step_keys_to_execute are set they must be consistent with the parent and root runs.
# (2) As for (1), but the ExecutionPlan passed must also agree in all relevant bits.


def execute_run_iterator(
    job: IJob,
    dagster_run: DagsterRun,
    instance: DagsterInstance,
    resume_from_failure: bool = False,
) -> Iterator[DagsterEvent]:
    check.inst_param(job, "job", IJob)
    check.inst_param(dagster_run, "dagster_run", DagsterRun)
    check.inst_param(instance, "instance", DagsterInstance)

    if dagster_run.status == DagsterRunStatus.CANCELED:
        # This can happen if the run was force-terminated while it was starting
        def gen_execute_on_cancel():
            yield instance.report_engine_event(
                "Not starting execution since the run was canceled before execution could start",
                dagster_run,
            )

        return gen_execute_on_cancel()

    if not resume_from_failure:
        if dagster_run.status not in (DagsterRunStatus.NOT_STARTED, DagsterRunStatus.STARTING):
            if dagster_run.is_finished:

                def gen_ignore_duplicate_run_worker():
                    yield instance.report_engine_event(
                        "Ignoring a run worker that started after the run had already finished.",
                        dagster_run,
                    )

                return gen_ignore_duplicate_run_worker()
            elif instance.run_monitoring_enabled:
                # This can happen if the pod was unexpectedly restarted by the cluster - ignore it since
                # the run monitoring daemon will also spin up a new pod
                def gen_ignore_duplicate_run_worker():
                    yield instance.report_engine_event(
                        "Ignoring a duplicate run that was started from somewhere other than"
                        " the run monitor daemon",
                        dagster_run,
                    )

                return gen_ignore_duplicate_run_worker()
            else:

                def gen_fail_restarted_run_worker():
                    yield instance.report_engine_event(
                        f"{dagster_run.job_name} ({dagster_run.run_id}) started a new"
                        f" run worker while the run was already in state {dagster_run.status}."
                        " This most frequently happens when the run worker unexpectedly stops"
                        " and is restarted by the cluster. Marking the run as failed.",
                        dagster_run,
                    )
                    yield instance.report_run_failed(
                        dagster_run,
                        job_failure_data=JobFailureData(
                            error=None, failure_reason=RunFailureReason.RUN_WORKER_RESTART
                        ),
                    )

                return gen_fail_restarted_run_worker()

    else:
        check.invariant(
            dagster_run.status == DagsterRunStatus.STARTED
            or dagster_run.status == DagsterRunStatus.STARTING,
            desc=(
                f"Run of {dagster_run.job_name} ({dagster_run.run_id}) in state {dagster_run.status}, expected STARTED or STARTING because it's "
                "resuming from a run worker failure"
            ),
        )

    if (
        dagster_run.resolved_op_selection
        or dagster_run.asset_selection
        or dagster_run.asset_check_selection
    ):
        # when `execute_run_iterator` is directly called, the sub pipeline hasn't been created
        # note that when we receive the solids to execute via DagsterRun, it won't support
        # solid selection query syntax
        job = job.get_subset(
            op_selection=(
                list(dagster_run.resolved_op_selection)
                if dagster_run.resolved_op_selection
                else None
            ),
            asset_selection=dagster_run.asset_selection,
            asset_check_selection=dagster_run.asset_check_selection,
        )

    execution_plan = _get_execution_plan_from_run(job, dagster_run, instance)
    if isinstance(job, ReconstructableJob):
        job = job.with_repository_load_data(execution_plan.repository_load_data)

    return iter(
        ExecuteRunWithPlanIterable(
            execution_plan=execution_plan,
            iterator=job_execution_iterator,
            execution_context_manager=PlanOrchestrationContextManager(
                context_event_generator=orchestration_context_event_generator,
                job=job,
                execution_plan=execution_plan,
                dagster_run=dagster_run,
                instance=instance,
                run_config=dagster_run.run_config,
                raise_on_error=False,
                executor_defs=None,
                output_capture=None,
                resume_from_failure=resume_from_failure,
            ),
        )
    )


def execute_run(
    job: IJob,
    dagster_run: DagsterRun,
    instance: DagsterInstance,
    raise_on_error: bool = False,
) -> JobExecutionResult:
    """Executes an existing job run synchronously.

    Synchronous version of execute_run_iterator.

    Args:
        job (IJob): The pipeline to execute.
        dagster_run (DagsterRun): The run to execute
        instance (DagsterInstance): The instance in which the run has been created.
        raise_on_error (Optional[bool]): Whether or not to raise exceptions when they occur.
            Defaults to ``False``.

    Returns:
        JobExecutionResult: The result of the execution.
    """
    if isinstance(job, JobDefinition):
        raise DagsterInvariantViolationError(
            "execute_run requires a reconstructable job but received job definition directly"
            " instead. To support hand-off to other processes please wrap your definition in a call"
            " to reconstructable(). Learn more about reconstructable here:"
            " https://docs.dagster.io/api/python-api/execution#dagster.reconstructable"
        )

    check.inst_param(job, "job", IJob)
    check.inst_param(dagster_run, "dagster_run", DagsterRun)
    check.inst_param(instance, "instance", DagsterInstance)

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
        desc=f"Run {dagster_run.job_name} ({dagster_run.run_id}) in state {dagster_run.status}, expected NOT_STARTED or STARTING",
    )
    if (
        dagster_run.resolved_op_selection
        or dagster_run.asset_selection
        or dagster_run.asset_check_selection
    ):
        # when `execute_run` is directly called, the sub job hasn't been created
        # note that when we receive the solids to execute via DagsterRun, it won't support
        # solid selection query syntax
        job = job.get_subset(
            op_selection=(
                list(dagster_run.resolved_op_selection)
                if dagster_run.resolved_op_selection
                else None
            ),
            asset_selection=dagster_run.asset_selection,
            asset_check_selection=dagster_run.asset_check_selection,
        )

    execution_plan = _get_execution_plan_from_run(job, dagster_run, instance)
    if isinstance(job, ReconstructableJob):
        job = job.with_repository_load_data(execution_plan.repository_load_data)

    _execute_run_iterable = ExecuteRunWithPlanIterable(
        execution_plan=execution_plan,
        iterator=job_execution_iterator,
        execution_context_manager=PlanOrchestrationContextManager(
            context_event_generator=orchestration_context_event_generator,
            job=job,
            execution_plan=execution_plan,
            dagster_run=dagster_run,
            instance=instance,
            run_config=dagster_run.run_config,
            raise_on_error=raise_on_error,
            executor_defs=None,
            output_capture=None,
        ),
    )
    event_list = list(_execute_run_iterable)

    # We need to reload the run object after execution for it to be accurate
    reloaded_dagster_run = check.not_none(instance.get_run_by_id(dagster_run.run_id))

    return JobExecutionResult(
        job.get_definition(),
        scoped_job_context(
            execution_plan,
            job,
            reloaded_dagster_run.run_config,
            reloaded_dagster_run,
            instance,
        ),
        event_list,
        reloaded_dagster_run,
    )


@contextmanager
def ephemeral_instance_if_missing(
    instance: Optional[DagsterInstance],
) -> Iterator[DagsterInstance]:
    if instance:
        yield instance
    else:
        with DagsterInstance.ephemeral() as ephemeral_instance:
            yield ephemeral_instance


class ReexecutionOptions(NamedTuple):
    """Reexecution options for python-based execution in Dagster.

    Args:
        parent_run_id (str): The run_id of the run to reexecute.
        step_selection (Sequence[str]):
            The list of step selections to reexecute. Must be a subset or match of the
            set of steps executed in the original run. For example:

            - ``['some_op']``: selects ``some_op`` itself.
            - ``['*some_op']``: select ``some_op`` and all its ancestors (upstream dependencies).
            - ``['*some_op+++']``: select ``some_op``, all its ancestors, and its descendants
              (downstream dependencies) within 3 levels down.
            - ``['*some_op', 'other_op_a', 'other_op_b+']``: select ``some_op`` and all its
              ancestors, ``other_op_a`` itself, and ``other_op_b`` and its direct child ops.
    """

    parent_run_id: str
    step_selection: Sequence[str] = []

    @staticmethod
    def from_failure(run_id: str, instance: DagsterInstance) -> "ReexecutionOptions":
        """Creates reexecution options from a failed run.

        Args:
            run_id (str): The run_id of the failed run. Run must fail in order to be reexecuted.
            instance (DagsterInstance): The DagsterInstance that the original run occurred in.

        Returns:
            ReexecutionOptions: Reexecution options to pass to a python execution.
        """
        return ReexecuteFromFailureOption(parent_run_id=run_id)


class ReexecuteFromFailureOption(ReexecutionOptions):
    """Marker subclass used to calculate reexecution information later."""


def execute_job(
    job: ReconstructableJob,
    instance: "DagsterInstance",
    run_config: Any = None,
    tags: Optional[Mapping[str, Any]] = None,
    raise_on_error: bool = False,
    op_selection: Optional[Sequence[str]] = None,
    reexecution_options: Optional[ReexecutionOptions] = None,
    asset_selection: Optional[Sequence[AssetKey]] = None,
) -> JobExecutionResult:
    """Execute a job synchronously.

    This API represents dagster's python entrypoint for out-of-process
    execution. For most testing purposes, :py:meth:`~dagster.JobDefinition.
    execute_in_process` will be more suitable, but when wanting to run
    execution using an out-of-process executor (such as :py:class:`dagster.
    multiprocess_executor`), then `execute_job` is suitable.

    `execute_job` expects a persistent :py:class:`DagsterInstance` for
    execution, meaning the `$DAGSTER_HOME` environment variable must be set.
    It also expects a reconstructable pointer to a :py:class:`JobDefinition` so
    that it can be reconstructed in separate processes. This can be done by
    wrapping the ``JobDefinition`` in a call to :py:func:`dagster.
    reconstructable`.

    .. code-block:: python

        from dagster import DagsterInstance, execute_job, job, reconstructable

        @job
        def the_job():
            ...

        instance = DagsterInstance.get()
        result = execute_job(reconstructable(the_job), instance=instance)
        assert result.success


    If using the :py:meth:`~dagster.GraphDefinition.to_job` method to
    construct the ``JobDefinition``, then the invocation must be wrapped in a
    module-scope function, which can be passed to ``reconstructable``.

    .. code-block:: python

        from dagster import graph, reconstructable

        @graph
        def the_graph():
            ...

        def define_job():
            return the_graph.to_job(...)

        result = execute_job(reconstructable(define_job), ...)

    Since `execute_job` is potentially executing outside of the current
    process, output objects need to be retrieved by use of the provided job's
    io managers. Output objects can be retrieved by opening the result of
    `execute_job` as a context manager.

    .. code-block:: python

        from dagster import execute_job

        with execute_job(...) as result:
            output_obj = result.output_for_node("some_op")

    ``execute_job`` can also be used to reexecute a run, by providing a :py:class:`ReexecutionOptions` object.

    .. code-block:: python

        from dagster import ReexecutionOptions, execute_job

        instance = DagsterInstance.get()

        options = ReexecutionOptions.from_failure(run_id=failed_run_id, instance)
        execute_job(reconstructable(job), instance, reexecution_options=options)

    Parameters:
        job (ReconstructableJob): A reconstructable pointer to a :py:class:`JobDefinition`.
        instance (DagsterInstance): The instance to execute against.
        run_config (Optional[dict]): The configuration that parametrizes this run, as a dict.
        tags (Optional[Dict[str, Any]]): Arbitrary key-value pairs that will be added to run logs.
        raise_on_error (Optional[bool]): Whether or not to raise exceptions when they occur.
            Defaults to ``False``.
        op_selection (Optional[List[str]]): A list of op selection queries (including single
            op names) to execute. For example:

            - ``['some_op']``: selects ``some_op`` itself.
            - ``['*some_op']``: select ``some_op`` and all its ancestors (upstream dependencies).
            - ``['*some_op+++']``: select ``some_op``, all its ancestors, and its descendants
              (downstream dependencies) within 3 levels down.
            - ``['*some_op', 'other_op_a', 'other_op_b+']``: select ``some_op`` and all its
              ancestors, ``other_op_a`` itself, and ``other_op_b`` and its direct child ops.
        reexecution_options (Optional[ReexecutionOptions]):
            Reexecution options to provide to the run, if this run is
            intended to be a reexecution of a previous run. Cannot be used in
            tandem with the ``op_selection`` argument.

    Returns:
      :py:class:`JobExecutionResult`: The result of job execution.
    """
    check.inst_param(job, "job", ReconstructableJob)
    check.inst_param(instance, "instance", DagsterInstance)
    check.opt_sequence_param(asset_selection, "asset_selection", of_type=AssetKey)

    # get the repository load data here because we call job.get_definition() later in this fn
    job_def, _ = _job_with_repository_load_data(job)

    if reexecution_options is not None and op_selection is not None:
        raise DagsterInvariantViolationError(
            "re-execution and op selection cannot be used together at this time."
        )

    if reexecution_options:
        if run_config is None:
            run = check.not_none(instance.get_run_by_id(reexecution_options.parent_run_id))
            run_config = run.run_config
        return _reexecute_job(
            job_arg=job_def,
            run_config=run_config,
            reexecution_options=reexecution_options,
            tags=tags,
            instance=instance,
            raise_on_error=raise_on_error,
        )
    else:
        return _logged_execute_job(
            job_arg=job_def,
            instance=instance,
            run_config=run_config,
            tags=tags,
            op_selection=op_selection,
            raise_on_error=raise_on_error,
            asset_selection=asset_selection,
        )


@telemetry_wrapper
def _logged_execute_job(
    job_arg: Union[IJob, JobDefinition],
    instance: DagsterInstance,
    run_config: Optional[Mapping[str, object]] = None,
    tags: Optional[Mapping[str, str]] = None,
    op_selection: Optional[Sequence[str]] = None,
    raise_on_error: bool = True,
    asset_selection: Optional[Sequence[AssetKey]] = None,
) -> JobExecutionResult:
    check.inst_param(instance, "instance", DagsterInstance)

    job_arg, repository_load_data = _job_with_repository_load_data(job_arg)

    (
        job_arg,
        run_config,
        tags,
        resolved_op_selection,
        op_selection,
    ) = _check_execute_job_args(
        job_arg=job_arg,
        run_config=run_config,
        tags=tags,
        op_selection=op_selection,
    )

    log_repo_stats(instance=instance, job=job_arg, source="execute_pipeline")

    dagster_run = instance.create_run_for_job(
        job_def=job_arg.get_definition(),
        run_config=run_config,
        op_selection=op_selection,
        resolved_op_selection=resolved_op_selection,
        tags=tags,
        job_code_origin=(
            job_arg.get_python_origin() if isinstance(job_arg, ReconstructableJob) else None
        ),
        repository_load_data=repository_load_data,
        asset_selection=frozenset(asset_selection) if asset_selection else None,
    )

    return execute_run(
        job_arg,
        dagster_run,
        instance,
        raise_on_error=raise_on_error,
    )


def _reexecute_job(
    job_arg: Union[IJob, JobDefinition],
    run_config: Optional[Mapping[str, object]],
    reexecution_options: ReexecutionOptions,
    tags: Optional[Mapping[str, str]],
    instance: DagsterInstance,
    raise_on_error: bool,
) -> JobExecutionResult:
    """Reexecute an existing job run."""
    with ephemeral_instance_if_missing(instance) as execute_instance:
        job_arg, repository_load_data = _job_with_repository_load_data(job_arg)

        (job_arg, run_config, tags, _, _) = _check_execute_job_args(
            job_arg=job_arg,
            run_config=run_config,
            tags=tags,
        )

        parent_dagster_run = execute_instance.get_run_by_id(reexecution_options.parent_run_id)
        if parent_dagster_run is None:
            check.failed(
                f"No parent run with id {reexecution_options.parent_run_id} found in instance.",
            )

        execution_plan: Optional[ExecutionPlan] = None
        # resolve step selection DSL queries using parent execution information
        if isinstance(reexecution_options, ReexecuteFromFailureOption):
            step_keys, known_state = KnownExecutionState.build_resume_retry_reexecution(
                instance=instance,
                parent_run=parent_dagster_run,
            )
            execution_plan = create_execution_plan(
                job_arg,
                run_config,
                step_keys_to_execute=step_keys,
                known_state=known_state,
                tags=parent_dagster_run.tags,
            )
        elif reexecution_options.step_selection:
            execution_plan = _resolve_reexecute_step_selection(
                execute_instance,
                job_arg,
                run_config,
                cast(DagsterRun, parent_dagster_run),
                reexecution_options.step_selection,
            )
        # else all steps will be executed and parent state is not needed

        if parent_dagster_run.asset_selection:
            job_arg = job_arg.get_subset(
                op_selection=None, asset_selection=parent_dagster_run.asset_selection
            )

        dagster_run = execute_instance.create_run_for_job(
            job_def=job_arg.get_definition(),
            execution_plan=execution_plan,
            run_config=run_config,
            tags=tags,
            op_selection=parent_dagster_run.op_selection,
            asset_selection=parent_dagster_run.asset_selection,
            resolved_op_selection=parent_dagster_run.resolved_op_selection,
            root_run_id=parent_dagster_run.root_run_id or parent_dagster_run.run_id,
            parent_run_id=parent_dagster_run.run_id,
            job_code_origin=(
                job_arg.get_python_origin() if isinstance(job_arg, ReconstructableJob) else None
            ),
            repository_load_data=repository_load_data,
        )

        return execute_run(
            job_arg,
            dagster_run,
            execute_instance,
            raise_on_error=raise_on_error,
        )


def execute_plan_iterator(
    execution_plan: ExecutionPlan,
    job: IJob,
    dagster_run: DagsterRun,
    instance: DagsterInstance,
    retry_mode: Optional[RetryMode] = None,
    run_config: Optional[Mapping[str, object]] = None,
) -> Iterator[DagsterEvent]:
    check.inst_param(execution_plan, "execution_plan", ExecutionPlan)
    check.inst_param(job, "job", IJob)
    check.inst_param(dagster_run, "dagster_run", DagsterRun)
    check.inst_param(instance, "instance", DagsterInstance)
    retry_mode = check.opt_inst_param(retry_mode, "retry_mode", RetryMode, RetryMode.DISABLED)
    run_config = check.opt_mapping_param(run_config, "run_config")

    if isinstance(job, ReconstructableJob):
        job = job.with_repository_load_data(execution_plan.repository_load_data)

    return iter(
        ExecuteRunWithPlanIterable(
            execution_plan=execution_plan,
            iterator=inner_plan_execution_iterator,
            execution_context_manager=PlanExecutionContextManager(
                job=job,
                retry_mode=retry_mode,
                execution_plan=execution_plan,
                run_config=run_config,
                dagster_run=dagster_run,
                instance=instance,
            ),
        )
    )


def execute_plan(
    execution_plan: ExecutionPlan,
    job: IJob,
    instance: DagsterInstance,
    dagster_run: DagsterRun,
    run_config: Optional[Mapping[str, object]] = None,
    retry_mode: Optional[RetryMode] = None,
) -> Sequence[DagsterEvent]:
    """This is the entry point of dagster-graphql executions. For the dagster CLI entry point, see
    execute_job() above.
    """
    check.inst_param(execution_plan, "execution_plan", ExecutionPlan)
    check.inst_param(job, "job", IJob)
    check.inst_param(instance, "instance", DagsterInstance)
    check.inst_param(dagster_run, "dagster_run", DagsterRun)
    run_config = check.opt_mapping_param(run_config, "run_config")
    check.opt_inst_param(retry_mode, "retry_mode", RetryMode)

    return list(
        execute_plan_iterator(
            execution_plan=execution_plan,
            job=job,
            run_config=run_config,
            dagster_run=dagster_run,
            instance=instance,
            retry_mode=retry_mode,
        )
    )


def _get_execution_plan_from_run(
    job: IJob,
    dagster_run: DagsterRun,
    instance: DagsterInstance,
) -> ExecutionPlan:
    execution_plan_snapshot = (
        instance.get_execution_plan_snapshot(dagster_run.execution_plan_snapshot_id)
        if dagster_run.execution_plan_snapshot_id
        else None
    )

    return create_execution_plan(
        job,
        run_config=dagster_run.run_config,
        step_keys_to_execute=dagster_run.step_keys_to_execute,
        instance_ref=instance.get_ref() if instance.is_persistent else None,
        tags=dagster_run.tags,
        repository_load_data=(
            execution_plan_snapshot.repository_load_data if execution_plan_snapshot else None
        ),
        known_state=(
            execution_plan_snapshot.initial_known_state if execution_plan_snapshot else None
        ),
    )


def create_execution_plan(
    job: Union[IJob, JobDefinition],
    run_config: Optional[Mapping[str, object]] = None,
    step_keys_to_execute: Optional[Sequence[str]] = None,
    known_state: Optional[KnownExecutionState] = None,
    instance_ref: Optional[InstanceRef] = None,
    tags: Optional[Mapping[str, str]] = None,
    repository_load_data: Optional[RepositoryLoadData] = None,
) -> ExecutionPlan:
    if isinstance(job, IJob):
        # If you have repository_load_data, make sure to use it when building plan
        if isinstance(job, ReconstructableJob) and repository_load_data is not None:
            job = job.with_repository_load_data(repository_load_data)
        job_def = job.get_definition()
    else:
        job_def = job

    run_config = check.opt_mapping_param(run_config, "run_config", key_type=str)
    check.opt_nullable_sequence_param(step_keys_to_execute, "step_keys_to_execute", of_type=str)
    check.opt_inst_param(instance_ref, "instance_ref", InstanceRef)
    tags = check.opt_mapping_param(tags, "tags", key_type=str, value_type=str)
    known_state = check.opt_inst_param(
        known_state,
        "known_state",
        KnownExecutionState,
        default=KnownExecutionState(),
    )
    repository_load_data = check.opt_inst_param(
        repository_load_data, "repository_load_data", RepositoryLoadData
    )

    resolved_run_config = ResolvedRunConfig.build(job_def, run_config)

    return ExecutionPlan.build(
        job_def,
        resolved_run_config,
        step_keys_to_execute=step_keys_to_execute,
        known_state=known_state,
        instance_ref=instance_ref,
        tags=tags,
        repository_load_data=repository_load_data,
    )


def job_execution_iterator(
    job_context: PlanOrchestrationContext, execution_plan: ExecutionPlan
) -> Iterator[DagsterEvent]:
    """A complete execution of a pipeline. Yields pipeline start, success,
    and failure events.

    Args:
        pipeline_context (PlanOrchestrationContext):
        execution_plan (ExecutionPlan):
    """
    # TODO: restart event?
    if not job_context.resume_from_failure:
        yield DagsterEvent.job_start(job_context)

    job_exception_info = None
    job_canceled_info = None
    failed_steps: list[
        DagsterEvent
    ] = []  # A list of failed steps, with the earliest failure event at the front
    generator_closed = False
    try:
        for event in job_context.executor.execute(job_context, execution_plan):
            if event.is_step_failure:
                failed_steps.append(event)
            elif event.is_resource_init_failure and event.step_key:
                failed_steps.append(event)

            # Telemetry
            log_dagster_event(event, job_context)

            yield event
    except GeneratorExit:
        # Shouldn't happen, but avoid runtime-exception in case this generator gets GC-ed
        # (see https://amir.rachum.com/blog/2017/03/03/generator-cleanup/).
        generator_closed = True
        job_exception_info = serializable_error_info_from_exc_info(sys.exc_info())
        if job_context.raise_on_error:
            raise
    except (KeyboardInterrupt, DagsterExecutionInterruptedError):
        job_canceled_info = serializable_error_info_from_exc_info(sys.exc_info())
        if job_context.raise_on_error:
            raise
    except BaseException:
        job_exception_info = serializable_error_info_from_exc_info(sys.exc_info())
        if job_context.raise_on_error:
            raise  # finally block will run before this is re-raised
    finally:
        if job_canceled_info:
            reloaded_run = job_context.instance.get_run_by_id(job_context.run_id)
            if reloaded_run and reloaded_run.status == DagsterRunStatus.CANCELING:
                event = DagsterEvent.job_canceled(job_context, job_canceled_info)
            elif reloaded_run and reloaded_run.status == DagsterRunStatus.CANCELED:
                # This happens if the run was force-terminated but was still able to send
                # a cancellation request
                event = DagsterEvent.engine_event(
                    job_context,
                    "Computational resources were cleaned up after the run was forcibly marked"
                    " as canceled.",
                    EngineEventData(),
                )
            elif job_context.instance.run_will_resume(job_context.run_id):
                event = DagsterEvent.engine_event(
                    job_context,
                    "Execution was interrupted unexpectedly. No user initiated termination"
                    " request was found, not treating as failure because run will be resumed.",
                    EngineEventData(),
                )
            elif reloaded_run and reloaded_run.status == DagsterRunStatus.FAILURE:
                event = DagsterEvent.engine_event(
                    job_context,
                    "Execution was interrupted for a run that was already in a failure state.",
                    EngineEventData(),
                )
            else:
                event = DagsterEvent.job_failure(
                    job_context,
                    "Execution was interrupted unexpectedly. "
                    "No user initiated termination request was found, treating as failure.",
                    failure_reason=RunFailureReason.UNEXPECTED_TERMINATION,
                    error_info=job_canceled_info,
                )
        elif job_exception_info:
            reloaded_run = job_context.instance.get_run_by_id(job_context.run_id)
            if reloaded_run and reloaded_run.status == DagsterRunStatus.CANCELING:
                event = DagsterEvent.job_canceled(
                    job_context,
                    error_info=job_exception_info,
                    message="Run failed after it was requested to be terminated.",
                )
            else:
                event = DagsterEvent.job_failure(
                    job_context,
                    "An exception was thrown during execution.",
                    failure_reason=RunFailureReason.RUN_EXCEPTION,
                    error_info=job_exception_info,
                )
        elif failed_steps:
            reloaded_run = job_context.instance.get_run_by_id(job_context.run_id)
            failed_step_keys = [event.step_key for event in failed_steps]

            if reloaded_run and reloaded_run.status == DagsterRunStatus.CANCELING:
                event = DagsterEvent.job_canceled(
                    job_context,
                    error_info=None,
                    message=f"Run was canceled. Failed steps: {failed_step_keys}.",
                )
            else:
                event = DagsterEvent.job_failure(
                    job_context,
                    f"Steps failed: {failed_step_keys}.",
                    failure_reason=RunFailureReason.STEP_FAILURE,
                    first_step_failure_event=failed_steps[0],
                )
        else:
            event = DagsterEvent.job_success(job_context)
        if not generator_closed:
            yield event


class ExecuteRunWithPlanIterable:
    """Utility class to consolidate execution logic.

    This is a class and not a function because, e.g., in constructing a `scoped_pipeline_context`
    for `JobExecutionResult`, we need to pull out the `pipeline_context` after we're done
    yielding events. This broadly follows a pattern we make use of in other places,
    cf. `dagster._utils.EventGenerationManager`.
    """

    def __init__(
        self,
        execution_plan: ExecutionPlan,
        iterator: Callable[..., Iterator[DagsterEvent]],
        execution_context_manager: ExecutionContextManager[Any],
    ):
        self.execution_plan = check.inst_param(execution_plan, "execution_plan", ExecutionPlan)
        self.iterator = check.callable_param(iterator, "iterator")
        self.execution_context_manager = check.inst_param(
            execution_context_manager, "execution_context_manager", ExecutionContextManager
        )

        self.job_context = None

    def __iter__(self) -> Iterator[DagsterEvent]:
        # Since interrupts can't be raised at arbitrary points safely, delay them until designated
        # checkpoints during the execution.
        # To be maximally certain that interrupts are always caught during an execution process,
        # you can safely add an additional `with capture_interrupts()` at the very beginning of the
        # process that performs the execution.
        with capture_interrupts():
            yield from self.execution_context_manager.prepare_context()
            self.job_context = self.execution_context_manager.get_context()
            generator_closed = False
            try:
                if self.job_context:  # False if we had a pipeline init failure
                    yield from self.iterator(
                        execution_plan=self.execution_plan,
                        job_context=self.job_context,
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


def _check_execute_job_args(
    job_arg: Union[JobDefinition, IJob],
    run_config: Optional[Mapping[str, object]],
    tags: Optional[Mapping[str, str]],
    op_selection: Optional[Sequence[str]] = None,
) -> tuple[
    IJob,
    Optional[Mapping],
    Mapping[str, str],
    Optional[AbstractSet[str]],
    Optional[Sequence[str]],
]:
    ijob = InMemoryJob(job_arg) if isinstance(job_arg, JobDefinition) else job_arg
    job_def = job_arg if isinstance(job_arg, JobDefinition) else job_arg.get_definition()

    run_config = check.opt_mapping_param(run_config, "run_config")

    tags = check.opt_mapping_param(tags, "tags", key_type=str)
    check.opt_sequence_param(op_selection, "op_selection", of_type=str)

    tags = merge_dicts(job_def.run_tags, tags)

    # generate job subset from the given op_selection
    if op_selection:
        ijob = ijob.get_subset(op_selection=op_selection)

    return (
        ijob,
        run_config,
        tags,
        ijob.resolved_op_selection,
        op_selection,
    )


def _resolve_reexecute_step_selection(
    instance: DagsterInstance,
    job: IJob,
    run_config: Optional[Mapping],
    parent_dagster_run: DagsterRun,
    step_selection: Sequence[str],
) -> ExecutionPlan:
    if parent_dagster_run.op_selection:
        job = job.get_subset(op_selection=parent_dagster_run.op_selection)

    state = KnownExecutionState.build_for_reexecution(instance, parent_dagster_run)

    parent_plan = create_execution_plan(
        job,
        parent_dagster_run.run_config,
        known_state=state,
    )
    step_keys_to_execute = parse_step_selection(parent_plan.get_all_step_deps(), step_selection)
    return create_execution_plan(
        job,
        run_config,
        step_keys_to_execute=list(step_keys_to_execute),
        known_state=state.update_for_step_selection(step_keys_to_execute),
        tags=parent_dagster_run.tags,
    )


def _job_with_repository_load_data(
    job_arg: Union[JobDefinition, IJob],
) -> tuple[Union[JobDefinition, IJob], Optional[RepositoryLoadData]]:
    """For ReconstructableJob, generate and return any required RepositoryLoadData, alongside
    a ReconstructableJob with this repository load data baked in.
    """
    if isinstance(job_arg, ReconstructableJob):
        # Unless this ReconstructableJob alread has repository_load_data attached, this will
        # force the repository_load_data to be computed from scratch.
        repository_load_data = job_arg.repository.get_definition().repository_load_data
        return job_arg.with_repository_load_data(repository_load_data), repository_load_data
    return job_arg, None
