import datetime
import operator
from typing import (
    TYPE_CHECKING,
    AbstractSet,
    Callable,
    NamedTuple,
    NewType,
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
from dagster._core.definitions.time_window_partitions import (
    BaseTimeWindowPartitionsSubset,
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

    @property
    def as_valid(self) -> "ValidAssetSubset":
        """Method to indicate to the type checker that this AssetSubset is valid based on the
        current PartitionsDefinition of the asset it represents.
        """
        return self  # type: ignore

    @staticmethod
    def all(
        asset_key: AssetKey,
        partitions_def: Optional[PartitionsDefinition],
        dynamic_partitions_store: Optional["DynamicPartitionsStore"] = None,
        current_time: Optional[datetime.datetime] = None,
    ) -> "ValidAssetSubset":
        if partitions_def is None:
            return AssetSubset(asset_key=asset_key, value=True).as_valid
        else:
            if dynamic_partitions_store is None or current_time is None:
                check.failed(
                    "Must provide dynamic_partitions_store and current_time for partitioned assets."
                )
            return AssetSubset(
                asset_key=asset_key,
                value=AllPartitionsSubset(partitions_def, dynamic_partitions_store, current_time),
            ).as_valid

    @staticmethod
    def empty(
        asset_key: AssetKey, partitions_def: Optional[PartitionsDefinition]
    ) -> "ValidAssetSubset":
        if partitions_def is None:
            return AssetSubset(asset_key=asset_key, value=False).as_valid
        else:
            return AssetSubset(asset_key=asset_key, value=partitions_def.empty_subset()).as_valid

    @staticmethod
    def from_asset_partitions_set(
        asset_key: AssetKey,
        partitions_def: Optional[PartitionsDefinition],
        asset_partitions_set: AbstractSet[AssetKeyPartitionKey],
    ) -> "ValidAssetSubset":
        if partitions_def is None:
            return AssetSubset(asset_key=asset_key, value=bool(asset_partitions_set)).as_valid
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
            ).as_valid

    def inverse(
        self,
        partitions_def: Optional[PartitionsDefinition],
        current_time: Optional[datetime.datetime] = None,
        dynamic_partitions_store: Optional["DynamicPartitionsStore"] = None,
    ) -> "ValidAssetSubset":
        """Returns the AssetSubset containing all asset partitions which are not in this AssetSubset."""
        if partitions_def is None:
            return self._replace(value=not self.bool_value).as_valid
        else:
            value = partitions_def.subset_with_partition_keys(
                self.subset_value.get_partition_keys_not_in_subset(
                    partitions_def,
                    current_time=current_time,
                    dynamic_partitions_store=dynamic_partitions_store,
                )
            )
            return self._replace(value=value).as_valid

    def _valid_empty_subset(self, valid: "ValidAssetSubset") -> "ValidAssetSubset":
        return valid._replace(
            # unfortunately, this is the best way to get an empty subset of an unknown type
            # if you don't have access to the partitions definition
            value=(valid.subset_value - valid.subset_value) if valid.is_partitioned else False
        )

    def _oper(self, other: "ValidAssetSubset", oper: Callable) -> "ValidAssetSubset":
        value = oper(self.value, other.value)
        return other._replace(value=value)

    def __sub__(self, other: "ValidAssetSubset") -> "ValidAssetSubset":
        """Returns an AssetSubset representing self - other if they are compatible, otherwise
        returns an empty subset.
        """
        if not self.is_compatible_with(other):
            return self._valid_empty_subset(valid=other)

        if not self.is_partitioned:
            return other._replace(value=self.bool_value and not other.bool_value)
        return self._oper(other, operator.sub)

    def __rsub__(self, other: "ValidAssetSubset") -> "ValidAssetSubset":
        """Returns an AssetSubset representing other - self if they are compatible, otherwise
        returns other.
        """
        if not self.is_compatible_with(other):
            return other

        if not self.is_partitioned:
            return other._replace(value=self.bool_value and not other.bool_value)
        return self._oper(other, operator.sub)

    def __and__(self, other: "ValidAssetSubset") -> "ValidAssetSubset":
        """Returns the intersection of this AssetSubset and another AssetSubset if they are compatible,
        otherwise returns an empty AssetSubset.
        """
        if not self.is_compatible_with(other):
            return self._valid_empty_subset(valid=other)
        return self._oper(other, operator.and_)

    def __or__(self, other: "ValidAssetSubset") -> "ValidAssetSubset":
        """Returns the union of this AssetSubset and another AssetSubset if they are compatible,
        otherwise returns the other AssetSubset.
        """
        if not self.is_compatible_with(other):
            return other
        return self._oper(other, operator.or_)

    def __contains__(self, item: AssetKeyPartitionKey) -> bool:
        if not self.is_partitioned:
            return (
                item.asset_key == self.asset_key and item.partition_key is None and self.bool_value
            )
        else:
            return item.asset_key == self.asset_key and item.partition_key in self.subset_value

    def is_compatible_with(self, other: "ValidAssetSubset") -> bool:
        if self.asset_key != other.asset_key:
            return False
        elif isinstance(self.value, BaseTimeWindowPartitionsSubset):
            # for time window partitions, we have access to the underlying partitions definitions so
            # we can ensure those are identical
            return (
                isinstance(other.value, (BaseTimeWindowPartitionsSubset, AllPartitionsSubset))
                and other.value.partitions_def == self.value.partitions_def
            )
        else:
            # otherwise, we just make sure that the underlying values are of the same type
            return self.is_partitioned == other.is_partitioned


# This type represents an AssetSubset which has been validated by the type checker to be compatible
# with the current PartitionsDefinition of the asset it represents.
ValidAssetSubset = NewType("ValidAssetSubset", AssetSubset)
