import dataclasses
import json
from dataclasses import dataclass
from functools import cached_property
from typing import TYPE_CHECKING, Mapping, NamedTuple, Optional, Sequence

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
    from .declarative_automation.serialized_objects import (
        AssetConditionEvaluationState,
        AssetConditionSnapshot,
        AutomationConditionCursor,
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
# TODO: rename to scheduling cursor or something
# 2024-05-16 -- schrockn
class AssetDaemonCursor:
    """State that's stored between daemon evaluations.

    Attributes:
        evaluation_id (int): The ID of the evaluation that produced this cursor.
        previous_evaluation_state (Sequence[AssetConditionEvaluationState]): (DEPRECATED) The
            evaluation info recorded for each asset on the previous tick.
        previous_cursors (Sequence[AutomationConditionCursor]): The cursor objects for each asset
            recorded on the previous tick.
    """

    evaluation_id: int
    last_observe_request_timestamp_by_asset_key: Mapping[AssetKey, float]

    previous_evaluation_state: Optional[Sequence["AssetConditionEvaluationState"]]
    previous_condition_cursors: Optional[Sequence["AutomationConditionCursor"]] = None

    @staticmethod
    def empty(evaluation_id: int = 0) -> "AssetDaemonCursor":
        return AssetDaemonCursor(
            evaluation_id=evaluation_id,
            previous_evaluation_state=None,
            previous_condition_cursors=[],
            last_observe_request_timestamp_by_asset_key={},
        )

    @cached_property
    def previous_condition_cursors_by_key(self) -> Mapping[AssetKey, "AutomationConditionCursor"]:
        """Efficient lookup of previous cursor by asset key."""
        from dagster._core.definitions.declarative_automation.serialized_objects import (
            AutomationConditionCursor,
        )

        if self.previous_condition_cursors is None:
            # automatically convert AssetConditionEvaluationState objects to AutomationConditionCursor
            return {
                evaluation_state.asset_key: AutomationConditionCursor.backcompat_from_evaluation_state(
                    evaluation_state
                )
                for evaluation_state in self.previous_evaluation_state or []
            }
        else:
            return {cursor.asset_key: cursor for cursor in self.previous_condition_cursors}

    def get_previous_condition_cursor(
        self, asset_key: AssetKey
    ) -> Optional["AutomationConditionCursor"]:
        """Returns the AutomationConditionCursor associated with the given asset key. If no stored
        cursor exists, returns an empty cursor.
        """
        return self.previous_condition_cursors_by_key.get(asset_key)

    def with_updates(
        self,
        evaluation_id: int,
        evaluation_timestamp: float,
        newly_observe_requested_asset_keys: Sequence[AssetKey],
        condition_cursors: Sequence["AutomationConditionCursor"],
    ) -> "AssetDaemonCursor":
        # do not "forget" about values for non-evaluated assets
        new_condition_cursors = dict(self.previous_condition_cursors_by_key)
        for cursor in condition_cursors:
            new_condition_cursors[cursor.asset_key] = cursor

        return dataclasses.replace(
            self,
            evaluation_id=evaluation_id,
            previous_evaluation_state=[],
            previous_condition_cursors=list(new_condition_cursors.values()),
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
        previous_condition_cursors=[],
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
