from collections import defaultdict
from typing import (
    TYPE_CHECKING,
    Dict,
    List,
    Mapping,
    NamedTuple,
    Optional,
    Sequence,
    Set,
    Tuple,
    cast,
)

from typing_extensions import TypeAlias

import dagster._check as check
from dagster._core.errors import DagsterExecutionPlanSnapshotNotFoundError, DagsterRunNotFoundError
from dagster._core.events import DagsterEventType
from dagster._core.execution.plan.handle import StepHandle, UnresolvedStepHandle
from dagster._core.execution.plan.outputs import StepOutputHandle
from dagster._core.execution.plan.step import ResolvedFromDynamicStepHandle
from dagster._core.execution.retries import RetryState
from dagster._core.instance import DagsterInstance
from dagster._core.storage.dagster_run import DagsterRun
from dagster._serdes import whitelist_for_serdes

if TYPE_CHECKING:
    from dagster._core.execution.plan.plan import StepHandleUnion


@whitelist_for_serdes
class StepOutputVersionData(NamedTuple):
    step_output_handle: StepOutputHandle
    version: str

    @staticmethod
    def get_version_list_from_dict(
        step_output_versions: Mapping[StepOutputHandle, str]
    ) -> Sequence["StepOutputVersionData"]:
        return [
            StepOutputVersionData(step_output_handle=step_output_handle, version=version)
            for step_output_handle, version in step_output_versions.items()
        ]

    @staticmethod
    def get_version_dict_from_list(
        step_output_versions: Sequence["StepOutputVersionData"],
    ) -> Mapping[StepOutputHandle, str]:
        return {data.step_output_handle: data.version for data in step_output_versions}


@whitelist_for_serdes
class PastExecutionState(
    NamedTuple(
        "_PastExecutionState",
        [
            ("run_id", str),
            ("produced_outputs", Set[StepOutputHandle]),
            # PastExecutionState, but no cycles allowed in NT
            ("parent_state", Optional[object]),
        ],
    )
):
    """Information relevant to execution about the parent run, notably which outputs
    were produced by which run ids, allowing for the proper ones to be loaded.
    """

    def __new__(
        cls,
        run_id: str,
        produced_outputs: Set[StepOutputHandle],
        parent_state: Optional["PastExecutionState"],
    ):
        return super().__new__(
            cls,
            check.str_param(run_id, "run_id"),
            check.set_param(produced_outputs, "produced_outputs", StepOutputHandle),
            check.opt_inst_param(parent_state, "parent_state", PastExecutionState),
        )

    def get_parent_state(self) -> Optional["PastExecutionState"]:
        return cast(Optional[PastExecutionState], self.parent_state)


@whitelist_for_serdes
class KnownExecutionState(
    NamedTuple(
        "_KnownExecutionState",
        [
            # step_key -> count
            ("previous_retry_attempts", Mapping[str, int]),
            # step_key -> output_name -> mapping_keys
            ("dynamic_mappings", Mapping[str, Mapping[str, Optional[Sequence[str]]]]),
            # step_output_handle -> version
            ("step_output_versions", Sequence[StepOutputVersionData]),
            ("ready_outputs", Set[StepOutputHandle]),
            ("parent_state", Optional[PastExecutionState]),
        ],
    )
):
    """A snapshot for the parts of an on going execution that need to be handed down when delegating
    step execution to another machine/process. This includes things like previous retries and
    resolved dynamic outputs.
    """

    def __new__(
        cls,
        previous_retry_attempts: Optional[Mapping[str, int]] = None,
        dynamic_mappings: Optional[Mapping[str, Mapping[str, Optional[Sequence[str]]]]] = None,
        step_output_versions: Optional[Sequence[StepOutputVersionData]] = None,
        ready_outputs: Optional[Set[StepOutputHandle]] = None,
        parent_state: Optional[PastExecutionState] = None,
    ):
        dynamic_mappings = check.opt_mapping_param(
            dynamic_mappings,
            "dynamic_mappings",
            key_type=str,
            value_type=dict,
        )
        # some old payloads (0.15.0 -> 0.15.6) were persisted with [None] mapping_keys
        # in dynamic_mappings, so can't assert [str] here in __new__.

        return super(KnownExecutionState, cls).__new__(
            cls,
            check.opt_mapping_param(
                previous_retry_attempts,
                "previous_retry_attempts",
                key_type=str,
                value_type=int,
            ),
            dynamic_mappings,
            check.opt_sequence_param(
                step_output_versions, "step_output_versions", of_type=StepOutputVersionData
            ),
            check.opt_set_param(ready_outputs, "ready_outputs", StepOutputHandle),
            check.opt_inst_param(parent_state, "parent_state", PastExecutionState),
        )

    def get_retry_state(self) -> RetryState:
        return RetryState(self.previous_retry_attempts)

    def update_for_step_selection(self, step_keys_to_execute) -> "KnownExecutionState":
        dynamic_mappings_to_use = {
            step_key: self.dynamic_mappings[step_key]
            for step_key in self.dynamic_mappings.keys()
            if step_key not in step_keys_to_execute
        }
        return self._replace(
            dynamic_mappings=dynamic_mappings_to_use,
        )

    @staticmethod
    def build_resume_retry_reexecution(
        instance: DagsterInstance,
        parent_run: DagsterRun,
    ) -> Tuple[Sequence[str], "KnownExecutionState"]:
        steps_to_retry, known_state = _derive_state_from_logs(instance, parent_run)
        return steps_to_retry, known_state.update_for_step_selection(steps_to_retry)

    @staticmethod
    def build_for_reexecution(
        instance: DagsterInstance,
        parent_run: DagsterRun,
    ) -> "KnownExecutionState":
        _, known_state = _derive_state_from_logs(instance, parent_run)
        return known_state


TrackingDict: TypeAlias = Dict[str, Set["StepHandleUnion"]]


def _copy_from_tracking_dict(
    dst: TrackingDict,
    src: TrackingDict,
    handle: "StepHandleUnion",
) -> None:
    if isinstance(handle, ResolvedFromDynamicStepHandle):
        key = handle.unresolved_form.to_key()
    else:
        key = handle.to_key()
    check.invariant(key in src)
    dst[key].update(src[key])


def _update_tracking_dict(tracking: TrackingDict, handle: "StepHandleUnion") -> None:
    if isinstance(handle, ResolvedFromDynamicStepHandle):
        tracking[handle.unresolved_form.to_key()].add(handle)
    else:
        tracking[handle.to_key()].add(handle)


def _in_tracking_dict(handle: "StepHandleUnion", tracking: TrackingDict) -> bool:
    if isinstance(handle, ResolvedFromDynamicStepHandle):
        unresolved_key = handle.unresolved_form.to_key()
        if unresolved_key in tracking:
            return handle in tracking[unresolved_key]
        else:
            return False
    else:
        return handle.to_key() in tracking


def _derive_state_of_past_run(
    instance: DagsterInstance,
    parent_run: DagsterRun,
) -> Tuple[
    Sequence[str], Mapping[str, Mapping[str, Optional[Sequence[str]]]], Set[StepOutputHandle]
]:
    from dagster._core.host_representation import ExternalExecutionPlan

    check.inst_param(instance, "instance", DagsterInstance)
    check.opt_inst_param(parent_run, "parent_run", DagsterRun)

    parent_run_id = parent_run.run_id
    parent_run_logs = instance.all_logs(
        parent_run_id,
        of_type={
            DagsterEventType.STEP_FAILURE,
            DagsterEventType.STEP_SUCCESS,
            DagsterEventType.STEP_OUTPUT,
            DagsterEventType.STEP_SKIPPED,
            DagsterEventType.RESOURCE_INIT_FAILURE,
        },
    )

    execution_plan_snapshot = instance.get_execution_plan_snapshot(
        check.not_none(parent_run.execution_plan_snapshot_id)
    )

    if not execution_plan_snapshot:
        raise DagsterExecutionPlanSnapshotNotFoundError(
            f"Could not load execution plan snapshot for run {parent_run_id}"
        )

    execution_plan = ExternalExecutionPlan(execution_plan_snapshot=execution_plan_snapshot)

    output_set: Set[StepOutputHandle] = set()
    observed_dynamic_outputs: Dict[str, Dict[str, List[str]]] = defaultdict(
        lambda: defaultdict(list)
    )

    # keep track of steps with dicts that point:
    # * step_key -> set(step_handle) in the normal case
    # * unresolved_step_key -> set(resolved_step_handle, ...) for dynamic outputs
    all_steps_in_parent_run_logs: TrackingDict = defaultdict(set)
    failed_steps_in_parent_run_logs: TrackingDict = defaultdict(set)
    successful_steps_in_parent_run_logs: TrackingDict = defaultdict(set)
    interrupted_steps_in_parent_run_logs: TrackingDict = defaultdict(set)
    skipped_steps_in_parent_run_logs: TrackingDict = defaultdict(set)

    for record in parent_run_logs:
        if record.dagster_event and record.dagster_event.step_handle:
            step_handle = record.dagster_event.step_handle
            _update_tracking_dict(all_steps_in_parent_run_logs, step_handle)

            if record.dagster_event_type == DagsterEventType.STEP_FAILURE:
                _update_tracking_dict(failed_steps_in_parent_run_logs, step_handle)

            if record.dagster_event_type == DagsterEventType.RESOURCE_INIT_FAILURE:
                _update_tracking_dict(failed_steps_in_parent_run_logs, step_handle)

            if record.dagster_event_type == DagsterEventType.STEP_SUCCESS:
                _update_tracking_dict(successful_steps_in_parent_run_logs, step_handle)

            if record.dagster_event_type == DagsterEventType.STEP_SKIPPED:
                _update_tracking_dict(skipped_steps_in_parent_run_logs, step_handle)

            if record.dagster_event_type == DagsterEventType.STEP_OUTPUT:
                output_data = record.get_dagster_event().step_output_data
                if output_data.mapping_key:
                    observed_dynamic_outputs[record.step_key][output_data.output_name].append(  # type: ignore
                        output_data.mapping_key
                    )
                output_set.add(output_data.step_output_handle)

    for step_set in all_steps_in_parent_run_logs.values():
        for step_handle in step_set:
            if (
                not _in_tracking_dict(step_handle, failed_steps_in_parent_run_logs)
                and not _in_tracking_dict(step_handle, successful_steps_in_parent_run_logs)
                and not _in_tracking_dict(step_handle, skipped_steps_in_parent_run_logs)
            ):
                _update_tracking_dict(interrupted_steps_in_parent_run_logs, step_handle)

    # expand type to allow filling in None mappings for skips
    dynamic_outputs = cast(Dict[str, Dict[str, Optional[List[str]]]], observed_dynamic_outputs)
    to_retry: TrackingDict = defaultdict(set)
    execution_deps = execution_plan.execution_deps()
    for step_snap in execution_plan.topological_steps():
        step_key = step_snap.key
        step_handle = StepHandle.parse_from_key(step_snap.key)

        if parent_run.step_keys_to_execute and step_snap.key not in parent_run.step_keys_to_execute:
            continue

        for output in step_snap.outputs:
            if output.properties.is_dynamic:
                if step_key in dynamic_outputs and output.name in dynamic_outputs[step_key]:
                    continue
                elif step_key in successful_steps_in_parent_run_logs:
                    if output.properties.is_required:
                        dynamic_outputs[step_key][output.name] = []
                    else:
                        dynamic_outputs[step_key][output.name] = None
                elif step_key in skipped_steps_in_parent_run_logs:
                    dynamic_outputs[step_key][output.name] = None

        if _in_tracking_dict(step_handle, failed_steps_in_parent_run_logs):
            _copy_from_tracking_dict(to_retry, failed_steps_in_parent_run_logs, step_handle)

        # Interrupted steps can occur when graceful cleanup from a step failure fails to run,
        # and a step failure event is not generated
        if _in_tracking_dict(step_handle, interrupted_steps_in_parent_run_logs):
            _copy_from_tracking_dict(to_retry, interrupted_steps_in_parent_run_logs, step_handle)

        step_dep_keys = execution_deps[step_key]

        # Missing steps did not execute, e.g. when a run was terminated
        if (not _in_tracking_dict(step_handle, all_steps_in_parent_run_logs)) and not (
            isinstance(step_handle, UnresolvedStepHandle)
            and any(
                (
                    key in skipped_steps_in_parent_run_logs
                    or key in successful_steps_in_parent_run_logs
                )
                for key in step_dep_keys
            )
        ):
            _update_tracking_dict(to_retry, step_handle)

        retrying_dep_keys = step_dep_keys.intersection(to_retry.keys())

        # this step is downstream of a step we are about to retry
        if retrying_dep_keys:
            for retrying_key in retrying_dep_keys:
                # If this step and its ancestor are both downstream of a dynamic output,
                # add resolved instances of this step for the retrying mapping keys
                if isinstance(step_handle, UnresolvedStepHandle) and all(
                    isinstance(handle, ResolvedFromDynamicStepHandle)
                    for handle in to_retry[retrying_key]
                ):
                    for resolved_handle in to_retry[retrying_key]:
                        _update_tracking_dict(
                            to_retry, step_handle.resolve(resolved_handle.mapping_key)  # type: ignore  # (must be ResolvedFromDynamicStepHandle)
                        )

                else:
                    _update_tracking_dict(to_retry, step_handle)

    steps_to_retry = [
        step_handle.to_key() for step_set in to_retry.values() for step_handle in step_set
    ]

    return steps_to_retry, dynamic_outputs, output_set


def _derive_state_from_logs(
    instance: DagsterInstance,
    parent_run: DagsterRun,
) -> Tuple[Sequence[str], "KnownExecutionState"]:
    # recursively build parent state chain

    def _create_parent_state(target_run):
        steps_to_retry, dynamic_outputs, output_set = _derive_state_of_past_run(
            instance, target_run
        )
        parent_parent_run = None
        if target_run.parent_run_id:
            run = instance.get_run_by_id(target_run.parent_run_id)
            if not run:
                raise DagsterRunNotFoundError(
                    f"Could not load ancestor run {target_run.parent_run_id} for re-execution",
                    invalid_run_id=target_run.parent_run_id,
                )
            parent_parent_run, parent_dynamic_outputs, _ = _create_parent_state(run)
            dynamic_outputs = {**parent_dynamic_outputs, **dynamic_outputs}

        return (
            PastExecutionState(
                target_run.run_id,
                output_set,
                parent_parent_run,
            ),
            dynamic_outputs,
            steps_to_retry,
        )

    parent_state, dynamic_mappings, steps_to_retry = _create_parent_state(parent_run)

    return steps_to_retry, KnownExecutionState(
        previous_retry_attempts={},  # no need to calculate these for re-execution
        dynamic_mappings=dynamic_mappings,
        step_output_versions=None,
        ready_outputs=None,
        parent_state=parent_state,
    )
