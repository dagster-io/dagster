import datetime
import operator
from typing import (
    TYPE_CHECKING,
    AbstractSet,
    Callable,
    NamedTuple,
    Optional,
    Union,
    cast,
)

import dagster._check as check
from dagster._core.definitions.events import AssetKey, AssetKeyPartitionKey
from dagster._core.definitions.partition import (
    AllPartitionsSubset,
    PartitionsDefinition,
    PartitionsSubset,
)
from dagster._serdes.serdes import NamedTupleSerializer, whitelist_for_serdes

if TYPE_CHECKING:
    from dagster._core.instance import DynamicPartitionsStore


class AssetSubsetSerializer(NamedTupleSerializer):
    """Ensures that the inner PartitionsSubset is converted to a serializable form if necessary."""

    def before_pack(self, value: "AssetSubset") -> "AssetSubset":
        if value.is_partitioned:
            return value._replace(value=value.subset_value.to_serializable_subset())
        return value


@whitelist_for_serdes(serializer=AssetSubsetSerializer)
class AssetSubset(NamedTuple):
    """Represents a set of AssetKeyPartitionKeys for a given AssetKey. For partitioned assets, this
    class uses a PartitionsSubset to represent the set of partitions, enabling lazy evaluation of the
    underlying partition keys. For unpartitioned assets, this class uses a bool to represent whether
    the asset is present or not.
    """

    asset_key: AssetKey
    value: Union[bool, PartitionsSubset]

    @property
    def is_partitioned(self) -> bool:
        return not isinstance(self.value, bool)

    @property
    def bool_value(self) -> bool:
        check.invariant(isinstance(self.value, bool))
        return cast(bool, self.value)

    @property
    def subset_value(self) -> PartitionsSubset:
        check.invariant(isinstance(self.value, PartitionsSubset))
        return cast(PartitionsSubset, self.value)

    @property
    def asset_partitions(self) -> AbstractSet[AssetKeyPartitionKey]:
        if not self.is_partitioned:
            return {AssetKeyPartitionKey(self.asset_key)} if self.bool_value else set()
        else:
            return {
                AssetKeyPartitionKey(self.asset_key, partition_key)
                for partition_key in self.subset_value.get_partition_keys()
            }

    @property
    def size(self) -> int:
        if not self.is_partitioned:
            return int(self.bool_value)
        else:
            return len(self.subset_value)

    @staticmethod
    def all(
        asset_key: AssetKey,
        partitions_def: Optional[PartitionsDefinition],
        dynamic_partitions_store: Optional["DynamicPartitionsStore"] = None,
        current_time: Optional[datetime.datetime] = None,
    ) -> "AssetSubset":
        if partitions_def is None:
            return AssetSubset(asset_key=asset_key, value=True)
        else:
            if dynamic_partitions_store is None or current_time is None:
                check.failed(
                    "Must provide dynamic_partitions_store and current_time for partitioned assets."
                )
            return AssetSubset(
                asset_key=asset_key,
                value=AllPartitionsSubset(partitions_def, dynamic_partitions_store, current_time),
            )

    @staticmethod
    def empty(asset_key: AssetKey, partitions_def: Optional[PartitionsDefinition]) -> "AssetSubset":
        if partitions_def is None:
            return AssetSubset(asset_key=asset_key, value=False)
        else:
            return AssetSubset(asset_key=asset_key, value=partitions_def.empty_subset())

    @staticmethod
    def from_asset_partitions_set(
        asset_key: AssetKey,
        partitions_def: Optional[PartitionsDefinition],
        asset_partitions_set: AbstractSet[AssetKeyPartitionKey],
    ) -> "AssetSubset":
        if partitions_def is None:
            return AssetSubset(asset_key=asset_key, value=bool(asset_partitions_set))
        else:
            return AssetSubset(
                asset_key=asset_key,
                value=partitions_def.subset_with_partition_keys(
                    {
                        ap.partition_key
                        for ap in asset_partitions_set
                        if ap.partition_key is not None
                    }
                ),
            )

    def inverse(
        self,
        partitions_def: Optional[PartitionsDefinition],
        current_time: Optional[datetime.datetime] = None,
        dynamic_partitions_store: Optional["DynamicPartitionsStore"] = None,
    ) -> "AssetSubset":
        if partitions_def is None:
            return self._replace(value=not self.bool_value)
        else:
            value = partitions_def.subset_with_partition_keys(
                self.subset_value.get_partition_keys_not_in_subset(
                    partitions_def,
                    current_time=current_time,
                    dynamic_partitions_store=dynamic_partitions_store,
                )
            )
            return self._replace(value=value)

    def _oper(self, other: "AssetSubset", oper: Callable) -> "AssetSubset":
        value = oper(self.value, other.value)
        return self._replace(value=value)

    def __sub__(self, other: "AssetSubset") -> "AssetSubset":
        if not self.is_partitioned:
            return self._replace(value=self.bool_value and not other.bool_value)
        return self._oper(other, operator.sub)

    def __and__(self, other: "AssetSubset") -> "AssetSubset":
        return self._oper(other, operator.and_)

    def __or__(self, other: "AssetSubset") -> "AssetSubset":
        return self._oper(other, operator.or_)

    def __contains__(self, item: AssetKeyPartitionKey) -> bool:
        if not self.is_partitioned:
            return (
                item.asset_key == self.asset_key and item.partition_key is None and self.bool_value
            )
        else:
            return item.asset_key == self.asset_key and item.partition_key in self.subset_value
