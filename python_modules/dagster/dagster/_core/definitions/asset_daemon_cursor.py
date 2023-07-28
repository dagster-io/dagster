import datetime
import itertools
import json
from collections import defaultdict
from typing import (
    TYPE_CHECKING,
    AbstractSet,
    Dict,
    Iterable,
    Mapping,
    NamedTuple,
    Optional,
    Sequence,
    Set,
    cast,
)

import dagster._check as check
from dagster._core.definitions.events import AssetKey, AssetKeyPartitionKey

from .asset_graph import AssetGraph
from .auto_materialize_condition import (
    AutoMaterializeCondition,
    AutoMaterializeDecisionType,
)
from .partition import (
    PartitionsDefinition,
    PartitionsSubset,
)

if TYPE_CHECKING:
    from dagster._core.instance import DynamicPartitionsStore


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

    def was_previously_handled(self, asset_key: AssetKey) -> bool:
        return asset_key in self.handled_root_asset_keys

    def get_unhandled_partitions(
        self,
        asset_key: AssetKey,
        asset_graph,
        dynamic_partitions_store: "DynamicPartitionsStore",
        current_time: datetime.datetime,
    ) -> Iterable[str]:
        partitions_def = asset_graph.get_partitions_def(asset_key)

        handled_subset = self.handled_root_partitions_by_asset_key.get(
            asset_key, partitions_def.empty_subset()
        )

        return handled_subset.get_partition_keys_not_in_subset(
            current_time=current_time,
            dynamic_partitions_store=dynamic_partitions_store,
        )

    def with_updates(
        self,
        latest_storage_id: Optional[int],
        conditions_by_asset_partition: Mapping[
            AssetKeyPartitionKey, AbstractSet[AutoMaterializeCondition]
        ],
        newly_materialized_root_asset_keys: AbstractSet[AssetKey],
        newly_materialized_root_partitions_by_asset_key: Mapping[AssetKey, AbstractSet[str]],
        evaluation_id: int,
        asset_graph: AssetGraph,
        newly_observe_requested_asset_keys: Sequence[AssetKey],
        observe_request_timestamp: float,
    ) -> "AssetDaemonCursor":
        """Returns a cursor that represents this cursor plus the updates that have happened within the
        tick.
        """
        handled_root_partitions_by_asset_key: Dict[AssetKey, Set[str]] = defaultdict(set)
        handled_non_partitioned_root_assets: Set[AssetKey] = set()

        for asset_partition, conditions in conditions_by_asset_partition.items():
            if (
                # only consider root assets
                not asset_graph.has_non_source_parents(asset_partition.asset_key)
                # which were discarded or materialized
                and (
                    AutoMaterializeDecisionType.from_conditions(conditions)
                    in (
                        AutoMaterializeDecisionType.DISCARD,
                        AutoMaterializeDecisionType.MATERIALIZE,
                    )
                )
            ):
                if asset_partition.partition_key:
                    handled_root_partitions_by_asset_key[asset_partition.asset_key].add(
                        asset_partition.partition_key
                    )
                else:
                    handled_non_partitioned_root_assets.add(asset_partition.asset_key)

        result_handled_root_partitions_by_asset_key = {**self.handled_root_partitions_by_asset_key}
        for asset_key in set(newly_materialized_root_partitions_by_asset_key.keys()) | set(
            handled_root_partitions_by_asset_key.keys()
        ):
            prior_materialized_partitions = self.handled_root_partitions_by_asset_key.get(asset_key)
            if prior_materialized_partitions is None:
                prior_materialized_partitions = cast(
                    PartitionsDefinition, asset_graph.get_partitions_def(asset_key)
                ).empty_subset()

            result_handled_root_partitions_by_asset_key[
                asset_key
            ] = prior_materialized_partitions.with_partition_keys(
                itertools.chain(
                    newly_materialized_root_partitions_by_asset_key[asset_key],
                    handled_root_partitions_by_asset_key[asset_key],
                )
            )

        result_handled_root_asset_keys = (
            self.handled_root_asset_keys
            | newly_materialized_root_asset_keys
            | handled_non_partitioned_root_assets
        )

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

        return AssetDaemonCursor(
            latest_storage_id=latest_storage_id or self.latest_storage_id,
            handled_root_asset_keys=result_handled_root_asset_keys,
            handled_root_partitions_by_asset_key=result_handled_root_partitions_by_asset_key,
            evaluation_id=evaluation_id,
            last_observe_request_timestamp_by_asset_key=result_last_observe_request_timestamp_by_asset_key,
        )

    @classmethod
    def empty(cls) -> "AssetDaemonCursor":
        return AssetDaemonCursor(
            latest_storage_id=None,
            handled_root_partitions_by_asset_key={},
            handled_root_asset_keys=set(),
            evaluation_id=0,
            last_observe_request_timestamp_by_asset_key={},
        )

    @classmethod
    def from_serialized(cls, cursor: str, asset_graph: AssetGraph) -> "AssetDaemonCursor":
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
                handled_root_partitions_by_asset_key[key] = partitions_def.deserialize_subset(
                    serialized_subset
                )
            except:
                handled_root_partitions_by_asset_key[key] = partitions_def.empty_subset()
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
                "handled_root_partitions_by_asset_key": serializable_handled_root_partitions_by_asset_key,
                "evaluation_id": self.evaluation_id,
                "last_observe_request_timestamp_by_asset_key": {
                    key.to_user_string(): timestamp
                    for key, timestamp in self.last_observe_request_timestamp_by_asset_key.items()
                },
            }
        )
        return serialized
