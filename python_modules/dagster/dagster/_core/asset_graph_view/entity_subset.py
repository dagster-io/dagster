import operator
from typing import (  # noqa: UP035
    TYPE_CHECKING,
    AbstractSet,
    Any,
    Callable,
    Generic,
    Literal,
    NamedTuple,
    Optional,
    TypeVar,
    Union,
)

from typing_extensions import Self

from dagster import _check as check
from dagster._core.asset_graph_view.serializable_entity_subset import (
    EntitySubsetValue,
    SerializableEntitySubset,
)
from dagster._core.definitions.asset_key import AssetCheckKey, EntityKey, T_EntityKey
from dagster._core.definitions.events import AssetKey, AssetKeyPartitionKey
from dagster._core.definitions.partitions.definition.partitions_definition import (
    PartitionsDefinition,
)
from dagster._core.definitions.partitions.subset import PartitionsSubset
from dagster._utils.cached_method import cached_method

if TYPE_CHECKING:
    from dagster._core.asset_graph_view.asset_graph_view import AssetGraphView


U_EntityKey = TypeVar("U_EntityKey", AssetKey, AssetCheckKey, EntityKey)


class _ValidatedEntitySubsetValue(NamedTuple):
    inner: EntitySubsetValue


class EntitySubset(Generic[T_EntityKey]):
    """An EntitySubset represents a subset of a given EntityKey tied to a particular instance of an
    AssetGraphView.
    """

    _key: T_EntityKey
    _value: EntitySubsetValue

    def __init__(
        self,
        asset_graph_view: "AssetGraphView",
        key: T_EntityKey,
        value: _ValidatedEntitySubsetValue,
    ):
        self._asset_graph_view = asset_graph_view

        self._key = key
        self._value = check.inst_param(value, "value", _ValidatedEntitySubsetValue).inner

    @property
    def key(self) -> T_EntityKey:
        return self._key

    @property
    def partitions_def(self) -> Optional[PartitionsDefinition]:
        return self._asset_graph_view.asset_graph.get(self._key).partitions_def

    def convert_to_serializable_subset(self) -> SerializableEntitySubset[T_EntityKey]:
        return SerializableEntitySubset(key=self._key, value=self._value)

    def expensively_compute_partition_keys(self) -> AbstractSet[str]:
        return {
            check.not_none(akpk.partition_key, "No None partition keys")
            for akpk in self.expensively_compute_asset_partitions()
        }

    def expensively_compute_asset_partitions(self) -> AbstractSet[AssetKeyPartitionKey]:
        if not isinstance(self.key, AssetKey):
            check.failed(f"Unsupported operation for type {type(self.key)}")
        internal_value = self.get_internal_value()
        if isinstance(internal_value, PartitionsSubset):
            partition_keys = internal_value.get_partition_keys()
        else:
            partition_keys = {None} if internal_value else set()
        return {AssetKeyPartitionKey(self.key, pk) for pk in partition_keys}

    def _oper(self, other: Self, oper: Callable[..., Any]) -> Self:
        value = oper(self.get_internal_value(), other.get_internal_value())
        return self.__class__(
            self._asset_graph_view, key=self._key, value=_ValidatedEntitySubsetValue(value)
        )

    def compute_difference(self, other: Self) -> Self:
        if isinstance(self._value, bool):
            value = self.get_internal_bool_value() and not other.get_internal_bool_value()
            return self.__class__(
                self._asset_graph_view, key=self._key, value=_ValidatedEntitySubsetValue(value)
            )
        else:
            return self._oper(other, operator.sub)

    def compute_union(self, other: Self) -> Self:
        return self._oper(other, operator.or_)

    def compute_intersection(self, other: Self) -> Self:
        return self._oper(other, operator.and_)

    def compute_intersection_with_partition_keys(
        self: "EntitySubset[AssetKey]", partition_keys: AbstractSet[str]
    ) -> "EntitySubset[AssetKey]":
        key = check.inst(self.key, AssetKey)
        partition_subset = self._asset_graph_view.get_asset_subset_from_asset_partitions(
            self.key, {AssetKeyPartitionKey(key, pk) for pk in partition_keys}
        )
        return self.compute_intersection(partition_subset)

    @cached_method
    def compute_parent_subset(self, parent_key: AssetKey) -> "EntitySubset[AssetKey]":
        return self._asset_graph_view.compute_parent_subset(parent_key, self)

    @cached_method
    def compute_child_subset(self, child_key: U_EntityKey) -> "EntitySubset[U_EntityKey]":
        return self._asset_graph_view.compute_child_subset(child_key, self)

    @cached_method
    def compute_mapped_subset(
        self, to_key: U_EntityKey, direction: Literal["up", "down"]
    ) -> "EntitySubset[U_EntityKey]":
        return self._asset_graph_view.compute_mapped_subset(to_key, self, direction=direction)

    @property
    def size(self) -> int:
        if isinstance(self._value, bool):
            return int(self._value)
        else:
            return len(self._value)

    @property
    def is_empty(self) -> bool:
        if isinstance(self._value, bool):
            return not self._value
        else:
            return self._value.is_empty

    @property
    def is_partitioned(self) -> bool:
        return isinstance(self._value, PartitionsSubset)

    def get_internal_value(self) -> Union[bool, PartitionsSubset]:
        return self._value

    def get_internal_subset_value(self) -> PartitionsSubset:
        return check.inst(self._value, PartitionsSubset)

    def get_internal_bool_value(self) -> bool:
        return check.inst(self._value, bool)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}<{self.key}>({self.get_internal_value()})"
