"""Writes serdes values in the compact format of `dagster_shared.serdes.compact` directly.

`serialize_value_compact(val)` must write the same packed value as `pack_value(val)`. Going
through `pack_value` would build a dict per object and then walk the packed value again, so this
module packs objects straight into the encoder's nodes instead. Serializers that customize packing
(`pack_items` or `before_pack`) still go through their generic path.

Most of the speed comes from two things:

* Values that are already known nodes (strings that were already seen, None and booleans) are looked
  up inline, without a call.
* Objects whose encoding was already computed are reused by identity: serdes objects of types that
  tend to be shared (e.g. asset keys in snapshots built from definitions) and long lists (e.g.
  partition keys). Memoizing by identity holds a reference to each memoized object, so that ids
  can't be reused while encoding.
"""

import collections
import collections.abc
from collections.abc import Callable, Mapping, Sequence
from dataclasses import is_dataclass
from enum import Enum
from typing import TYPE_CHECKING, Any, NamedTuple

from dagster_shared.check.record import is_record
from dagster_shared.serdes.compact import DICT_TAG, LIST_TAG, Encoder, json_scalar, scalar_key
from dagster_shared.serdes.errors import SerializationError
from dagster_shared.serdes.serdes import (
    EMPTY_VALUES_TO_SKIP,
    NamedTupleSerializer,
    ObjectSerializer,
    PackedObjects,
    PydanticModelSerializer,
    SerializableNonScalarKeyMapping,
    _get_pydantic_base_model,
    _pack_object,
    _transform_for_serialization,
    pack_value,
)

if TYPE_CHECKING:
    from dagster_shared.serdes.serdes import FieldSerializer, WhitelistMap

# Lists shorter than this are rarely shared, and cheap to deduplicate by value, so they aren't
# memoized by identity.
_MIN_MEMOIZED_LIST_LEN = 3

# Memoizing serdes objects by identity only pays off for types whose objects are referenced
# several times. Each type is sampled: memoization is turned off for it if none of its first
# _MEMO_SAMPLE_SIZE objects is referenced twice. This only affects speed, since equal values are
# deduplicated anyway when interned.
_MEMO_SAMPLE_SIZE = 100
_MEMO_ON = -1
_MEMO_OFF = 0

_STR_TYPES = {str}
_CONTAINER_TYPES = {list, dict}


# The `_asdict` method that `collections.namedtuple` generates: every class has its own function
# object, but they share their code.
_DEFAULT_ASDICT_CODE = collections.namedtuple("_Example", "x")._asdict.__code__


def _has_default_asdict(klass: type) -> bool:
    asdict = getattr(klass, "_asdict", None)
    return getattr(asdict, "__code__", None) is _DEFAULT_ASDICT_CODE


class _Plan(NamedTuple):
    """How to pack the objects of a serializer that doesn't customize packing."""

    storage_name: str
    storage_field_names: Mapping[str, str]
    field_serializers: Mapping[str, "FieldSerializer"]
    skip_when_empty_fields: Any
    skip_when_none_fields: Any
    old_fields: Mapping[str, Any]
    # Field names, for records and NamedTuples, which are tuples of their field values. None for
    # other objects, which are packed from their `object_as_mapping`.
    tuple_field_names: tuple[str, ...] | None
    # Attribute names, for pydantic models without aliases. None for other objects.
    attribute_names: tuple[str, ...] | None
    # Class tags, by the field names actually written (fields may be skipped).
    class_tags: dict[tuple[str, ...], int]
    # Whether all fields are written as is, without field serializers.
    is_plain: bool
    # When all fields are written, some with a field serializer: their indexes and serializers.
    custom_fields: tuple[tuple[int, "FieldSerializer"], ...] | None


class CompactPacker(Encoder):
    def __init__(self, whitelist_map: "WhitelistMap"):
        super().__init__()
        self.whitelist_map = whitelist_map
        self.packed_objects_type = PackedObjects
        # node ids of None, True and False
        self.scalar_ids = {
            value: self.intern((type(value), value)) for value in (None, True, False)
        }
        # node ids of the markers of packed sets and frozensets
        self.set_markers = {set: self.intern("__set__"), frozenset: self.intern("__frozenset__")}
        # node ids of enum members, by id, and their types
        self.enum_ids: dict[int, int] = {}
        self.enum_types: set[type] = set()
        # Per serdes object type seen so far: its serializer, or for plain objects that aren't
        # memoized, their class tag (records and NamedTuples) or their class tag and attribute
        # names (pydantic models).
        self.object_types: dict[type, ObjectSerializer | int | tuple[int, tuple[str, ...]]] = {}
        # Per serdes object type: _MEMO_ON, _MEMO_OFF, or the number of objects left to sample.
        self.memo_states: dict[type, int] = {}
        self.memo: dict[int, int] = {}
        self.memoized: list[Any] = []
        self.plans: dict[ObjectSerializer, _Plan | None] = {}
        # class tags of the packed objects returned by field serializers, by class name and keys
        self.packed_class_tags: dict[tuple[str, tuple[str, ...]], int] = {}

    def release(self) -> None:
        super().release()
        self.enum_ids = {}
        self.object_types = {}
        self.memo = {}
        self.memoized = []
        self.plans = {}

    def pack_root(self, val: Any) -> int:
        try:
            return self.pack(val)
        except SerializationError:
            # Descent paths aren't tracked, since they are only needed for errors: pack again
            # with `pack_value` to raise the error with its descent path.
            pack_value(val, self.whitelist_map)
            raise

    def pack(self, val: Any) -> int:
        tval = type(val)
        if tval is str:
            key = val
        elif val is None or tval is bool or tval is int or tval is float:
            key = scalar_key(val)
        elif tval is list or tval is tuple:  # tuples are packed as lists, like `pack_value`
            if not val:
                key = (LIST_TAG,)
            elif tval is tuple or len(val) < _MIN_MEMOIZED_LIST_LEN:
                # short lists and tuples, mostly of already seen strings (e.g. asset key parts)
                get = self.node_ids.get
                key = (
                    LIST_TAG,
                    *[
                        (get(item) if type(item) is str else None) or self.pack(item)
                        for item in val
                    ],
                )
            else:
                node_id = self.memo.get(id(val))
                if node_id is None:
                    node_id = self.memo[id(val)] = self.intern((LIST_TAG, *self.pack_all(val)))
                    self.memoized.append(val)
                return node_id
        else:
            serializer = self.object_types.get(tval)
            if type(serializer) is tuple:
                # plain pydantic model that isn't memoized: class tag and attribute names
                tag, names = serializer
                attributes = val.__dict__
                key = (tag, *self.pack_all([attributes[name] for name in names]))
            elif type(serializer) is int:
                # Plain record or NamedTuple that isn't memoized: `serializer` is its class tag.
                # Most field values are None, booleans or already seen strings.
                get = self.node_ids.get
                scalar_ids = self.scalar_ids
                key = (
                    serializer,
                    *[
                        scalar_ids[v]
                        if v is None or v is True or v is False
                        else (get(v) if type(v) is str else None) or self.pack(v)
                        for v in tuple.__iter__(val)
                    ],
                )
            elif serializer is not None:
                return self._pack_memoized_object(val, tval, serializer)
            else:
                node_id = self.enum_ids.get(id(val)) if tval in self.enum_types else None
                return self._pack_other(val, tval) if node_id is None else node_id
        # inlined `intern`, since this is the hottest path
        node_ids = self.node_ids
        node_id = node_ids.get(key)
        if node_id is None:
            node_id = node_ids[key] = len(self.nodes)
            self.nodes.append(key)
        return node_id

    def pack_all(self, values: Any) -> list[int]:
        """Pack each of `values`. Strings that were already seen, None and booleans are looked up
        without a call.
        """
        if type(values) is list and len(values) >= _MIN_MEMOIZED_LIST_LEN:
            # Long lists are mostly of already seen strings (e.g. partition keys).
            if set(map(type, values)) == _STR_TYPES:
                node_ids = list(map(self.node_ids.get, values))
                if None not in node_ids:
                    return node_ids
        get = self.node_ids.get
        scalar_ids = self.scalar_ids
        pack = self.pack
        return [
            scalar_ids[value]
            if value is None or value is True or value is False
            else (get(value) if type(value) is str else None) or pack(value)
            for value in values
        ]

    def _pack_memoized_object(self, val: Any, tval: type, serializer: ObjectSerializer) -> int:
        memo_state = self.memo_states[tval]
        if memo_state == _MEMO_OFF:
            return self._pack_object(val, serializer)
        node_id = self.memo.get(id(val))
        if node_id is not None:
            if memo_state > 0:
                self.memo_states[tval] = _MEMO_ON
            return node_id
        node_id = self.memo[id(val)] = self._pack_object(val, serializer)
        self.memoized.append(val)
        if memo_state > 0:
            if memo_state > 1:
                self.memo_states[tval] = memo_state - 1
            else:
                self._stop_memoizing(tval, serializer)
        return node_id

    def _stop_memoizing(self, tval: type, serializer: ObjectSerializer) -> None:
        self.memo_states[tval] = _MEMO_OFF
        plan = self.plans.get(serializer)
        if plan is not None and plan.is_plain:
            if plan.tuple_field_names is not None:
                # plain records and NamedTuples take the fast path in `pack`
                self.object_types[tval] = self._class_tag(plan, plan.tuple_field_names)
            elif plan.attribute_names is not None:
                # plain pydantic models too, through their attributes
                self.object_types[tval] = (
                    self._class_tag(plan, plan.attribute_names),
                    plan.attribute_names,
                )

    def _pack_other(self, val: Any, tval: type) -> int:
        """Pack a value that isn't a scalar, list, tuple, or known serdes object type."""
        whitelist_map = self.whitelist_map
        if tval is dict:
            return self._pack_dict_items(list(val.items()), self.pack)
        if tval is set or tval is frozenset:
            # sorted by `str` like `pack_value`, which is plain sorting for sets of strings
            items = sorted(val) if set(map(type, val)) <= _STR_TYPES else sorted(val, key=str)
            marker = self.set_markers[tval]
            return self.intern((DICT_TAG, marker, self.intern((LIST_TAG, *self.pack_all(items)))))
        if isinstance(val, Enum):
            node_id = self.add(_transform_for_serialization(val, whitelist_map, _pack_object, ""))
            # enum members are singletons, so they are memoized by identity: members of different
            # enums can be equal, e.g. with a str mixin
            self.enum_ids[id(val)] = node_id
            self.enum_types.add(tval)
            return node_id
        if tval is SerializableNonScalarKeyMapping:
            return self.add(_transform_for_serialization(val, whitelist_map, _pack_object, ""))
        if (
            (isinstance(val, tuple) and hasattr(val, "_fields"))
            or isinstance(val, _get_pydantic_base_model())
            or (is_dataclass(val) and not isinstance(val, type))
        ):
            serializer = whitelist_map.object_serializers.get(tval.__name__)
            if serializer is None:
                raise SerializationError(
                    f"Can only serialize whitelisted namedtuples, received {val}."
                )
            # first object of its type: register the type for the dispatch in `pack`
            self.object_types[tval] = serializer
            self.memo_states[tval] = _MEMO_SAMPLE_SIZE
            return self.pack(val)
        if isinstance(val, (set, frozenset)):
            marker = "__set__" if isinstance(val, set) else "__frozenset__"
            items = self.intern((LIST_TAG, *self.pack_all(sorted(list(val), key=str))))
            return self.intern((DICT_TAG, self.intern(marker), items))
        if isinstance(val, (str, int, float)):
            # subclasses of JSON scalars, which `json.dumps` writes as their plain value
            return self.add(json_scalar(val))
        if isinstance(val, collections.abc.Mapping):
            return self._pack_dict_items(list(val.items()), self.pack)
        if isinstance(val, collections.abc.Sequence):
            return self.intern((LIST_TAG, *self.pack_all(list(val))))
        raise SerializationError(f"Unhandled value type {tval}")

    def _pack_dict_items(self, items: Any, pack_value: Callable[[Any], int]) -> int:
        """Pack a dict that isn't a serdes object, e.g. tags."""
        keys = [key for key, _ in items]
        if set(map(type, keys)) - _STR_TYPES or keys != sorted(keys):
            # keys that must be converted or sorted, like the legacy format does
            return self.add_dict_items(items, pack_value)
        # Most dicts have str keys that are already sorted: pack keys and values without a call
        # when they were already seen.
        get = self.node_ids.get
        intern = self.intern
        scalar_ids = self.scalar_ids
        children = []
        for key, value in items:
            children.append(get(key) or intern(key))
            children.append(
                scalar_ids[value]
                if value is None or value is True or value is False
                else (get(value) if type(value) is str else None) or pack_value(value)
            )
        return intern((DICT_TAG, *children))

    def pack_packed(self, val: Any) -> int:
        """Pack the result of `FieldSerializer.pack_shallow`: a value that may be partially packed
        already, where packed serdes objects are dicts with a `__class__` key, or `PackedObjects`.
        """
        tval = type(val)
        if tval is self.packed_objects_type:
            tag = self.class_tag(val.class_name, val.field_names)
            intern = self.intern
            # same as `pack_all` on each row, inlined since rows are many and short
            get = self.node_ids.get
            scalar_ids = self.scalar_ids
            pack = self.pack
            return intern(
                (
                    LIST_TAG,
                    *[
                        intern(
                            (
                                tag,
                                *[
                                    scalar_ids[value]
                                    if value is None or value is True or value is False
                                    else (get(value) if type(value) is str else None) or pack(value)
                                    for value in row
                                ],
                            )
                        )
                        for row in val.rows
                    ],
                )
            )
        if tval is list:
            if not any(type(item) in _CONTAINER_TYPES for item in val):
                return self.intern((LIST_TAG, *self.pack_all(val)))
            pack_packed = self.pack_packed
            return self.intern((LIST_TAG, *[pack_packed(item) for item in val]))
        if tval is not dict:
            return self.pack(val)
        class_name = val.get("__class__")
        if type(class_name) is not str:
            return self._pack_dict_items(list(val.items()), self.pack_packed)
        keys = tuple(val)
        tag = self.packed_class_tags.get((class_name, keys))
        if tag is None:
            tag = self.packed_class_tags[(class_name, keys)] = self.class_tag(
                class_name, tuple([key for key in keys if key != "__class__"])
            )
        # Packed objects are mostly flat (e.g. metadata entries, whose values are serdes objects):
        # pack their values directly.
        get = self.node_ids.get
        scalar_ids = self.scalar_ids
        pack = self.pack
        pack_packed = self.pack_packed
        return self.intern(
            (
                tag,
                *[
                    scalar_ids[value]
                    if value is None or value is True or value is False
                    else (get(value) if type(value) is str else None)
                    or (pack_packed(value) if type(value) in _CONTAINER_TYPES else pack(value))
                    for key, value in val.items()
                    if key != "__class__"
                ],
            )
        )

    def _plan(self, serializer: ObjectSerializer) -> _Plan | None:
        klass = type(serializer)
        if (
            klass.pack_items is not ObjectSerializer.pack_items
            or klass.before_pack is not ObjectSerializer.before_pack
        ):
            return None
        tuple_field_names = None
        attribute_names = None
        if (
            klass.object_as_mapping is NamedTupleSerializer.object_as_mapping
            and issubclass(serializer.klass, tuple)
            # `object_as_mapping` uses `_asdict` for NamedTuples, which the class could override
            and (is_record(serializer.klass) or _has_default_asdict(serializer.klass))
        ):
            # `object_as_mapping` maps the fields of records and NamedTuples to their values, with
            # record fields renamed by `__field_remap__`.
            remap = getattr(serializer.klass, "__field_remap__", None) or {}
            tuple_field_names = tuple(
                [remap.get(name, name) for name in serializer.klass._fields]  # ty: ignore[unresolved-attribute]
            )
        elif klass.object_as_mapping is PydanticModelSerializer.object_as_mapping:
            model_fields = serializer._model_fields  # noqa: SLF001  # ty: ignore[unresolved-attribute]
            if all(
                field.alias is None
                and field.serialization_alias is None
                and field.validation_alias is None
                for field in model_fields.values()
            ):
                attribute_names = tuple(model_fields)
        field_names = tuple_field_names or attribute_names
        no_skips = not serializer.skip_when_empty_fields and not serializer.skip_when_none_fields
        return _Plan(
            storage_name=serializer.get_storage_name(),
            storage_field_names=serializer.storage_field_names,
            field_serializers=serializer.field_serializers,
            skip_when_empty_fields=serializer.skip_when_empty_fields,
            skip_when_none_fields=serializer.skip_when_none_fields,
            old_fields=serializer.old_fields,
            tuple_field_names=tuple_field_names,
            attribute_names=attribute_names,
            class_tags={},
            is_plain=no_skips and not serializer.field_serializers and not serializer.old_fields,
            custom_fields=tuple(
                [
                    (index, serializer.field_serializers[name])
                    for index, name in enumerate(field_names)
                    if name in serializer.field_serializers
                ]
            )
            if field_names is not None and no_skips
            else None,
        )

    def _class_tag(self, plan: _Plan, field_names: tuple[str, ...]) -> int:
        tag = plan.class_tags.get(field_names)
        if tag is None:
            tag = plan.class_tags[field_names] = self.class_tag(
                plan.storage_name,
                tuple([plan.storage_field_names.get(name, name) for name in field_names]),
            )
        return tag

    def _pack_object(self, val: Any, serializer: ObjectSerializer) -> int:
        plans = self.plans
        if serializer in plans:
            plan = plans[serializer]
        else:
            plan = plans[serializer] = self._plan(serializer)
        if plan is None:
            return self.add(dict(serializer.pack_items(val, self.whitelist_map, _pack_object, "")))

        if plan.tuple_field_names is not None:
            field_names = plan.tuple_field_names
            values: Sequence[Any] = tuple(tuple.__iter__(val))
        elif plan.attribute_names is not None:
            field_names = plan.attribute_names
            values = [val.__dict__[name] for name in field_names]
        else:
            mapping = serializer.object_as_mapping(val)
            field_names = tuple(mapping)
            values = list(mapping.values())

        if plan.is_plain:
            children = self.pack_all(values)
        elif plan.custom_fields is not None:
            # All fields are written: pack the plain ones in bulk, then the custom ones.
            plain_values = list(values)
            for index, _ in plan.custom_fields:
                plain_values[index] = None
            children = self.pack_all(plain_values)
            for index, field_serializer in plan.custom_fields:
                children[index] = self.pack_packed(
                    field_serializer.pack_shallow(values[index], self.whitelist_map)
                )
            if plan.old_fields:
                field_names = (*field_names, *plan.old_fields)
                children.extend([self.add(default) for default in plan.old_fields.values()])
        else:
            names: list[str] = []
            children = []
            skip_empty = plan.skip_when_empty_fields
            skip_none = plan.skip_when_none_fields
            for name, field_value in zip(field_names, values):
                field_serializer = plan.field_serializers.get(name)
                value = (
                    field_value
                    if field_serializer is None
                    else field_serializer.pack_shallow(field_value, self.whitelist_map)
                )
                if (
                    skip_empty
                    and name in skip_empty
                    and (
                        value in EMPTY_VALUES_TO_SKIP
                        or (type(value) is self.packed_objects_type and not value.rows)
                    )
                ) or (skip_none and name in skip_none and value is None):
                    continue
                names.append(name)
                children.append(
                    self.pack(value) if field_serializer is None else self.pack_packed(value)
                )
            for name, default in plan.old_fields.items():
                names.append(name)
                children.append(self.add(default))
            field_names = tuple(names)
        return self.intern((self._class_tag(plan, field_names), *children))
