from collections import defaultdict
from typing import Dict, List, NamedTuple, Optional, Set, cast

import dagster._check as check
from dagster._core.errors import DagsterRunNotFoundError
from dagster._core.events import DagsterEventType
from dagster._core.execution.plan.outputs import StepOutputHandle
from dagster._core.execution.retries import RetryState
from dagster._core.instance import DagsterInstance
from dagster._core.storage.pipeline_run import DagsterRun
from dagster._serdes import whitelist_for_serdes


@whitelist_for_serdes
class StepOutputVersionData(NamedTuple):
    step_output_handle: StepOutputHandle
    version: str

    @staticmethod
    def get_version_list_from_dict(
        step_output_versions: Dict[StepOutputHandle, str]
    ) -> List["StepOutputVersionData"]:
        return [
            StepOutputVersionData(step_output_handle=step_output_handle, version=version)
            for step_output_handle, version in step_output_versions.items()
        ]

    @staticmethod
    def get_version_dict_from_list(
        step_output_versions: List["StepOutputVersionData"],
    ) -> Dict[StepOutputHandle, str]:
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
    """
    Information relevant to execution about the parent run, notably which outputs
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
            ("previous_retry_attempts", Dict[str, int]),
            # step_key -> output_name -> mapping_keys
            ("dynamic_mappings", Dict[str, Dict[str, List[str]]]),
            # step_output_handle -> version
            ("step_output_versions", List[StepOutputVersionData]),
            ("ready_outputs", Set[StepOutputHandle]),
            ("parent_state", Optional[PastExecutionState]),
        ],
    )
):
    """
    A snapshot for the parts of an on going execution that need to be handed down when delegating
    step execution to another machine/process. This includes things like previous retries and
    resolved dynamic outputs.
    """

    def __new__(
        cls,
        previous_retry_attempts: Optional[Dict[str, int]] = None,
        dynamic_mappings: Optional[Dict[str, Dict[str, List[str]]]] = None,
        step_output_versions: Optional[List[StepOutputVersionData]] = None,
        ready_outputs: Optional[Set[StepOutputHandle]] = None,
        parent_state: Optional[PastExecutionState] = None,
    ):
        dynamic_mappings = check.opt_dict_param(
            dynamic_mappings,
            "dynamic_mappings",
            key_type=str,
            value_type=dict,
        )
        # some old payloads (0.15.0 -> 0.15.6) were persisted with [None] mapping_keys
        # in dynamic_mappings, so can't assert [str] here in __new__.

        return super(KnownExecutionState, cls).__new__(
            cls,
            check.opt_dict_param(
                previous_retry_attempts,
                "previous_retry_attempts",
                key_type=str,
                value_type=int,
            ),
            dynamic_mappings,
            check.opt_list_param(
                step_output_versions, "step_output_versions", of_type=StepOutputVersionData
            ),
            check.opt_set_param(ready_outputs, "ready_outputs", StepOutputHandle),
            check.opt_inst_param(parent_state, "parent_state", PastExecutionState),
        )

    def get_retry_state(self):
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
    def build_for_reexecution(
        instance: DagsterInstance,
        parent_run: DagsterRun,
    ) -> "KnownExecutionState":

        # recursively build parent state chain

        def _create_parent_state(target_run):
            output_set = set()
            dynamic_outputs = defaultdict(lambda: defaultdict(list))
            for output_record in instance.all_logs(
                target_run.run_id, of_type=DagsterEventType.STEP_OUTPUT
            ):
                output_data = output_record.get_dagster_event().step_output_data
                if output_data.mapping_key:
                    dynamic_outputs[output_record.step_key][output_data.output_name].append(
                        output_data.mapping_key
                    )
                output_set.add(output_data.step_output_handle)

            parent_parent_run = None
            if target_run.parent_run_id:
                run = instance.get_run_by_id(target_run.parent_run_id)
                if not run:
                    raise DagsterRunNotFoundError(
                        f"Could not load ancestor run {target_run.parent_run_id} for re-execution",
                        invalid_run_id=target_run.parent_run_id,
                    )
                parent_parent_run, _ = _create_parent_state(run)

            return (
                PastExecutionState(
                    target_run.run_id,
                    output_set,
                    parent_parent_run,
                ),
                dynamic_outputs,
            )

        parent_state, dynamic_mappings = _create_parent_state(parent_run)

        return KnownExecutionState(
            previous_retry_attempts={},  # no need to calculate these for re-execution
            dynamic_mappings=dynamic_mappings,
            step_output_versions=None,
            ready_outputs=None,
            parent_state=parent_state,
        )
