import datetime
import operator
from typing import TYPE_CHECKING, AbstractSet, Any, Callable, NamedTuple, Optional, Union, cast

import dagster._check as check
from dagster._core.definitions.events import AssetKey, AssetKeyPartitionKey
from dagster._core.definitions.partition import (
    AllPartitionsSubset,
    PartitionsDefinition,
    PartitionsSubset,
)
from dagster._core.definitions.time_window_partitions import BaseTimeWindowPartitionsSubset
from dagster._model import InstanceOf
from dagster._serdes.serdes import NamedTupleSerializer, whitelist_for_serdes

if TYPE_CHECKING:
    from dagster._core.instance import DynamicPartitionsStore


class AssetSubsetSerializer(NamedTupleSerializer):
    """Ensures that the inner PartitionsSubset is converted to a serializable form if necessary."""

    def get_storage_name(self) -> str:
        # override this method so all ValidAssetSubsets are serialzied as AssetSubsets
        return "AssetSubset"

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

    # use InstanceOf to tell pydantic to just do an instanceof check instead of the default
    # costly NamedTuple validation and reconstruction
    asset_key: InstanceOf[AssetKey]
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

    @property
    def is_empty(self) -> bool:
        if self.is_partitioned:
            return self.subset_value.is_empty
        else:
            return not self.bool_value

    def is_compatible_with_partitions_def(
        self, partitions_def: Optional[PartitionsDefinition]
    ) -> bool:
        if self.is_partitioned:
            # for some PartitionSubset types, we have access to the underlying partitions
            # definitions, so we can ensure those are identical
            if isinstance(self.value, (BaseTimeWindowPartitionsSubset, AllPartitionsSubset)):
                return self.value.partitions_def == partitions_def
            else:
                return partitions_def is not None
        else:
            return partitions_def is None

    def _is_compatible_with_subset(self, other: "AssetSubset") -> bool:
        if isinstance(other.value, (BaseTimeWindowPartitionsSubset, AllPartitionsSubset)):
            return self.is_compatible_with_partitions_def(other.value.partitions_def)
        else:
            return self.is_partitioned == other.is_partitioned

    def as_valid(self, partitions_def: Optional[PartitionsDefinition]) -> "ValidAssetSubset":
        """Converts this AssetSubset to a ValidAssetSubset by returning a copy of this AssetSubset
        if it is compatible with the given PartitionsDefinition, otherwise returns an empty subset.
        """
        if self.is_compatible_with_partitions_def(partitions_def):
            return ValidAssetSubset(asset_key=self.asset_key, value=self.value)
        else:
            return ValidAssetSubset.empty(self.asset_key, partitions_def)

    @staticmethod
    def all(
        asset_key: AssetKey,
        partitions_def: Optional[PartitionsDefinition],
        dynamic_partitions_store: Optional["DynamicPartitionsStore"] = None,
        current_time: Optional[datetime.datetime] = None,
    ) -> "ValidAssetSubset":
        if partitions_def is None:
            return ValidAssetSubset(asset_key=asset_key, value=True)
        else:
            if dynamic_partitions_store is None or current_time is None:
                check.failed(
                    "Must provide dynamic_partitions_store and current_time for partitioned assets."
                )
            return ValidAssetSubset(
                asset_key=asset_key,
                value=AllPartitionsSubset(partitions_def, dynamic_partitions_store, current_time),
            )

    @staticmethod
    def empty(
        asset_key: AssetKey, partitions_def: Optional[PartitionsDefinition]
    ) -> "ValidAssetSubset":
        if partitions_def is None:
            return ValidAssetSubset(asset_key=asset_key, value=False)
        else:
            return ValidAssetSubset(asset_key=asset_key, value=partitions_def.empty_subset())

    @staticmethod
    def from_asset_partitions_set(
        asset_key: AssetKey,
        partitions_def: Optional[PartitionsDefinition],
        asset_partitions_set: AbstractSet[AssetKeyPartitionKey],
    ) -> "ValidAssetSubset":
        return (
            ValidAssetSubset.from_partition_keys(
                asset_key=asset_key,
                partitions_def=partitions_def,
                partition_keys={
                    ap.partition_key for ap in asset_partitions_set if ap.partition_key is not None
                },
            )
            if partitions_def
            else ValidAssetSubset(asset_key=asset_key, value=bool(asset_partitions_set))
        )

    @staticmethod
    def from_partition_keys(
        asset_key: AssetKey,
        partitions_def: PartitionsDefinition,
        partition_keys: AbstractSet[str],
    ) -> "ValidAssetSubset":
        return ValidAssetSubset(
            asset_key=asset_key, value=partitions_def.subset_with_partition_keys(partition_keys)
        )

    def __contains__(self, item: AssetKeyPartitionKey) -> bool:
        if not self.is_partitioned:
            return (
                item.asset_key == self.asset_key and item.partition_key is None and self.bool_value
            )
        else:
            return item.asset_key == self.asset_key and item.partition_key in self.subset_value

    def dict(self, **kwargs) -> dict:
        # Must be overridden as the Pydantic implementation errors when encountering NamedTuples
        # which have different fields than their __new__ method, which TimeWindowPartitionsSubset
        # unfortunately has.
        # This can likely be removed once TimeWindowPartitionsSubset is converted into a DagsterModel
        return {"asset_key": self.asset_key, "value": self.value}

    def __eq__(self, other: Any) -> bool:
        # Pydantic 2.x does not handle this comparison correctly for some reason, just override it
        if not isinstance(other, AssetSubset):
            return False
        return self.dict() == other.dict()


@whitelist_for_serdes(serializer=AssetSubsetSerializer)
class ValidAssetSubset(AssetSubset):
    """Represents an AssetSubset which is known to be compatible with the current PartitionsDefinition
    of the asset represents.

    This class serializes to a regular AssetSubset, as it is unknown if this value will still be
    valid in the process that deserializes it.

    All operations act over the set of AssetKeyPartitionKeys that the operands represent if the
    subsets are both ValidAssetSubsets. If the other operand cannot be coerced to a ValidAssetSubset,
    it is treated as an empty subset.
    """

    def inverse(
        self,
        partitions_def: Optional[PartitionsDefinition],
        current_time: Optional[datetime.datetime] = None,
        dynamic_partitions_store: Optional["DynamicPartitionsStore"] = None,
    ) -> "ValidAssetSubset":
        """Returns the AssetSubset containing all asset partitions which are not in this AssetSubset."""
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

    def _oper(self, other: "ValidAssetSubset", oper: Callable[..., Any]) -> "ValidAssetSubset":
        value = oper(self.value, other.value)
        return self._replace(value=value)

    def __sub__(self, other: AssetSubset) -> "ValidAssetSubset":
        """Returns an AssetSubset representing self.asset_partitions - other.asset_partitions."""
        valid_other = self.get_valid(other)
        if not self.is_partitioned:
            return self._replace(value=self.bool_value and not valid_other.bool_value)
        return self._oper(valid_other, operator.sub)

    def __and__(self, other: AssetSubset) -> "ValidAssetSubset":
        """Returns an AssetSubset representing self.asset_partitions & other.asset_partitions."""
        return self._oper(self.get_valid(other), operator.and_)

    def __or__(self, other: AssetSubset) -> "ValidAssetSubset":
        """Returns an AssetSubset representing self.asset_partitions | other.asset_partitions."""
        return self._oper(self.get_valid(other), operator.or_)

    def get_valid(self, other: AssetSubset) -> "ValidAssetSubset":
        """Creates a ValidAssetSubset from the given AssetSubset by returning a copy of the given
        AssetSubset if it is compatible with this AssetSubset, otherwise returns an empty subset.
        """
        if isinstance(other, ValidAssetSubset):
            return other
        elif self._is_compatible_with_subset(other):
            return ValidAssetSubset(asset_key=other.asset_key, value=other.value)
        else:
            return self._replace(
                # unfortunately, this is the best way to get an empty partitions subset of an unknown
                # type if you don't have access to the partitions definition
                value=(self.subset_value - self.subset_value) if self.is_partitioned else False
            )
