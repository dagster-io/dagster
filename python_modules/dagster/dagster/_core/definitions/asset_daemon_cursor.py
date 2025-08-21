import dataclasses
import json
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from functools import cached_property
from typing import TYPE_CHECKING, NamedTuple, Optional

from dagster_shared.serdes.serdes import (
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

from dagster._core.definitions.asset_key import EntityKey, T_EntityKey
from dagster._core.definitions.assets.graph.base_asset_graph import BaseAssetGraph
from dagster._core.definitions.events import AssetKey

if TYPE_CHECKING:
    from dagster._core.definitions.declarative_automation.serialized_objects import (
        AutomationConditionCursor,
        AutomationConditionEvaluationState,
        AutomationConditionNodeSnapshot,
    )


@whitelist_for_serdes(storage_name="AssetConditionCursorExtras")
class AutomationConditionCursorExtras(NamedTuple):
    """Represents additional state that may be optionally saved by an AutomationCondition between
    evaluations.
    """

    condition_snapshot: "AutomationConditionNodeSnapshot"
    extras: Mapping[str, PackableValue]


class ObserveRequestTimestampSerializer(FieldSerializer):
    def pack(
        self,
        mapping: Mapping[str, float],
        whitelist_map: WhitelistMap,
        descent_path: str,
    ) -> JsonSerializableValue:
        return pack_value(SerializableNonScalarKeyMapping(mapping), whitelist_map, descent_path)

    def unpack(  # pyright: ignore[reportIncompatibleMethodOverride]
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

    Args:
        evaluation_id (int): The ID of the evaluation that produced this cursor.
        previous_evaluation_state (Sequence[AutomationConditionEvaluationState]): (DEPRECATED) The
            evaluation info recorded for each asset on the previous tick.
        previous_cursors (Sequence[AutomationConditionCursor]): The cursor objects for each asset
            recorded on the previous tick.
    """

    evaluation_id: int
    last_observe_request_timestamp_by_asset_key: Mapping[AssetKey, float]

    previous_evaluation_state: Optional[Sequence["AutomationConditionEvaluationState"]]
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
    def previous_condition_cursors_by_key(
        self,
    ) -> Mapping[EntityKey, "AutomationConditionCursor"]:
        """Efficient lookup of previous cursor by asset key."""
        from dagster._core.definitions.declarative_automation.serialized_objects import (
            AutomationConditionCursor,
        )

        if self.previous_condition_cursors is None:
            # automatically convert AutomationConditionEvaluationState objects to AutomationConditionCursor
            return {
                evaluation_state.asset_key: AutomationConditionCursor.backcompat_from_evaluation_state(
                    evaluation_state
                )
                for evaluation_state in self.previous_evaluation_state or []
            }
        else:
            return {cursor.key: cursor for cursor in self.previous_condition_cursors}

    def get_previous_condition_cursor(
        self, key: T_EntityKey
    ) -> Optional["AutomationConditionCursor[T_EntityKey]"]:
        """Returns the AutomationConditionCursor associated with the given asset key. If no stored
        cursor exists, returns an empty cursor.
        """
        return self.previous_condition_cursors_by_key.get(key)

    def with_updates(
        self,
        evaluation_id: int,
        evaluation_timestamp: float,
        newly_observe_requested_asset_keys: Sequence[AssetKey],
        condition_cursors: Sequence["AutomationConditionCursor"],
        asset_graph: BaseAssetGraph,
    ) -> "AssetDaemonCursor":
        # we carry forward the last cursor of any asset that is either not in the current
        # asset graph, or is not materializable, as an asset with a condition can enter
        # this state if a code location is temporarily unavailable.
        #
        # this means that we will explicitly not carry forward the cursor for an asset that
        # is currently materializable, meaning if an asset has its automation condition
        # removed explicitly, its cursor will be deleted.
        unpropagated_keys = {
            k for k in asset_graph.get_all_asset_keys() if asset_graph.get(k).is_materializable
        }
        new_condition_cursors = {
            k: v
            for k, v in self.previous_condition_cursors_by_key.items()
            if k not in unpropagated_keys
        }
        # populate the real new cursors
        for cursor in condition_cursors:
            new_condition_cursors[cursor.key] = cursor

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
