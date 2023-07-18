import datetime
import json
from typing import (
    TYPE_CHECKING,
    AbstractSet,
    Iterable,
    Mapping,
    NamedTuple,
    Optional,
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
    """State that's saved between asset daemon evaluations.

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

    def with_updates(
        self,
        asset_graph: AssetGraph,
        new_latest_storage_id: Optional[int],
        newly_observed_source_assets: AbstractSet[AssetKey],
        newly_observed_source_timestamp: float,
        newly_handled_asset_partitions: AbstractSet[AssetKeyPartitionKey],
        conditions_by_asset_partition_by_asset_key: Mapping[
            AssetKey, Mapping[AssetKeyPartitionKey, AbstractSet[AutoMaterializeCondition]]
        ],
    ) -> "AssetDaemonCursor":
        root_asset_keys = asset_graph.root_asset_keys
        # Create a single dictionary for all the newly-handled asset partitions
        handled_root_asset_partitions_by_asset_key = {
            asset_key: {
                asset_partition
                for asset_partition, conditions in conditions_by_asset_partition.items()
                if AutoMaterializeDecisionType.from_conditions(conditions)
                in (AutoMaterializeDecisionType.MATERIALIZE, AutoMaterializeDecisionType.DISCARD)
            }
            for asset_key, conditions_by_asset_partition in conditions_by_asset_partition_by_asset_key.items()
            if asset_key in root_asset_keys
        }
        for asset_partition in newly_handled_asset_partitions:
            handled_root_asset_partitions_by_asset_key.setdefault(
                asset_partition.asset_key, set()
            ).add(asset_partition)

        # update the relevant fields depending on if the asset key is partitioned or not
        new_handled_root_asset_keys = set(self.handled_root_asset_keys)
        new_handled_root_asset_partitions_by_asset_key = {}
        handled_conditions = (
            AutoMaterializeDecisionType.MATERIALIZE,
            AutoMaterializeDecisionType.DISCARD,
        )
        for asset_key in root_asset_keys:
            if asset_graph.is_partitioned(asset_key):
                prior_materialized_partitions = self.handled_root_partitions_by_asset_key.get(
                    asset_key
                )
                if prior_materialized_partitions is None:
                    prior_materialized_partitions = cast(
                        PartitionsDefinition, asset_graph.get_partitions_def(asset_key)
                    ).empty_subset()
                new_handled_root_asset_partitions_by_asset_key[
                    asset_key
                ] = prior_materialized_partitions.with_partition_keys(
                    {
                        check.not_none(ap.partition_key)
                        for ap in handled_root_asset_partitions_by_asset_key.get(asset_key, set())
                    }
                )
            else:
                asset_partition = AssetKeyPartitionKey(asset_key)
                if asset_partition in newly_handled_asset_partitions or (
                    asset_key in conditions_by_asset_partition_by_asset_key
                    and AutoMaterializeDecisionType.from_conditions(
                        conditions_by_asset_partition_by_asset_key[asset_key][asset_partition]
                    )
                    in handled_conditions
                ):
                    new_handled_root_asset_keys.add(asset_key)

        return self._replace(
            evaluation_id=self.evaluation_id + 1,
            latest_storage_id=new_latest_storage_id,
            handled_root_asset_keys=new_handled_root_asset_keys,
            handled_root_partitions_by_asset_key=new_handled_root_asset_partitions_by_asset_key,
            last_observe_request_timestamp_by_asset_key={
                **self.last_observe_request_timestamp_by_asset_key,
                **{
                    asset_key: newly_observed_source_timestamp
                    for asset_key in newly_observed_source_assets
                },
            },
        )
