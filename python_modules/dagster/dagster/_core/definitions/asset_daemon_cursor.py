import dataclasses
import json
from dataclasses import dataclass
from functools import cached_property
from typing import (
    TYPE_CHECKING,
    Mapping,
    NamedTuple,
    Optional,
    Sequence,
)

from dagster._core.definitions.asset_graph_subset import AssetGraphSubset
from dagster._core.definitions.asset_subset import AssetSubset
from dagster._core.definitions.events import AssetKey
from dagster._serdes.serdes import (
    FieldSerializer,
    JsonSerializableValue,
    PackableValue,
    SerializableNonScalarKeyMapping,
    UnpackContext,
    WhitelistMap,
    pack_value,
    unpack_value,
    whitelist_for_serdes,
)

from .asset_graph import AssetGraph

if TYPE_CHECKING:
    from .asset_condition.asset_condition import (
        AssetConditionEvaluation,
        AssetConditionEvaluationState,
        AssetConditionSnapshot,
    )


@whitelist_for_serdes
class AssetConditionCursorExtras(NamedTuple):
    """Represents additional state that may be optionally saved by an AssetCondition between
    evaluations.
    """

    condition_snapshot: "AssetConditionSnapshot"
    extras: Mapping[str, PackableValue]


class ObserveRequestTimestampSerializer(FieldSerializer):
    def pack(
        self,
        mapping: Mapping[str, float],
        whitelist_map: WhitelistMap,
        descent_path: str,
    ) -> JsonSerializableValue:
        return pack_value(SerializableNonScalarKeyMapping(mapping), whitelist_map, descent_path)

    def unpack(
        self,
        unpacked_value: JsonSerializableValue,
        whitelist_map: WhitelistMap,
        context: UnpackContext,
    ) -> PackableValue:
        return unpack_value(unpacked_value, dict, whitelist_map, context)


@whitelist_for_serdes(
    field_serializers={
        "last_observe_request_timestamp_by_asset_key": ObserveRequestTimestampSerializer
    }
)
@dataclass(frozen=True)
class AssetDaemonCursor:
    """State that's stored between daemon evaluations.

    Attributes:
        evaluation_id (int): The ID of the evaluation that produced this cursor.
        previous_evaluation_state (Sequence[AssetConditionEvaluationInfo]): The evaluation info
            recorded for each asset on the previous tick.
    """

    evaluation_id: int
    previous_evaluation_state: Sequence["AssetConditionEvaluationState"]

    last_observe_request_timestamp_by_asset_key: Mapping[AssetKey, float]

    @staticmethod
    def empty(evaluation_id: int = 0) -> "AssetDaemonCursor":
        return AssetDaemonCursor(
            evaluation_id=evaluation_id,
            previous_evaluation_state=[],
            last_observe_request_timestamp_by_asset_key={},
        )

    @cached_property
    def previous_evaluation_state_by_key(
        self,
    ) -> Mapping[AssetKey, "AssetConditionEvaluationState"]:
        """Efficient lookup of previous evaluation info by asset key."""
        return {
            evaluation_state.asset_key: evaluation_state
            for evaluation_state in self.previous_evaluation_state
        }

    def get_previous_evaluation_state(
        self, asset_key: AssetKey
    ) -> Optional["AssetConditionEvaluationState"]:
        """Returns the AssetConditionCursor associated with the given asset key. If no stored
        cursor exists, returns an empty cursor.
        """
        return self.previous_evaluation_state_by_key.get(asset_key)

    def get_previous_evaluation(self, asset_key: AssetKey) -> Optional["AssetConditionEvaluation"]:
        """Returns the previous AssetConditionEvaluation for a given asset key, if it exists."""
        previous_evaluation_state = self.get_previous_evaluation_state(asset_key)
        return previous_evaluation_state.previous_evaluation if previous_evaluation_state else None

    def with_updates(
        self,
        evaluation_id: int,
        evaluation_timestamp: float,
        newly_observe_requested_asset_keys: Sequence[AssetKey],
        evaluation_state: Sequence["AssetConditionEvaluationState"],
    ) -> "AssetDaemonCursor":
        return dataclasses.replace(
            self,
            evaluation_id=evaluation_id,
            previous_evaluation_state=evaluation_state,
            last_observe_request_timestamp_by_asset_key={
                **self.last_observe_request_timestamp_by_asset_key,
                **{
                    asset_key: evaluation_timestamp
                    for asset_key in newly_observe_requested_asset_keys
                },
            },
        )

    def __hash__(self) -> int:
        return hash(id(self))


# BACKCOMPAT


def get_backcompat_asset_condition_evaluation_state(
    latest_evaluation: "AssetConditionEvaluation",
    latest_storage_id: Optional[int],
    latest_timestamp: Optional[float],
    handled_root_subset: Optional[AssetSubset],
) -> "AssetConditionEvaluationState":
    """Generates an AssetDaemonCursor from information available on the old cursor format."""
    from dagster._core.definitions.asset_condition.asset_condition import (
        AssetConditionEvaluationState,
        RuleCondition,
    )
    from dagster._core.definitions.auto_materialize_rule import MaterializeOnMissingRule

    return AssetConditionEvaluationState(
        previous_evaluation=latest_evaluation,
        previous_tick_evaluation_timestamp=latest_timestamp,
        max_storage_id=latest_storage_id,
        # the only information we need to preserve from the previous cursor is the handled subset
        extra_state_by_unique_id={
            RuleCondition(MaterializeOnMissingRule()).unique_id: handled_root_subset,
        }
        if handled_root_subset and handled_root_subset.size > 0
        else {},
    )


def backcompat_deserialize_asset_daemon_cursor_str(
    cursor_str: str, asset_graph: Optional[AssetGraph], default_evaluation_id: int
) -> AssetDaemonCursor:
    """This serves as a backcompat layer for deserializing the old cursor format. Some information
    is impossible to fully recover, this will recover enough to continue operating as normal.
    """
    from .asset_condition.asset_condition import AssetConditionEvaluation, AssetConditionSnapshot
    from .auto_materialize_rule_evaluation import (
        deserialize_auto_materialize_asset_evaluation_to_asset_condition_evaluation_with_run_ids,
    )

    data = json.loads(cursor_str)

    if isinstance(data, list):
        evaluation_id = data[0] if isinstance(data[0], int) else default_evaluation_id
        return AssetDaemonCursor.empty(evaluation_id)
    elif not isinstance(data, dict):
        return AssetDaemonCursor.empty(default_evaluation_id)
    elif asset_graph is None:
        return AssetDaemonCursor.empty(data.get("evaluation_id", default_evaluation_id))

    serialized_last_observe_request_timestamp_by_asset_key = data.get(
        "last_observe_request_timestamp_by_asset_key", {}
    )
    last_observe_request_timestamp_by_asset_key = {
        AssetKey.from_user_string(key_str): timestamp
        for key_str, timestamp in serialized_last_observe_request_timestamp_by_asset_key.items()
    }

    partition_subsets_by_asset_key = {}
    for key_str, serialized_str in data.get("handled_root_partitions_by_asset_key", {}).items():
        asset_key = AssetKey.from_user_string(key_str)
        partitions_def = asset_graph.get_partitions_def(asset_key) if asset_graph else None
        if not partitions_def:
            continue
        try:
            partition_subsets_by_asset_key[asset_key] = partitions_def.deserialize_subset(
                serialized_str
            )
        except:
            continue

    handled_root_asset_graph_subset = AssetGraphSubset(
        non_partitioned_asset_keys={
            AssetKey.from_user_string(key_str)
            for key_str in data.get("handled_root_asset_keys", set())
        },
        partitions_subsets_by_asset_key=partition_subsets_by_asset_key,
    )

    serialized_latest_evaluation_by_asset_key = data.get("latest_evaluation_by_asset_key", {})
    latest_evaluation_by_asset_key = {}
    for key_str, serialized_evaluation in serialized_latest_evaluation_by_asset_key.items():
        key = AssetKey.from_user_string(key_str)
        partitions_def = asset_graph.get_partitions_def(key) if asset_graph else None

        evaluation = deserialize_auto_materialize_asset_evaluation_to_asset_condition_evaluation_with_run_ids(
            serialized_evaluation, partitions_def
        ).evaluation

        latest_evaluation_by_asset_key[key] = evaluation

    previous_evaluation_state = []
    cursor_keys = (
        asset_graph.materializable_asset_keys
        if asset_graph
        else latest_evaluation_by_asset_key.keys()
    )
    for asset_key in cursor_keys:
        latest_evaluation_result = latest_evaluation_by_asset_key.get(asset_key)
        # create a placeholder evaluation result if we don't have one
        if not latest_evaluation_result:
            partitions_def = asset_graph.get_partitions_def(asset_key) if asset_graph else None
            latest_evaluation_result = AssetConditionEvaluation(
                condition_snapshot=AssetConditionSnapshot("", "", ""),
                true_subset=AssetSubset.empty(asset_key, partitions_def),
                candidate_subset=AssetSubset.empty(asset_key, partitions_def),
                start_timestamp=None,
                end_timestamp=None,
                subsets_with_metadata=[],
                child_evaluations=[],
            )
        backcompat_evaluation_state = get_backcompat_asset_condition_evaluation_state(
            latest_evaluation_result,
            data.get("latest_storage_id"),
            data.get("latest_evaluation_timestamp"),
            handled_root_asset_graph_subset.get_asset_subset(asset_key, asset_graph)
            if asset_graph
            else None,
        )
        previous_evaluation_state.append(backcompat_evaluation_state)

    return AssetDaemonCursor(
        evaluation_id=data.get("evaluation_id") or default_evaluation_id,
        previous_evaluation_state=previous_evaluation_state,
        last_observe_request_timestamp_by_asset_key=last_observe_request_timestamp_by_asset_key,
    )


@whitelist_for_serdes
class LegacyAssetDaemonCursorWrapper(NamedTuple):
    """Wrapper class for the legacy AssetDaemonCursor object, which is not a serializable NamedTuple."""

    serialized_cursor: str

    def get_asset_daemon_cursor(self, asset_graph: Optional[AssetGraph]) -> AssetDaemonCursor:
        return backcompat_deserialize_asset_daemon_cursor_str(
            self.serialized_cursor, asset_graph, 0
        )
