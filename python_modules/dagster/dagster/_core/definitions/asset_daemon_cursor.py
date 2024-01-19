import base64
import datetime
import json
import zlib
from typing import (
    TYPE_CHECKING,
    AbstractSet,
    Mapping,
    NamedTuple,
    Optional,
    Sequence,
    Type,
    TypeVar,
)

import dagster._check as check
from dagster._core.definitions.events import AssetKey
from dagster._core.definitions.time_window_partitions import (
    TimeWindowPartitionsDefinition,
    TimeWindowPartitionsSubset,
)
from dagster._serdes.serdes import (
    PackableValue,
    deserialize_value,
    serialize_value,
    whitelist_for_serdes,
)

from .asset_graph import AssetGraph
from .asset_subset import AssetSubset
from .partition import PartitionsDefinition, PartitionsSubset

if TYPE_CHECKING:
    from .asset_condition import AssetCondition, AssetConditionEvaluation, AssetConditionSnapshot
    from .asset_condition_evaluation_context import AssetConditionEvaluationContext

ExtrasDict = Mapping[str, PackableValue]

T = TypeVar("T")


def _get_placeholder_missing_condition() -> "AssetCondition":
    """Temporary hard-coding of the hash of the "materialize on missing" condition. This will
    no longer be necessary once we start serializing the AssetDaemonCursor.
    """
    from .asset_condition import RuleCondition
    from .auto_materialize_rule import MaterializeOnMissingRule

    return RuleCondition(MaterializeOnMissingRule())


_PLACEHOLDER_HANDLED_SUBSET_KEY = "handled_subset"


class AssetConditionCursorExtras(NamedTuple):
    """Class to represent additional unstructured information that may be tracked by a particular
    asset condition.
    """

    condition_snapshot: "AssetConditionSnapshot"
    extras: ExtrasDict


class AssetConditionCursor(NamedTuple):
    """Convenience class to represent the state of an individual asset being handled by the daemon.
    In the future, this will be serialized as part of the cursor.
    """

    asset_key: AssetKey
    previous_evaluation: Optional["AssetConditionEvaluation"]
    previous_max_storage_id: Optional[int]
    previous_evaluation_timestamp: Optional[float]

    extras: Sequence[AssetConditionCursorExtras]

    @staticmethod
    def empty(asset_key: AssetKey) -> "AssetConditionCursor":
        return AssetConditionCursor(
            asset_key=asset_key,
            previous_evaluation=None,
            previous_max_storage_id=None,
            previous_evaluation_timestamp=None,
            extras=[],
        )

    def get_extras_value(
        self, condition: "AssetCondition", key: str, as_type: Type[T]
    ) -> Optional[T]:
        """Returns a value from the extras dict for the given condition, if it exists and is of the
        expected type. Otherwise, returns None.
        """
        for condition_extras in self.extras:
            if condition_extras.condition_snapshot == condition.snapshot:
                extras_value = condition_extras.extras.get(key)
                if isinstance(extras_value, as_type):
                    return extras_value
                return None
        return None

    def get_previous_requested_or_discarded_subset(
        self, condition: "AssetCondition", partitions_def: Optional[PartitionsDefinition]
    ) -> AssetSubset:
        if not self.previous_evaluation:
            return AssetSubset.empty(self.asset_key, partitions_def)
        return self.previous_evaluation.get_requested_or_discarded_subset(condition)

    @property
    def handled_subset(self) -> Optional[AssetSubset]:
        return self.get_extras_value(
            condition=_get_placeholder_missing_condition(),
            key=_PLACEHOLDER_HANDLED_SUBSET_KEY,
            as_type=AssetSubset,
        )

    def with_updates(
        self, context: "AssetConditionEvaluationContext", evaluation: "AssetConditionEvaluation"
    ) -> "AssetConditionCursor":
        newly_materialized_requested_or_discarded_subset = (
            context.materialized_since_previous_tick_subset
            | evaluation.get_requested_or_discarded_subset(context.condition)
        )

        handled_subset = (
            self.handled_subset or context.empty_subset()
        ) | newly_materialized_requested_or_discarded_subset

        # for now, hard-code the materialized_requested_or_discarded_subset location
        return self._replace(
            previous_evaluation=evaluation,
            extras=[
                AssetConditionCursorExtras(
                    condition_snapshot=_get_placeholder_missing_condition().snapshot,
                    extras={_PLACEHOLDER_HANDLED_SUBSET_KEY: handled_subset},
                )
            ],
        )


class AssetDaemonCursor(NamedTuple):
    """State that's saved between reconciliation evaluations.

    Attributes:
        latest_storage_id:
            The latest observed storage ID across all assets. Useful for finding out what has
            happened since the last tick.
        handled_root_asset_keys:
            Every entry is a non-partitioned asset with no parents that has been requested by this
            sensor, discarded by this sensor, or has been materialized (even if not by this sensor).
        handled_root_partitions_by_asset_key:
            Every key is a partitioned root asset. Every value is the set of that asset's partitions
            that have been requested by this sensor, discarded by this sensor,
            or have been materialized (even if not by this sensor).
        last_observe_request_timestamp_by_asset_key:
            Every key is an observable source asset that has been auto-observed. The value is the
            timestamp of the tick that requested the observation.
    """

    latest_storage_id: Optional[int]
    handled_root_asset_keys: AbstractSet[AssetKey]
    handled_root_partitions_by_asset_key: Mapping[AssetKey, PartitionsSubset]
    evaluation_id: int
    last_observe_request_timestamp_by_asset_key: Mapping[AssetKey, float]
    latest_evaluation_by_asset_key: Mapping[AssetKey, "AssetConditionEvaluation"]
    latest_evaluation_timestamp: Optional[float]

    def was_previously_handled(self, asset_key: AssetKey) -> bool:
        return asset_key in self.handled_root_asset_keys

    def asset_cursor_for_key(
        self, asset_key: AssetKey, asset_graph: AssetGraph
    ) -> AssetConditionCursor:
        partitions_def = asset_graph.get_partitions_def(asset_key)
        handled_partitions_subset = self.handled_root_partitions_by_asset_key.get(asset_key)
        if handled_partitions_subset is not None:
            handled_subset = AssetSubset(asset_key=asset_key, value=handled_partitions_subset)
        elif asset_key in self.handled_root_asset_keys:
            handled_subset = AssetSubset(asset_key=asset_key, value=True)
        else:
            handled_subset = AssetSubset.empty(asset_key, partitions_def)

        previous_evaluation = self.latest_evaluation_by_asset_key.get(asset_key)
        return AssetConditionCursor(
            asset_key=asset_key,
            previous_evaluation=previous_evaluation,
            previous_max_storage_id=self.latest_storage_id,
            previous_evaluation_timestamp=self.latest_evaluation_timestamp,
            extras=[
                AssetConditionCursorExtras(
                    condition_snapshot=_get_placeholder_missing_condition().snapshot,
                    extras={"handled_subset": handled_subset},
                )
            ],
        )

    def with_updates(
        self,
        latest_storage_id: Optional[int],
        evaluation_id: int,
        newly_observe_requested_asset_keys: Sequence[AssetKey],
        observe_request_timestamp: float,
        evaluations: Sequence["AssetConditionEvaluation"],
        evaluation_time: datetime.datetime,
        asset_cursors: Sequence[AssetConditionCursor],
    ) -> "AssetDaemonCursor":
        """Returns a cursor that represents this cursor plus the updates that have happened within the
        tick.
        """
        result_last_observe_request_timestamp_by_asset_key = {
            **self.last_observe_request_timestamp_by_asset_key
        }
        for asset_key in newly_observe_requested_asset_keys:
            result_last_observe_request_timestamp_by_asset_key[
                asset_key
            ] = observe_request_timestamp

        if latest_storage_id and self.latest_storage_id:
            check.invariant(
                latest_storage_id >= self.latest_storage_id,
                "Latest storage ID should be >= previous latest storage ID",
            )

        latest_evaluation_by_asset_key = {
            evaluation.asset_key: evaluation for evaluation in evaluations
        }

        return AssetDaemonCursor(
            latest_storage_id=latest_storage_id or self.latest_storage_id,
            handled_root_asset_keys={
                cursor.asset_key
                for cursor in asset_cursors
                if cursor.handled_subset is not None
                and not cursor.handled_subset.is_partitioned
                and cursor.handled_subset.bool_value
            },
            handled_root_partitions_by_asset_key={
                cursor.asset_key: cursor.handled_subset.subset_value
                for cursor in asset_cursors
                if cursor.handled_subset is not None and cursor.handled_subset.is_partitioned
            },
            evaluation_id=evaluation_id,
            last_observe_request_timestamp_by_asset_key=result_last_observe_request_timestamp_by_asset_key,
            latest_evaluation_by_asset_key=latest_evaluation_by_asset_key,
            latest_evaluation_timestamp=evaluation_time.timestamp(),
        )

    @classmethod
    def empty(cls) -> "AssetDaemonCursor":
        return AssetDaemonCursor(
            latest_storage_id=None,
            handled_root_partitions_by_asset_key={},
            handled_root_asset_keys=set(),
            evaluation_id=0,
            last_observe_request_timestamp_by_asset_key={},
            latest_evaluation_by_asset_key={},
            latest_evaluation_timestamp=None,
        )

    @classmethod
    def from_serialized(cls, cursor: str, asset_graph: AssetGraph) -> "AssetDaemonCursor":
        from .asset_condition import AssetConditionEvaluationWithRunIds

        data = json.loads(cursor)

        if isinstance(data, list):  # backcompat
            check.invariant(len(data) in [3, 4], "Invalid serialized cursor")
            (
                latest_storage_id,
                serialized_handled_root_asset_keys,
                serialized_handled_root_partitions_by_asset_key,
            ) = data[:3]

            evaluation_id = data[3] if len(data) == 4 else 0
            serialized_last_observe_request_timestamp_by_asset_key = {}
            serialized_latest_evaluation_by_asset_key = {}
            latest_evaluation_timestamp = 0
        else:
            latest_storage_id = data["latest_storage_id"]
            serialized_handled_root_asset_keys = data["handled_root_asset_keys"]
            serialized_handled_root_partitions_by_asset_key = data[
                "handled_root_partitions_by_asset_key"
            ]
            evaluation_id = data["evaluation_id"]
            serialized_last_observe_request_timestamp_by_asset_key = data.get(
                "last_observe_request_timestamp_by_asset_key", {}
            )
            serialized_latest_evaluation_by_asset_key = data.get(
                "latest_evaluation_by_asset_key", {}
            )
            latest_evaluation_timestamp = data.get("latest_evaluation_timestamp", 0)

        handled_root_partitions_by_asset_key = {}
        for (
            key_str,
            serialized_subset,
        ) in serialized_handled_root_partitions_by_asset_key.items():
            key = AssetKey.from_user_string(key_str)
            if key not in asset_graph.materializable_asset_keys:
                continue

            partitions_def = asset_graph.get_partitions_def(key)
            if partitions_def is None:
                continue

            try:
                # in the case that the partitions def has changed, we may not be able to deserialize
                # the corresponding subset. in this case, we just use an empty subset
                subset = partitions_def.deserialize_subset(serialized_subset)
                # this covers the case in which the start date has changed for a time-partitioned
                # asset. in reality, we should be using the can_deserialize method but because we
                # are not storing the serializable unique id, we can't do that.
                if (
                    isinstance(subset, TimeWindowPartitionsSubset)
                    and isinstance(partitions_def, TimeWindowPartitionsDefinition)
                    and any(
                        time_window.start < partitions_def.start
                        for time_window in subset.included_time_windows
                    )
                ):
                    subset = partitions_def.empty_subset()
            except:
                subset = partitions_def.empty_subset()
            handled_root_partitions_by_asset_key[key] = subset

        latest_evaluation_by_asset_key = {}
        for key_str, serialized_evaluation in serialized_latest_evaluation_by_asset_key.items():
            key = AssetKey.from_user_string(key_str)
            deserialized_evaluation = deserialize_value(serialized_evaluation)
            if isinstance(deserialized_evaluation, AssetConditionEvaluationWithRunIds):
                evaluation = deserialized_evaluation.evaluation
            else:
                evaluation = deserialized_evaluation
            latest_evaluation_by_asset_key[key] = evaluation

        return cls(
            latest_storage_id=latest_storage_id,
            handled_root_asset_keys={
                AssetKey.from_user_string(key_str) for key_str in serialized_handled_root_asset_keys
            },
            handled_root_partitions_by_asset_key=handled_root_partitions_by_asset_key,
            evaluation_id=evaluation_id,
            last_observe_request_timestamp_by_asset_key={
                AssetKey.from_user_string(key_str): timestamp
                for key_str, timestamp in serialized_last_observe_request_timestamp_by_asset_key.items()
            },
            latest_evaluation_by_asset_key=latest_evaluation_by_asset_key,
            latest_evaluation_timestamp=latest_evaluation_timestamp,
        )

    @classmethod
    def get_evaluation_id_from_serialized(cls, cursor: str) -> Optional[int]:
        data = json.loads(cursor)
        if isinstance(data, list):  # backcompat
            check.invariant(len(data) in [3, 4], "Invalid serialized cursor")
            return data[3] if len(data) == 4 else None
        else:
            return data["evaluation_id"]

    def serialize(self) -> str:
        serializable_handled_root_partitions_by_asset_key = {
            key.to_user_string(): subset.serialize()
            for key, subset in self.handled_root_partitions_by_asset_key.items()
        }
        serialized = json.dumps(
            {
                "latest_storage_id": self.latest_storage_id,
                "handled_root_asset_keys": [
                    key.to_user_string() for key in self.handled_root_asset_keys
                ],
                "handled_root_partitions_by_asset_key": (
                    serializable_handled_root_partitions_by_asset_key
                ),
                "evaluation_id": self.evaluation_id,
                "last_observe_request_timestamp_by_asset_key": {
                    key.to_user_string(): timestamp
                    for key, timestamp in self.last_observe_request_timestamp_by_asset_key.items()
                },
                "latest_evaluation_by_asset_key": {
                    key.to_user_string(): serialize_value(evaluation)
                    for key, evaluation in self.latest_evaluation_by_asset_key.items()
                },
                "latest_evaluation_timestamp": self.latest_evaluation_timestamp,
            }
        )
        return serialized


@whitelist_for_serdes
class LegacyAssetDaemonCursorWrapper(NamedTuple):
    """Wrapper class for the legacy AssetDaemonCursor object, which is not a serializable NamedTuple."""

    serialized_cursor: str

    def get_asset_daemon_cursor(self, asset_graph: AssetGraph) -> AssetDaemonCursor:
        return AssetDaemonCursor.from_serialized(self.serialized_cursor, asset_graph)

    @staticmethod
    def from_compressed(compressed: str) -> "LegacyAssetDaemonCursorWrapper":
        """This method takes a b64 encoded, zlib compressed string and returns the original
        BackcompatAssetDaemonEvaluationInfo object.
        """
        decoded_bytes = base64.b64decode(compressed)
        decompressed_bytes = zlib.decompress(decoded_bytes)
        decoded_str = decompressed_bytes.decode("utf-8")
        return deserialize_value(decoded_str, LegacyAssetDaemonCursorWrapper)

    def to_compressed(self) -> str:
        """This method compresses the serialized cursor and returns a b64 encoded string to be
        stored as a string value.
        """
        serialized_bytes = serialize_value(self).encode("utf-8")
        compressed_bytes = zlib.compress(serialized_bytes)
        encoded_str = base64.b64encode(compressed_bytes)
        return encoded_str.decode("utf-8")
