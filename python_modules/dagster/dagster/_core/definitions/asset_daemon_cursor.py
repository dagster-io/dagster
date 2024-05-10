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

from .base_asset_graph import BaseAssetGraph

if TYPE_CHECKING:
    from .declarative_scheduling.serialized_objects import (
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


def backcompat_deserialize_asset_daemon_cursor_str(
    cursor_str: str, asset_graph: Optional[BaseAssetGraph], default_evaluation_id: int
) -> AssetDaemonCursor:
    """This serves as a backcompat layer for deserializing the old cursor format. Will only recover
    the previous evaluation id.
    """
    data = json.loads(cursor_str)

    if isinstance(data, list):
        evaluation_id = data[0] if isinstance(data[0], int) else default_evaluation_id
        return AssetDaemonCursor.empty(evaluation_id)
    elif not isinstance(data, dict):
        return AssetDaemonCursor.empty(default_evaluation_id)
    elif asset_graph is None:
        return AssetDaemonCursor.empty(data.get("evaluation_id", default_evaluation_id))

    return AssetDaemonCursor(
        evaluation_id=data.get("evaluation_id") or default_evaluation_id,
        previous_evaluation_state=[],
        last_observe_request_timestamp_by_asset_key={},
    )


@whitelist_for_serdes
class LegacyAssetDaemonCursorWrapper(NamedTuple):
    """Wrapper class for the legacy AssetDaemonCursor object, which is not a serializable NamedTuple."""

    serialized_cursor: str

    def get_asset_daemon_cursor(self, asset_graph: Optional[BaseAssetGraph]) -> AssetDaemonCursor:
        return backcompat_deserialize_asset_daemon_cursor_str(
            self.serialized_cursor, asset_graph, 0
        )
