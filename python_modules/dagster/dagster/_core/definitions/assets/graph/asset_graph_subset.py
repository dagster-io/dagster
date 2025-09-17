import operator
from collections import defaultdict
from collections.abc import Iterable, Mapping
from typing import AbstractSet, Any, Callable, NamedTuple, Optional, Union  # noqa: UP035

from dagster_shared.serdes import (
    NamedTupleSerializer,
    SerializableNonScalarKeyMapping,
    whitelist_for_serdes,
)

from dagster import _check as check
from dagster._core.asset_graph_view.entity_subset import EntitySubset
from dagster._core.asset_graph_view.serializable_entity_subset import SerializableEntitySubset
from dagster._core.definitions.assets.graph.base_asset_graph import BaseAssetGraph
from dagster._core.definitions.events import AssetKey, AssetKeyPartitionKey
from dagster._core.definitions.partitions.definition import TimeWindowPartitionsDefinition
from dagster._core.definitions.partitions.subset import PartitionsSubset
from dagster._core.errors import DagsterDefinitionChangedDeserializationError


class PartitionsSubsetMappingNamedTupleSerializer(NamedTupleSerializer):
    """Serializes NamedTuples with fields that are mappings containing PartitionsSubsets.

    This is necessary because not all subsets are serializable.
    """

    def before_pack(self, value: NamedTuple) -> NamedTuple:
        replaced_value_by_field_name = {}
        for field_name, field_value in value._asdict().items():
            if isinstance(field_value, Mapping) and all(
                isinstance(v, PartitionsSubset) for v in field_value.values()
            ):
                # Converts non-serializable subsets to serializable ones
                subsets_by_key = {k: v.to_serializable_subset() for k, v in field_value.items()}

                # If the mapping is keyed by AssetKey wrap it in a SerializableNonScalarKeyMapping
                # so it can be serialized. This can be expanded to other key types in the future.
                if all(isinstance(k, AssetKey) for k in subsets_by_key.keys()):
                    replaced_value_by_field_name[field_name] = SerializableNonScalarKeyMapping(
                        subsets_by_key
                    )

        return value._replace(**replaced_value_by_field_name)


@whitelist_for_serdes(serializer=PartitionsSubsetMappingNamedTupleSerializer)
class AssetGraphSubset(NamedTuple):
    partitions_subsets_by_asset_key: Mapping[AssetKey, PartitionsSubset] = {}
    non_partitioned_asset_keys: AbstractSet[AssetKey] = set()

    @property
    def asset_keys(self) -> AbstractSet[AssetKey]:
        return {
            key
            for key, subset in self.partitions_subsets_by_asset_key.items()
            if not subset.is_empty
        } | self.non_partitioned_asset_keys

    @property
    def num_partitions_and_non_partitioned_assets(self) -> int:
        return len(self.non_partitioned_asset_keys) + sum(
            len(subset) for subset in self.partitions_subsets_by_asset_key.values()
        )

    @property
    def is_empty(self) -> bool:
        return len(self.asset_keys) == 0

    def _get_serializable_entity_subset(
        self, asset_key: AssetKey
    ) -> SerializableEntitySubset[AssetKey]:
        if asset_key in self.non_partitioned_asset_keys:
            return SerializableEntitySubset(key=asset_key, value=True)
        elif asset_key in self.partitions_subsets_by_asset_key:
            return SerializableEntitySubset(
                key=asset_key, value=self.partitions_subsets_by_asset_key[asset_key]
            )
        else:
            check.failed(f"Asset {asset_key} must be part of the AssetGraphSubset")

    def get_asset_subset(
        self, asset_key: AssetKey, asset_graph: BaseAssetGraph
    ) -> SerializableEntitySubset[AssetKey]:
        """Returns an AssetSubset representing the subset of a specific asset that this
        AssetGraphSubset contains.
        """
        if (
            asset_key in self.non_partitioned_asset_keys
            or asset_key in self.partitions_subsets_by_asset_key
        ):
            return self._get_serializable_entity_subset(asset_key)
        else:
            partitions_def = asset_graph.get(asset_key).partitions_def
            return SerializableEntitySubset(
                key=asset_key,
                value=partitions_def.empty_subset() if partitions_def else False,
            )

    def get_partitions_subset(
        self, asset_key: AssetKey, asset_graph: Optional[BaseAssetGraph] = None
    ) -> PartitionsSubset:
        if asset_graph:
            partitions_def = asset_graph.get(asset_key).partitions_def
            if partitions_def is None:
                check.failed("Can only call get_partitions_subset on a partitioned asset")

            return self.partitions_subsets_by_asset_key.get(
                asset_key, partitions_def.empty_subset()
            )
        else:
            return self.partitions_subsets_by_asset_key[asset_key]

    def iterate_asset_partitions(self) -> Iterable[AssetKeyPartitionKey]:
        for (
            asset_key,
            partitions_subset,
        ) in self.partitions_subsets_by_asset_key.items():
            for partition_key in partitions_subset.get_partition_keys():
                yield AssetKeyPartitionKey(asset_key, partition_key)

        for asset_key in self.non_partitioned_asset_keys:
            yield AssetKeyPartitionKey(asset_key, None)

    def iterate_asset_subsets(self) -> Iterable[SerializableEntitySubset[AssetKey]]:
        """Returns an Iterable of AssetSubsets representing the subset of each asset that this
        AssetGraphSubset contains.
        """
        for asset_key in self.asset_keys:
            yield self._get_serializable_entity_subset(asset_key)

    def __contains__(self, asset: Union[AssetKey, AssetKeyPartitionKey]) -> bool:  # pyright: ignore[reportIncompatibleMethodOverride]
        """If asset is an AssetKeyPartitionKey, check if the given AssetKeyPartitionKey is in the
        subset. If asset is an AssetKey, check if any of partitions of the given AssetKey are in
        the subset.
        """
        if isinstance(asset, AssetKey):
            # check if any keys are in the subset
            partitions_subset = self.partitions_subsets_by_asset_key.get(asset)
            return (partitions_subset is not None and len(partitions_subset) > 0) or (
                asset in self.non_partitioned_asset_keys
            )
        elif asset.partition_key is None:
            return asset.asset_key in self.non_partitioned_asset_keys
        else:
            partitions_subset = self.partitions_subsets_by_asset_key.get(asset.asset_key)
            return partitions_subset is not None and asset.partition_key in partitions_subset

    def to_storage_dict(self, asset_graph: BaseAssetGraph) -> Mapping[str, object]:
        return {
            "partitions_subsets_by_asset_key": {
                key.to_user_string(): value.serialize()
                for key, value in self.partitions_subsets_by_asset_key.items()
            },
            "serializable_partitions_def_ids_by_asset_key": {
                key.to_user_string(): check.not_none(
                    asset_graph.get(key).partitions_def
                ).get_serializable_unique_identifier()
                for key, _ in self.partitions_subsets_by_asset_key.items()
            },
            "partitions_def_class_names_by_asset_key": {
                key.to_user_string(): check.not_none(
                    asset_graph.get(key).partitions_def
                ).__class__.__name__
                for key, _ in self.partitions_subsets_by_asset_key.items()
            },
            "non_partitioned_asset_keys": [
                key.to_user_string() for key in self.non_partitioned_asset_keys
            ],
        }

    def _oper(self, other: "AssetGraphSubset", oper: Callable[..., Any]) -> "AssetGraphSubset":
        """Returns the AssetGraphSubset that results from applying the given operator to the set of
        asset partitions in self and other.

        Note: Not all operators are supported on the underlying PartitionsSubset objects.
        """
        result_partition_subsets_by_asset_key = {**self.partitions_subsets_by_asset_key}
        result_non_partitioned_asset_keys = set(self.non_partitioned_asset_keys)

        for asset_key in other.asset_keys:
            if asset_key in other.non_partitioned_asset_keys:
                check.invariant(asset_key not in self.partitions_subsets_by_asset_key)
                result_non_partitioned_asset_keys = oper(
                    result_non_partitioned_asset_keys, {asset_key}
                )
            else:
                check.invariant(asset_key not in self.non_partitioned_asset_keys)
                subset = (
                    self.get_partitions_subset(asset_key)
                    if asset_key in self.partitions_subsets_by_asset_key
                    else None
                )

                other_subset = other.get_partitions_subset(asset_key)

                if other_subset is not None and subset is not None:
                    result_partition_subsets_by_asset_key[asset_key] = oper(subset, other_subset)

                # Special case operations if either subset is None
                if subset is None and other_subset is not None and oper == operator.or_:
                    result_partition_subsets_by_asset_key[asset_key] = other_subset
                elif subset is not None and other_subset is None and oper == operator.and_:
                    del result_partition_subsets_by_asset_key[asset_key]

        return AssetGraphSubset(
            partitions_subsets_by_asset_key=result_partition_subsets_by_asset_key,
            non_partitioned_asset_keys=result_non_partitioned_asset_keys,
        )

    def __or__(self, other: "AssetGraphSubset") -> "AssetGraphSubset":
        return self._oper(other, operator.or_)

    def __sub__(self, other: "AssetGraphSubset") -> "AssetGraphSubset":
        return self._oper(other, operator.sub)

    def __and__(self, other: "AssetGraphSubset") -> "AssetGraphSubset":
        return self._oper(other, operator.and_)

    def filter_asset_keys(self, asset_keys: AbstractSet[AssetKey]) -> "AssetGraphSubset":
        return AssetGraphSubset(
            partitions_subsets_by_asset_key={
                asset_key: subset
                for asset_key, subset in self.partitions_subsets_by_asset_key.items()
                if asset_key in asset_keys
            },
            non_partitioned_asset_keys=self.non_partitioned_asset_keys & asset_keys,
        )

    def __eq__(self, other) -> bool:
        return (
            isinstance(other, AssetGraphSubset)
            and self.non_partitioned_asset_keys == other.non_partitioned_asset_keys
            and _non_empty(self.partitions_subsets_by_asset_key)
            == _non_empty(other.partitions_subsets_by_asset_key)
        )

    def __ne__(self, other) -> bool:
        return not self.__eq__(other)

    def __repr__(self) -> str:
        return (
            "AssetGraphSubset("
            f"non_partitioned_asset_keys={self.non_partitioned_asset_keys}, "
            f"partitions_subsets_by_asset_key={self.partitions_subsets_by_asset_key}"
            ")"
        )

    @classmethod
    def from_asset_partition_set(
        cls,
        asset_partitions_set: AbstractSet[AssetKeyPartitionKey],
        asset_graph: BaseAssetGraph,
        validate_time_range: bool = True,
    ) -> "AssetGraphSubset":
        partitions_by_asset_key = defaultdict(set)
        non_partitioned_asset_keys = set()
        for asset_key, partition_key in asset_partitions_set:
            if partition_key is not None:
                partitions_by_asset_key[asset_key].add(partition_key)
            else:
                non_partitioned_asset_keys.add(asset_key)

        partitions_subsets_by_asset_key = {}
        for asset_key, partition_keys in partitions_by_asset_key.items():
            partitions_def = asset_graph.get(asset_key).partitions_def
            subset = partitions_def.empty_subset()
            if isinstance(partitions_def, TimeWindowPartitionsDefinition):
                subset = subset.with_partition_keys(partition_keys, validate=validate_time_range)
            else:
                subset = subset.with_partition_keys(partition_keys)
            partitions_subsets_by_asset_key[asset_key] = subset

        return AssetGraphSubset(
            partitions_subsets_by_asset_key=partitions_subsets_by_asset_key,
            non_partitioned_asset_keys=non_partitioned_asset_keys,
        )

    @classmethod
    def create_empty_subset(cls) -> "AssetGraphSubset":
        return AssetGraphSubset({}, set())

    @classmethod
    def from_entity_subsets(
        cls, entity_subsets: Iterable[EntitySubset[AssetKey]]
    ) -> "AssetGraphSubset":
        return AssetGraphSubset(
            partitions_subsets_by_asset_key={
                subset.key: subset.get_internal_subset_value()
                for subset in entity_subsets
                if subset.is_partitioned and not subset.is_empty
            },
            non_partitioned_asset_keys={
                subset.key
                for subset in entity_subsets
                if not subset.is_partitioned and not subset.is_empty
            },
        )

    @classmethod
    def can_deserialize(
        cls, serialized_dict: Mapping[str, Any], asset_graph: BaseAssetGraph
    ) -> bool:
        serializable_partitions_ids = serialized_dict.get(
            "serializable_partitions_def_ids_by_asset_key", {}
        )

        partitions_def_class_names_by_asset_key = serialized_dict.get(
            "partitions_def_class_names_by_asset_key", {}
        )

        for key, value in serialized_dict["partitions_subsets_by_asset_key"].items():
            asset_key = AssetKey.from_user_string(key)
            if not asset_graph.has(asset_key):
                # Asset had a definition at storage time, but no longer does
                return False

            partitions_def = asset_graph.get(asset_key).partitions_def
            if partitions_def is None:
                # Asset had a partitions definition at storage time, but no longer does
                return False

            if not partitions_def.can_deserialize_subset(
                value,
                serialized_partitions_def_unique_id=serializable_partitions_ids.get(key),
                serialized_partitions_def_class_name=partitions_def_class_names_by_asset_key.get(
                    key
                ),
            ):
                return False

        return True

    @classmethod
    def from_storage_dict(
        cls,
        serialized_dict: Mapping[str, Any],
        asset_graph: BaseAssetGraph,
        allow_partial: bool = False,
    ) -> "AssetGraphSubset":
        serializable_partitions_ids = serialized_dict.get(
            "serializable_partitions_def_ids_by_asset_key", {}
        )

        partitions_def_class_names_by_asset_key = serialized_dict.get(
            "partitions_def_class_names_by_asset_key", {}
        )
        partitions_subsets_by_asset_key: dict[AssetKey, PartitionsSubset] = {}
        for key, value in serialized_dict["partitions_subsets_by_asset_key"].items():
            asset_key = AssetKey.from_user_string(key)

            if not asset_graph.has(asset_key):
                if not allow_partial:
                    raise DagsterDefinitionChangedDeserializationError(
                        f"Asset {key} existed at storage-time, but no longer does"
                    )
                continue

            partitions_def = asset_graph.get(asset_key).partitions_def

            if partitions_def is None:
                if not allow_partial:
                    raise DagsterDefinitionChangedDeserializationError(
                        f"Asset {key} had a PartitionsDefinition at storage-time, but no longer"
                        " does"
                    )
                continue

            if not partitions_def.can_deserialize_subset(
                value,
                serialized_partitions_def_unique_id=serializable_partitions_ids.get(key),
                serialized_partitions_def_class_name=partitions_def_class_names_by_asset_key.get(
                    key
                ),
            ):
                if not allow_partial:
                    raise DagsterDefinitionChangedDeserializationError(
                        f"Cannot deserialize stored partitions subset for asset {key}. This likely"
                        " indicates that the partitions definition has changed since this was"
                        " stored"
                    )
                continue

            partitions_subsets_by_asset_key[asset_key] = partitions_def.deserialize_subset(value)

        non_partitioned_asset_keys = {
            asset_key
            for key in serialized_dict["non_partitioned_asset_keys"]
            if asset_graph.has(asset_key := AssetKey.from_user_string(key))
        }

        return AssetGraphSubset(
            partitions_subsets_by_asset_key=partitions_subsets_by_asset_key,
            non_partitioned_asset_keys=non_partitioned_asset_keys,
        )

    @classmethod
    def all(cls, asset_graph: BaseAssetGraph) -> "AssetGraphSubset":
        return cls.from_asset_keys(asset_graph.materializable_asset_keys, asset_graph)

    @classmethod
    def from_asset_keys(
        cls, asset_keys: Iterable[AssetKey], asset_graph: BaseAssetGraph
    ) -> "AssetGraphSubset":
        partitions_subsets_by_asset_key: dict[AssetKey, PartitionsSubset] = {}
        non_partitioned_asset_keys: set[AssetKey] = set()

        for asset_key in asset_keys:
            partitions_def = asset_graph.get(asset_key).partitions_def
            if partitions_def:
                partitions_subsets_by_asset_key[asset_key] = (
                    partitions_def.empty_subset().with_partition_keys(
                        partitions_def.get_partition_keys()
                    )
                )
            else:
                non_partitioned_asset_keys.add(asset_key)

        return AssetGraphSubset(
            partitions_subsets_by_asset_key=partitions_subsets_by_asset_key,
            non_partitioned_asset_keys=non_partitioned_asset_keys,
        )


def _non_empty(d: Mapping[AssetKey, PartitionsSubset]) -> Mapping[AssetKey, PartitionsSubset]:
    """Returns a new dictionary with only the non-empty PartitionsSubsets in d."""
    return {k: v for k, v in d.items() if not v.is_empty}
