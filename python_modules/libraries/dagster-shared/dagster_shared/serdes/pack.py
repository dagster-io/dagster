"""Compressed serialization for serdes objects.

Provides deduplication and columnar packing of serialized data. Plugs a custom
object_handler into ``_transform_for_serialization`` so columnar collection
happens during the single serialization pass.

Columnar packing works by:

1. Grouping serialized objects by class, storing field names once per class
2. Storing each object's values as a compact positional row (no field names)
3. Deduplicating identical objects via content hashing (same-content rows
   share the same row index)
4. Replacing inline objects with compact ``{"__oid__": "tableId:rowIndex"}``
   references (numeric table IDs minimize payload size)

Usage::

    packed_json = serialize_deduped(cursor)
    cursor = deserialize_deduped(packed_json, as_type=AssetDaemonCursor)
"""

from collections.abc import Mapping
from typing import Any, cast, overload

from dagster_shared import seven
from dagster_shared.match import match_type
from dagster_shared.serdes.serdes import (
    _WHITELIST_MAP,
    JsonSerializableValue,
    PackableValue,
    SerializableObject,
    T_PackableValue,
    U_PackableValue,
    UnpackContext,
    UnpackedValue,
    WhitelistMap,
    _transform_for_serialization,
    _unpack_object,
)

# Wire format keys. Single-letter table keys minimize serialized size.
_COLUMNAR_KEY = "__columnar__"  # envelope marker: this is a columnar-packed payload
_OBJ_ID_KEY = "__oid__"  # inline ref: replaced object → "tableId:rowIndex"
_TABLE_CLASS_KEY = "c"  # table field: the serdes storage name for this class
_TABLE_FIELDS_KEY = "f"  # table field: ordered list of field names
_TABLE_ROWS_KEY = "r"  # table field: list of rows (each row is positional values)


###############################################################################
# Public API
###############################################################################


def serialize_deduped(
    val: PackableValue,
    whitelist_map: WhitelistMap = _WHITELIST_MAP,
    columnar_classes: frozenset[str] | None = None,
) -> str:
    """Serialize a value into columnar-packed JSON with deduplication.

    Args:
        columnar_classes: If provided, only these storage names will be packed into
            columnar tables.  All other serdes objects are serialized inline (like
            normal ``serialize_value``).  When ``None`` (the default), *every*
            serdes object is columnar-packed.
    """
    collector = _ColumnarCollector()
    handler = _make_collecting_handler(collector, columnar_classes)

    tree = _transform_for_serialization(
        val,
        whitelist_map=whitelist_map,
        object_handler=handler,
        # Empty descent_path disables path tracking in error messages for perf.
        # Acceptable because callers (e.g. asset daemon) catch and re-raise with
        # their own context.
        descent_path="",
    )

    envelope = {
        _COLUMNAR_KEY: True,
        "tables": collector.tables,
        "value": tree,
    }
    return seven.json.dumps(envelope)


@overload
def deserialize_deduped(
    val: str,
    as_type: tuple[type[T_PackableValue], type[U_PackableValue]],
    whitelist_map: WhitelistMap = ...,
) -> T_PackableValue | U_PackableValue: ...


@overload
def deserialize_deduped(
    val: str,
    as_type: type[T_PackableValue],
    whitelist_map: WhitelistMap = ...,
) -> T_PackableValue: ...


@overload
def deserialize_deduped(
    val: str,
    as_type: None = ...,
    whitelist_map: WhitelistMap = ...,
) -> PackableValue: ...


def deserialize_deduped(
    val: str,
    as_type: type[T_PackableValue]
    | tuple[type[T_PackableValue], type[U_PackableValue]]
    | None = None,
    whitelist_map: WhitelistMap = _WHITELIST_MAP,
) -> PackableValue | T_PackableValue | U_PackableValue:
    """Deserialize a JSON string produced by ``serialize_deduped``."""
    parsed = seven.json.loads(val)

    context = UnpackContext()
    unpacked = _unpack_columnar(
        parsed["value"], parsed["tables"], whitelist_map, context, row_cache={}
    )
    result = context.finalize_unpack(unpacked)

    if as_type is not None and not match_type(result, as_type):  # type: ignore[arg-type]
        from dagster_shared.serdes.errors import DeserializationError

        raise DeserializationError(
            f"Unpacked object was not expected type {as_type}, got {type(result)}"
        )
    return result


###############################################################################
# Columnar packing (serialization)
###############################################################################


def _make_hashable(val: Any) -> Any:
    """Convert a JSON-serializable value to a hashable form for dedup.

    Fast-paths ``__oid__`` ref dicts (already simple strings) to avoid
    building unnecessary tuples — these make up ~30% of row values in
    practice.
    """
    if isinstance(val, dict):
        oid = val.get(_OBJ_ID_KEY)
        if oid is not None:
            return oid
        # Only bare mapping dicts reach here — @record instances are already
        # replaced with __oid__ refs (fast-pathed above) by the time _make_hashable runs.
        return tuple(sorted((k, _make_hashable(v)) for k, v in val.items()))
    if isinstance(val, list):
        return tuple(_make_hashable(v) for v in val)
    return val


class _ColumnarCollector:
    """Collects serialized objects into columnar tables during serialization.

    Each class gets a table with field names stored once and values as compact
    rows.  Duplicate objects (by value-equal row content) share the same row
    index.  Tables are stored as a list and referenced by numeric table_id in
    ``__oid__`` refs to minimize payload size.
    """

    def __init__(self) -> None:
        self.tables: list[dict[str, Any]] = []
        self._class_to_table_id: dict[str, int] = {}
        # (table_id, hashable_row) -> row index for dedup
        self._dedup: dict[tuple, int] = {}

    def register(
        self, class_name: str, fields_dict: Mapping[str, JsonSerializableValue]
    ) -> JsonSerializableValue:
        """Register a serialized object and return an ``__oid__`` ref.

        ``fields_dict`` contains already-serialized field values — nested
        objects are already ``__oid__`` refs, so hashing covers only one level.
        """
        if class_name not in self._class_to_table_id:
            table_id = len(self.tables)
            self._class_to_table_id[class_name] = table_id
            fields = sorted(k for k in fields_dict if k != "__class__")
            self.tables.append(
                {
                    _TABLE_CLASS_KEY: class_name,
                    _TABLE_FIELDS_KEY: fields,
                    _TABLE_ROWS_KEY: [],
                }
            )

        table_id = self._class_to_table_id[class_name]
        table = self.tables[table_id]
        row = [fields_dict.get(f) for f in table[_TABLE_FIELDS_KEY]]

        row_key = (table_id, _make_hashable(row))
        existing_idx = self._dedup.get(row_key)
        if existing_idx is not None:
            return {_OBJ_ID_KEY: f"{table_id}:{existing_idx}"}

        idx = len(table[_TABLE_ROWS_KEY])
        table[_TABLE_ROWS_KEY].append(row)
        self._dedup[row_key] = idx
        return {_OBJ_ID_KEY: f"{table_id}:{idx}"}


def _make_collecting_handler(
    collector: _ColumnarCollector,
    columnar_classes: frozenset[str] | None = None,
):
    """Create an ``object_handler`` that collects objects into columnar tables.

    Plugs into ``_transform_for_serialization``'s ``object_handler`` parameter.
    Children are serialized first via ``pack_items`` (which calls back into this
    handler), so by the time we register a row, all nested objects are already
    ``__oid__`` refs.

    When *columnar_classes* is set, only objects whose storage name is in the set
    are columnar-packed.  All others are serialized inline as regular dicts (like
    ``_pack_object``), but still recurse through this handler so their children
    can be columnar-packed.
    """

    def handler(
        obj: SerializableObject,
        wm: WhitelistMap,
        descent_path: str,
    ) -> JsonSerializableValue:
        klass_name = obj.__class__.__name__
        serializer = wm.object_serializers[klass_name]
        fields_dict = dict(serializer.pack_items(obj, wm, handler, descent_path))
        storage_name = cast("str", fields_dict["__class__"])

        if columnar_classes is not None and storage_name not in columnar_classes:
            # Inline — return the full dict just like _pack_object would.
            return fields_dict

        return collector.register(storage_name, fields_dict)

    return handler


###############################################################################
# Columnar unpacking (deserialization)
###############################################################################


def _unpack_columnar(
    val: JsonSerializableValue,
    tables: list[dict[str, Any]],
    whitelist_map: WhitelistMap,
    context: UnpackContext,
    row_cache: dict[str, UnpackedValue],
) -> UnpackedValue:
    """Recursively unpack a columnar-packed value tree.

    Each ``__oid__`` ref is resolved exactly once and cached — subsequent
    references return the same Python object.
    """
    if isinstance(val, list):
        return [_unpack_columnar(item, tables, whitelist_map, context, row_cache) for item in val]

    if isinstance(val, dict):
        if _OBJ_ID_KEY in val:
            oid = cast("str", val[_OBJ_ID_KEY])
            if oid not in row_cache:
                table_id_str, idx_str = oid.rsplit(":", 1)
                table = tables[int(table_id_str)]
                row = table[_TABLE_ROWS_KEY][int(idx_str)]

                obj_dict: dict[str, Any] = {"__class__": table[_TABLE_CLASS_KEY]}
                for field_name, field_val in zip(table[_TABLE_FIELDS_KEY], row):
                    obj_dict[field_name] = _unpack_columnar(
                        field_val, tables, whitelist_map, context, row_cache
                    )
                row_cache[oid] = _unpack_object(obj_dict, whitelist_map, context)
            return row_cache[oid]

        # Non-columnar dict — a plain serdes object or raw mapping. Delegate to
        # _unpack_object which handles __class__ detection and passthrough.
        return _unpack_object(
            {
                k: _unpack_columnar(v, tables, whitelist_map, context, row_cache)
                for k, v in val.items()
            },
            whitelist_map,
            context,
        )

    return val
