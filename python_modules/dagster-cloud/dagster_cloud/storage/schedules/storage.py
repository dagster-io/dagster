from collections.abc import Iterable, Sequence
from typing import TYPE_CHECKING, Any

import dagster._check as check
from dagster._core.definitions.asset_key import EntityKey
from dagster._core.definitions.declarative_automation.serialized_objects import (
    AutomationConditionEvaluationWithRunIds,
)
from dagster._core.definitions.run_request import InstigatorType
from dagster._core.scheduler.instigation import (
    AutoMaterializeAssetEvaluationRecord,
    InstigatorState,
    InstigatorStatus,
    InstigatorTick,
    TickData,
    TickStatus,
)
from dagster._core.storage.schedules.base import ScheduleStorage
from dagster._serdes import (
    ConfigurableClass,
    ConfigurableClassData,
    deserialize_value,
    serialize_value,
)
from typing_extensions import Self

from dagster_cloud.storage.schedules.queries import (
    ADD_JOB_STATE_MUTATION,
    ALL_STORED_JOB_STATE_QUERY,
    CREATE_JOB_TICK_MUTATION,
    GET_JOB_STATE_QUERY,
    GET_JOB_TICKS_QUERY,
    UPDATE_JOB_STATE_MUTATION,
    UPDATE_JOB_TICK_MUTATION,
)

if TYPE_CHECKING:
    from dagster_cloud.instance import DagsterCloudAgentInstance  # noqa: F401


class GraphQLScheduleStorage(ScheduleStorage["DagsterCloudAgentInstance"], ConfigurableClass):
    def __init__(self, inst_data=None, override_graphql_client=None):
        """Initialize this class directly only for test (using `override_graphql_client`).
        Use the ConfigurableClass machinery to init from instance yaml.
        """
        self._inst_data = check.opt_inst_param(inst_data, "inst_data", ConfigurableClassData)
        self._override_graphql_client = override_graphql_client

    @property
    def inst_data(self):
        return self._inst_data

    @classmethod
    def config_type(cls):
        return {}

    @classmethod
    def from_config_value(cls, inst_data: ConfigurableClassData, config_value: Any) -> Self:
        return cls(inst_data=inst_data)

    @property
    def _graphql_client(self):
        return (
            self._override_graphql_client
            if self._override_graphql_client
            else self._instance.graphql_client
        )

    def _execute_query(self, query, variables=None):
        return self._graphql_client.execute(query, variable_values=variables)

    def wipe(self):
        raise Exception("Not allowed to wipe from user cloud")

    def all_instigator_state(  # ty: ignore[invalid-method-override], fix me!
        self,
        repository_origin_id: str | None = None,
        repository_selector_id: str | None = None,
        instigator_type: InstigatorType | None = None,
        instigator_statuses: set[InstigatorStatus] | None = None,
    ) -> Iterable[InstigatorState]:
        res = self._execute_query(
            ALL_STORED_JOB_STATE_QUERY,
            variables={
                "repositoryOriginId": repository_origin_id,
                "repositorySelectorId": repository_selector_id,
                "jobType": instigator_type.value if instigator_type else None,
                "statuses": (
                    [status.value for status in instigator_statuses]
                    if instigator_statuses
                    else None
                ),
            },
        )

        return [
            deserialize_value(state, InstigatorState)
            for state in res["data"]["schedules"]["jobStates"]
        ]

    def get_instigator_state(self, origin_id: str, selector_id: str) -> InstigatorState | None:
        res = self._execute_query(
            GET_JOB_STATE_QUERY,
            variables={
                "jobOriginId": origin_id,
                "selectorId": selector_id,
            },
        )

        state = res["data"]["schedules"]["jobState"]
        if state is None:
            return None

        return deserialize_value(state, InstigatorState)

    def add_instigator_state(self, state: InstigatorState):
        self._execute_query(
            ADD_JOB_STATE_MUTATION,
            variables={
                "serializedJobState": serialize_value(
                    check.inst_param(state, "state", InstigatorState)
                )
            },
        )

    def update_instigator_state(self, state: InstigatorState):
        self._execute_query(
            UPDATE_JOB_STATE_MUTATION,
            variables={
                "serializedJobState": serialize_value(
                    check.inst_param(state, "state", InstigatorState)
                )
            },
        )

    def delete_instigator_state(self, origin_id: str, selector_id: str):
        raise NotImplementedError("Not callable from user cloud")

    def get_tick(self, tick_id: int) -> InstigatorTick:
        raise NotImplementedError("Not callable from user cloud")

    def get_ticks(  # ty: ignore[invalid-method-override], fix me!
        self,
        origin_id: str,
        selector_id: str,
        before: float | None = None,
        after: float | None = None,
        limit: int | None = None,
        statuses: Sequence[TickStatus] | None = None,
    ) -> Iterable[InstigatorTick]:
        status_strs = [status.value for status in statuses] if statuses else None
        res = self._execute_query(
            GET_JOB_TICKS_QUERY,
            variables={
                "jobOriginId": origin_id,
                "selectorId": selector_id,
                "before": before,
                "after": after,
                "limit": limit,
                "statuses": status_strs,
            },
        )

        return [
            deserialize_value(tick, InstigatorTick) for tick in res["data"]["schedules"]["jobTicks"]
        ]

    def create_tick(self, tick_data: TickData):
        res = self._execute_query(
            CREATE_JOB_TICK_MUTATION,
            variables={
                "serializedJobTickData": serialize_value(
                    check.inst_param(tick_data, "tick_data", TickData)
                )
            },
        )

        tick_id = res["data"]["schedules"]["createJobTick"]["tickId"]
        return InstigatorTick(tick_id, tick_data)

    def update_tick(self, tick: InstigatorTick):
        self._execute_query(
            UPDATE_JOB_TICK_MUTATION,
            variables={
                "tickId": tick.tick_id,
                "serializedJobTickData": serialize_value(
                    check.inst_param(tick.tick_data, "tick_data", TickData)
                ),
            },
        )
        return tick

    def purge_ticks(
        self,
        origin_id: str,
        selector_id: str,
        before: float,
        tick_statuses: Sequence[TickStatus] | None = None,
    ):
        raise NotImplementedError("Not callable from user cloud")

    def add_auto_materialize_asset_evaluations(
        self,
        evaluation_id: int,
        asset_evaluations: Sequence[AutomationConditionEvaluationWithRunIds],
    ) -> None:
        raise NotImplementedError("Not callable from user cloud")

    def get_auto_materialize_asset_evaluations(
        self, key: EntityKey, limit: int, cursor: int | None = None
    ) -> Sequence[AutoMaterializeAssetEvaluationRecord]:
        raise NotImplementedError("Not callable from user cloud")

    def get_auto_materialize_evaluations_for_evaluation_id(
        self, evaluation_id: int
    ) -> Sequence[AutoMaterializeAssetEvaluationRecord]:
        raise NotImplementedError("Not callable from user cloud")

    def purge_asset_evaluations(self, before: float):
        raise NotImplementedError("Not callable from user cloud")

    def upgrade(self):
        raise NotImplementedError("Not callable from user cloud")
