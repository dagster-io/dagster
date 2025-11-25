"""Fast serialization for Dagster objects.

This module provides an optimized serialization format that significantly reduces
both size and serialization time for large objects with lots of duplication.

Key optimizations:
1. Schema-based encoding: Class and field names stored once, referenced by index
2. String interning: Repeated strings stored once, referenced by index
3. Object deduplication: Identical objects stored once, referenced by hash
4. Binary format: msgpack instead of JSON

Format:
{
    "v": 1,  # Version
    "s": {"c": [...], "f": [...]},  # Schema (class names, field names)
    "t": [...],  # String table
    "o": {...},  # Object table (hash -> packed object)
    "d": ...,  # Root data
}
"""

import hashlib
from dataclasses import is_dataclass
from enum import Enum
from typing import Any, Optional, Union

import msgpack

from dagster_shared.match import is_named_tuple_subclass
from dagster_shared.record import (
    as_dict as record_as_dict,
    is_record,
)
from dagster_shared.serdes.serdes import (
    _WHITELIST_MAP,
    SerializableNonScalarKeyMapping,
    WhitelistMap,
)

# Minimum string length to consider for interning
MIN_INTERN_LENGTH = 8

# Minimum occurrences for a string to be interned
MIN_INTERN_COUNT = 2

# Classes that are worth deduplicating
# Split into simple (can use repr for hashing) and complex (need recursive hashing)
SIMPLE_DEDUP_CLASSES = frozenset(
    {
        "AssetKey",
        "AssetCheckKey",
        "TimestampWithTimezone",
        "TimeWindow",
        "TimeWindowPartitionsDefinition",
    }
)

COMPLEX_DEDUP_CLASSES = frozenset(
    {
        "TimeWindowPartitionsSubset",  # Uses specialized hash function below
    }
)

# Combined for the dedup check
DEDUP_CLASSES = SIMPLE_DEDUP_CLASSES | COMPLEX_DEDUP_CLASSES


class PackContext:
    """Context for packing (serialization) operations."""

    def __init__(self) -> None:
        # Schema: maps class names to indices
        self.class_names: list[str] = []
        self.class_index: dict[str, int] = {}

        # Schema: maps field names to indices
        self.field_names: list[str] = []
        self.field_index: dict[str, int] = {}

        # String table: maps strings to indices
        self.strings: list[str] = []
        self.string_index: dict[str, int] = {}
        self.string_counts: dict[str, int] = {}  # Track counts for interning decision

        # Object deduplication: maps content hash to packed representation
        self.objects: dict[str, Any] = {}

        # Hash cache: maps object id to content hash (for performance within single serialization)
        self.hash_cache: dict[int, str] = {}

    def get_class_index(self, name: str) -> int:
        """Get or create index for a class name."""
        if name not in self.class_index:
            self.class_index[name] = len(self.class_names)
            self.class_names.append(name)
        return self.class_index[name]

    def get_field_index(self, name: str) -> int:
        """Get or create index for a field name."""
        if name not in self.field_index:
            self.field_index[name] = len(self.field_names)
            self.field_names.append(name)
        return self.field_index[name]

    def intern_string(self, s: str) -> Union[str, dict]:
        """Potentially intern a string, returning either the string or a reference.

        Returns the string directly if it's short or not seen enough times.
        Returns {"~": index} dict for interned strings.
        """
        if len(s) < MIN_INTERN_LENGTH:
            return s

        # Track count
        self.string_counts[s] = self.string_counts.get(s, 0) + 1

        # Check if already interned
        if s in self.string_index:
            return {"~": self.string_index[s]}

        # Intern if seen enough times
        if self.string_counts[s] >= MIN_INTERN_COUNT:
            idx = len(self.strings)
            self.string_index[s] = idx
            self.strings.append(s)
            return {"~": idx}

        return s

    def get_schema(self) -> dict:
        """Get the schema for the packed data."""
        return {
            "c": self.class_names,
            "f": self.field_names,
        }


class UnpackContext:
    """Context for unpacking (deserialization) operations."""

    def __init__(self, schema: dict, strings: list, objects: dict) -> None:
        self.class_names: list[str] = schema.get("c", [])
        self.field_names: list[str] = schema.get("f", [])
        self.strings: list[str] = strings
        self.objects: dict[str, Any] = objects
        self.unpacked_objects: dict[str, Any] = {}  # Cache unpacked objects


def _compute_content_hash(obj: Any, ctx: PackContext) -> str:
    """Compute a stable hash for object content.

    For simple classes (SIMPLE_DEDUP_CLASSES), uses repr() which is fast.
    For TimeWindowPartitionsSubset, uses a specialized hash that avoids full recursion.

    Caches results by object id() for performance within a single serialization run.
    """
    # Check cache first
    obj_id = id(obj)
    if obj_id in ctx.hash_cache:
        return ctx.hash_cache[obj_id]

    class_name = type(obj).__name__

    # For simple classes, use fast repr-based hashing
    if class_name in SIMPLE_DEDUP_CLASSES:
        full_repr = f"{class_name}:{obj!r}"
        result = hashlib.md5(full_repr.encode()).hexdigest()[:16]
        ctx.hash_cache[obj_id] = result
        return result

    # Special handling for TimeWindowPartitionsSubset
    # Its repr() doesn't include partitions_def, so we need custom hashing
    # But we can be smart: hash partitions_def (which uses repr) + hash of time_windows
    if class_name == "TimeWindowPartitionsSubset":
        # Get the essential fields
        pd = getattr(obj, "partitions_def", None)
        itw = getattr(obj, "included_time_windows", None)
        np = getattr(obj, "num_partitions", None)

        # Hash partitions_def using its repr (it's complete)
        pd_repr = repr(pd) if pd else "None"

        # Hash time_windows - just use repr of each PersistedTimeWindow
        # PersistedTimeWindow.start and .end are TimestampWithTimezone
        if itw:
            tw_parts = []
            for tw in itw:
                start = getattr(tw, "start", None)
                end = getattr(tw, "end", None)
                tw_parts.append(f"({start!r},{end!r})")
            tw_repr = "[" + ",".join(tw_parts) + "]"
        else:
            tw_repr = "[]"

        full_repr = f"TimeWindowPartitionsSubset:pd={pd_repr},itw={tw_repr},np={np}"
        result = hashlib.md5(full_repr.encode()).hexdigest()[:16]
        ctx.hash_cache[obj_id] = result
        return result

    # Fallback: recursive field traversal (shouldn't normally reach here)
    def to_hashable(val: Any) -> Any:
        if val is None or isinstance(val, (bool, int, float, str)):
            return val
        elif isinstance(val, Enum):
            return (type(val).__name__, val.name)
        elif is_record(val):
            return (type(val).__name__, to_hashable(tuple(sorted(record_as_dict(val).items()))))
        elif is_named_tuple_subclass(type(val)):
            return (type(val).__name__, to_hashable(tuple(sorted(val._asdict().items()))))
        elif is_dataclass(val) and not isinstance(val, type):
            return (type(val).__name__, to_hashable(tuple(sorted(val.__dict__.items()))))
        elif isinstance(val, dict):
            return ("dict", tuple(sorted((to_hashable(k), to_hashable(v)) for k, v in val.items())))
        elif isinstance(val, (list, tuple)):
            return (type(val).__name__, tuple(to_hashable(v) for v in val))
        elif isinstance(val, (set, frozenset)):
            return (type(val).__name__, frozenset(to_hashable(v) for v in val))
        else:
            return (type(val).__name__, repr(val))

    hashable = to_hashable(obj)
    result = hashlib.md5(repr(hashable).encode()).hexdigest()[:16]
    ctx.hash_cache[obj_id] = result
    return result


def pack_value_fast(
    val: Any,
    ctx: PackContext,
    whitelist_map: WhitelistMap = _WHITELIST_MAP,
    dedup: bool = True,
) -> Any:
    """Pack a value into the optimized format.

    Args:
        val: Value to pack
        ctx: Pack context for schema and deduplication
        whitelist_map: Whitelist map for registered types
        dedup: Whether to deduplicate objects

    Returns:
        Packed representation suitable for msgpack serialization
    """
    # Scalars pass through
    if val is None or isinstance(val, bool):
        return val

    if isinstance(val, (int, float)):
        return val

    if isinstance(val, str):
        return ctx.intern_string(val)

    # Lists
    if isinstance(val, (list, tuple)) and not is_named_tuple_subclass(type(val)):
        return [pack_value_fast(v, ctx, whitelist_map, dedup) for v in val]

    # Sets and frozensets
    if isinstance(val, (set, frozenset)):
        marker = "__set__" if isinstance(val, set) else "__frozenset__"
        packed_items = sorted(
            [pack_value_fast(v, ctx, whitelist_map, dedup) for v in val], key=lambda x: repr(x)
        )
        return {marker: packed_items}

    # Non-scalar key mappings
    if isinstance(val, SerializableNonScalarKeyMapping):
        return {
            "__mapping_items__": [
                [
                    pack_value_fast(k, ctx, whitelist_map, dedup),
                    pack_value_fast(v, ctx, whitelist_map, dedup),
                ]
                for k, v in val.items()
            ]
        }

    # Regular dicts - don't intern keys since they need to be hashable
    if isinstance(val, dict):
        return {k: pack_value_fast(v, ctx, whitelist_map, dedup) for k, v in val.items()}

    # Enums
    if isinstance(val, Enum):
        enum_class = type(val).__name__
        if enum_class in whitelist_map.enum_serializers:
            serializer = whitelist_map.enum_serializers[enum_class]
            return {"__enum__": f"{serializer.enum_type.__name__}.{val.name}"}
        else:
            return {"__enum__": f"{enum_class}.{val.name}"}

    # Whitelisted objects (NamedTuple, dataclass, pydantic, @record)
    class_name = type(val).__name__
    if class_name in whitelist_map.object_serializers:
        serializer = whitelist_map.object_serializers[class_name]

        # Only deduplicate specific classes (leaf types that appear frequently)
        should_dedup = dedup and class_name in DEDUP_CLASSES

        # Check for deduplication - use content hash only (no id())
        if should_dedup:
            # Compute content hash
            content_hash = _compute_content_hash(val, ctx)

            if content_hash in ctx.objects:
                # Same content - reuse existing packed representation
                return {"#": content_hash}

        # Get storage name
        storage_name = serializer.storage_name or class_name
        class_idx = ctx.get_class_index(storage_name)

        # Pack fields
        obj_dict = serializer.object_as_mapping(val)
        packed_fields = {}

        for field_name, field_value in obj_dict.items():
            # Apply field name mapping
            storage_field = field_name
            if serializer.storage_field_names and field_name in serializer.storage_field_names:
                storage_field = serializer.storage_field_names[field_name]

            # Skip empty fields if configured
            if (
                serializer.skip_when_empty_fields
                and field_name in serializer.skip_when_empty_fields
            ):
                if not field_value:
                    continue

            # Skip None fields if configured
            if serializer.skip_when_none_fields and field_name in serializer.skip_when_none_fields:
                if field_value is None:
                    continue

            # Apply field serializer if any
            if serializer.field_serializers and field_name in serializer.field_serializers:
                field_ser = serializer.field_serializers[field_name]
                field_value = field_ser.pack(field_value, whitelist_map, "")  # noqa: PLW2901

            # Get field index
            field_idx = ctx.get_field_index(storage_field)

            # Pack the value
            packed_fields[field_idx] = pack_value_fast(field_value, ctx, whitelist_map, dedup)

        # Create packed object
        packed = {"@": class_idx, **packed_fields}

        # Store for deduplication if enabled
        if should_dedup:
            ctx.objects[content_hash] = packed

        return packed

    # Fallback: try to handle as namedtuple, @record, or dataclass
    if is_record(val):
        class_idx = ctx.get_class_index(class_name)
        packed_fields = {}
        for field_name, field_value in record_as_dict(val).items():
            field_idx = ctx.get_field_index(field_name)
            packed_fields[field_idx] = pack_value_fast(field_value, ctx, whitelist_map, dedup)
        return {"@": class_idx, **packed_fields}

    if is_named_tuple_subclass(type(val)):
        class_idx = ctx.get_class_index(class_name)
        packed_fields = {}
        for field_name, field_value in val._asdict().items():
            field_idx = ctx.get_field_index(field_name)
            packed_fields[field_idx] = pack_value_fast(field_value, ctx, whitelist_map, dedup)
        return {"@": class_idx, **packed_fields}

    if is_dataclass(val) and not isinstance(val, type):
        class_idx = ctx.get_class_index(class_name)
        packed_fields = {}
        for field_name, field_value in val.__dict__.items():
            field_idx = ctx.get_field_index(field_name)
            packed_fields[field_idx] = pack_value_fast(field_value, ctx, whitelist_map, dedup)
        return {"@": class_idx, **packed_fields}

    raise TypeError(f"Cannot pack value of type {type(val)}: {val!r}")


def unpack_value_fast(
    val: Any,
    ctx: UnpackContext,
    whitelist_map: WhitelistMap = _WHITELIST_MAP,
) -> Any:
    """Unpack a value from the optimized format.

    Args:
        val: Packed value
        ctx: Unpack context with schema and object table
        whitelist_map: Whitelist map for registered types

    Returns:
        Unpacked Python object
    """
    # Scalars pass through
    if val is None or isinstance(val, (bool, int, float)):
        return val

    # Regular string
    if isinstance(val, str):
        return val

    # Lists
    if isinstance(val, list):
        return [unpack_value_fast(v, ctx, whitelist_map) for v in val]

    # Dicts with special markers
    if isinstance(val, dict):
        # Interned string reference: {"~": index}
        if "~" in val and len(val) == 1:
            return ctx.strings[val["~"]]

        # Object reference
        if "#" in val and len(val) == 1:
            obj_hash = val["#"]
            if obj_hash in ctx.unpacked_objects:
                return ctx.unpacked_objects[obj_hash]
            # Unpack from object table
            packed = ctx.objects[obj_hash]
            unpacked = unpack_value_fast(packed, ctx, whitelist_map)
            ctx.unpacked_objects[obj_hash] = unpacked
            return unpacked

        # Set
        if "__set__" in val:
            return set(unpack_value_fast(v, ctx, whitelist_map) for v in val["__set__"])

        # Frozenset
        if "__frozenset__" in val:
            return frozenset(unpack_value_fast(v, ctx, whitelist_map) for v in val["__frozenset__"])

        # Enum
        if "__enum__" in val:
            enum_str = val["__enum__"]
            class_name, member_name = enum_str.rsplit(".", 1)
            if class_name in whitelist_map.enum_serializers:
                enum_class = whitelist_map.enum_serializers[class_name].enum_type
                return enum_class[member_name]
            raise ValueError(f"Unknown enum class: {class_name}")

        # Non-scalar key mapping - unpack to regular dict
        if "__mapping_items__" in val:
            items = val["__mapping_items__"]
            return {
                unpack_value_fast(k, ctx, whitelist_map): unpack_value_fast(v, ctx, whitelist_map)
                for k, v in items
            }

        # Object with class marker
        if "@" in val:
            class_idx = val["@"]
            class_name = ctx.class_names[class_idx]

            if class_name in whitelist_map.object_deserializers:
                serializer = whitelist_map.object_deserializers[class_name]
                klass = serializer.klass

                # Unpack fields
                kwargs = {}
                for key, packed_value in val.items():
                    if key == "@":
                        continue

                    field_idx = key
                    field_name = ctx.field_names[field_idx]

                    # Reverse field name mapping
                    if serializer.storage_field_names:
                        reverse_map = {v: k for k, v in serializer.storage_field_names.items()}
                        if field_name in reverse_map:
                            field_name = reverse_map[field_name]

                    # Unpack value
                    unpacked_value = unpack_value_fast(packed_value, ctx, whitelist_map)

                    # Apply field deserializer if any
                    if serializer.field_serializers and field_name in serializer.field_serializers:
                        field_ser = serializer.field_serializers[field_name]
                        from dagster_shared.serdes.serdes import UnpackContext as OldUnpackContext

                        old_ctx = OldUnpackContext()
                        unpacked_value = field_ser.unpack(unpacked_value, whitelist_map, old_ctx)

                    kwargs[field_name] = unpacked_value

                # Apply old_fields defaults
                if serializer.old_fields:
                    for old_field, default_value in serializer.old_fields.items():
                        if old_field not in kwargs:
                            kwargs[old_field] = default_value

                # Construct object
                try:
                    return klass(**kwargs)
                except TypeError:
                    # Filter to only constructor params
                    constructor_params = set(serializer.constructor_param_names)
                    filtered_kwargs = {k: v for k, v in kwargs.items() if k in constructor_params}
                    return klass(**filtered_kwargs)

            raise ValueError(f"Unknown class: {class_name}")

        # Regular dict - keys are passed through as-is (not interned)
        return {k: unpack_value_fast(v, ctx, whitelist_map) for k, v in val.items()}

    raise TypeError(f"Cannot unpack value: {val!r}")


def serialize_value_fast(
    val: Any,
    whitelist_map: WhitelistMap = _WHITELIST_MAP,
    dedup: bool = True,
) -> bytes:
    """Serialize an object to optimized msgpack bytes.

    Args:
        val: Object to serialize
        whitelist_map: Whitelist map for registered types
        dedup: Whether to deduplicate objects (default True)

    Returns:
        msgpack-encoded bytes
    """
    ctx = PackContext()
    packed = pack_value_fast(val, ctx, whitelist_map, dedup)

    envelope = {
        "v": 1,  # Format version
        "s": ctx.get_schema(),
        "t": ctx.strings,
        "o": ctx.objects,
        "d": packed,
    }

    return msgpack.packb(envelope, use_bin_type=True)


def deserialize_value_fast(
    data: bytes,
    as_type: Optional[type] = None,
    whitelist_map: WhitelistMap = _WHITELIST_MAP,
) -> Any:
    """Deserialize msgpack bytes to an object.

    Args:
        data: msgpack-encoded bytes
        as_type: Expected type (for validation, not currently enforced)
        whitelist_map: Whitelist map for registered types

    Returns:
        Deserialized Python object
    """
    envelope = msgpack.unpackb(data, raw=False, strict_map_key=False)

    version = envelope.get("v", 1)
    if version != 1:
        raise ValueError(f"Unsupported format version: {version}")

    ctx = UnpackContext(
        schema=envelope.get("s", {}),
        strings=envelope.get("t", []),
        objects=envelope.get("o", {}),
    )

    return unpack_value_fast(envelope["d"], ctx, whitelist_map)
