from collections import defaultdict
from typing import Dict, List, NamedTuple, cast

import dagster._check as check
from dagster.core.events.log import EventLogEntry
from dagster.core.execution.plan.outputs import StepOutputHandle
from dagster.core.execution.retries import RetryState
from dagster.serdes import whitelist_for_serdes


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
        ],
    )
):
    """
    A snapshot for the parts of an on going execution that need to be handed down when delegating
    step execution to another machine/process. This includes things like previous retries and
    resolved dynamic outputs.
    """

    def __new__(cls, previous_retry_attempts, dynamic_mappings, step_output_versions=None):

        return super(KnownExecutionState, cls).__new__(
            cls,
            check.dict_param(
                previous_retry_attempts, "previous_retry_attempts", key_type=str, value_type=int
            ),
            check.dict_param(dynamic_mappings, "dynamic_mappings", key_type=str, value_type=dict),
            check.opt_list_param(
                step_output_versions, "step_output_versions", of_type=StepOutputVersionData
            ),
        )

    def get_retry_state(self):
        return RetryState(self.previous_retry_attempts)

    @staticmethod
    def derive_from_logs(logs: List[EventLogEntry]) -> "KnownExecutionState":
        """
        Derive the known state from iterating over the event logs
        """

        previous_retry_attempts: Dict[str, int] = defaultdict(int)
        dynamic_outputs: Dict[str, Dict[str, List[str]]] = defaultdict(lambda: defaultdict(list))
        successful_dynamic_mappings: Dict[str, Dict[str, List[str]]] = {}

        for log in logs:
            if not log.is_dagster_event:
                continue
            event = log.get_dagster_event()

            step_key = cast(str, event.step_key)

            # record dynamic outputs
            if event.is_successful_output and event.step_output_data.mapping_key:
                dynamic_outputs[step_key][event.step_output_data.output_name].append(
                    event.step_output_data.mapping_key
                )

            # on a retry
            if event.is_step_up_for_retry:
                # tally up retry attempt
                previous_retry_attempts[step_key] += 1

                # clear any existing tracked mapping keys
                if event.step_key in dynamic_outputs:
                    for mapping_list in dynamic_outputs[step_key].values():
                        mapping_list.clear()

            # commit the set of dynamic outputs once the step is successful
            if event.is_step_success and step_key in dynamic_outputs:
                successful_dynamic_mappings[step_key] = dict(dynamic_outputs[step_key])

        return KnownExecutionState(
            dict(previous_retry_attempts),
            successful_dynamic_mappings,
        )

    @staticmethod
    def for_reexecution(
        parent_run_logs: List[EventLogEntry], step_keys_to_execute: List[str]
    ) -> "KnownExecutionState":
        """
        Copy over dynamic mappings from previous run, but drop any for steps that we intend to re-execute
        """
        parent_state = KnownExecutionState.derive_from_logs(parent_run_logs)
        dynamic_mappings_to_use = {
            step_key: parent_state.dynamic_mappings[step_key]
            for step_key in parent_state.dynamic_mappings.keys()
            if step_key not in step_keys_to_execute
        }
        return KnownExecutionState({}, dynamic_mappings_to_use)
