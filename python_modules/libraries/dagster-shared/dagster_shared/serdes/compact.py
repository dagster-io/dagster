"""Compact serialization format for large serdes values.

The legacy format writes the packed value as plain JSON: every serdes object is a JSON object
that repeats its class name and all of its field names, and every repeated value (asset keys,
partitions definitions, metadata entries, descriptions, ...) is written out in full each time it
appears. For large repository snapshots this repetition dominates the payload.

The compact format writes the same packed value with two changes:

* Each serdes object is a JSON array `[tag, field_value, ...]`. The tag indexes a class table that
  stores the class name and field names once.
* Values are hash-consed: identical subtrees are stored once in a value table and referenced by
  index. A table entry can only reference earlier entries.

The envelope is a JSON object `{"__compact_serdes__": 1, "classes": [...], "table": [...],
"root": value}`. Within it, values are encoded as:

* `str`, `true`, `false`, `null`: literal;
* a non-negative integer: a reference to an entry of the value table;
* `[0, number]`: a literal int or float;
* `[1, item, ...]`: a list;
* `[2, key, value, ...]`: a dict that is not a serdes object (keys are encoded values too);
* `[3 + i, field_value, ...]`: a serdes object of class `classes[i]`, whose entry is
  `[class_name, [field_name, ...]]`.

Decoding produces exactly the packed value of the legacy format and unpacks it with the same
object hook, so readers keep their backcompat behavior. Decoded table entries are reused at every
reference, so equal subtrees deserialize to the same Python object.
"""

import json
from collections.abc import Callable, Sequence
from typing import Any

COMPACT_SERDES_KEY = "__compact_serdes__"
COMPACT_SERDES_VERSION = 1
COMPACT_SERDES_PREFIX = '{"' + COMPACT_SERDES_KEY + '":'

_NUMBER_TAG = 0
_LIST_TAG = 1
_DICT_TAG = 2
_FIRST_CLASS_TAG = 3

# Strings shorter than this are repeated inline rather than referenced, since a reference would not
# be meaningfully shorter.
_MIN_SHARED_STR_LEN = 6

_LIST_KIND = 0
_DICT_KIND = 1
_OBJECT_KIND = 2
_SCALAR_KIND = 3


def is_compact_serialized(value: str) -> bool:
    return value.startswith(COMPACT_SERDES_PREFIX)


class _Encoder:
    def __init__(self) -> None:
        # Hash-consed nodes. A node is identified by its kind and the ids of its children (or by
        # its value for scalars), so equal subtrees get the same id.
        self.node_ids: dict[Any, int] = {}
        self.kinds: list[int] = []
        self.payloads: list[Any] = []
        self.ref_counts: list[int] = []
        self.class_ids: dict[tuple[str, tuple[str, ...]], int] = {}
        self.classes: list[list[Any]] = []

    def _node(self, key: Any, kind: int, payload: Any, children: tuple[int, ...]) -> int:
        node_ids = self.node_ids
        node_id = node_ids.get(key)
        if node_id is None:
            node_id = len(self.kinds)
            node_ids[key] = node_id
            self.kinds.append(kind)
            self.payloads.append(payload)
            self.ref_counts.append(0)
            # children are only counted once per distinct parent, since each distinct parent is
            # written once
            ref_counts = self.ref_counts
            for child in children:
                ref_counts[child] += 1
        return node_id

    def add(self, value: Any) -> int:
        tval = type(value)
        if tval is str:
            node_id = self.node_ids.get(value)
            if node_id is None:
                node_id = self._node(value, _SCALAR_KIND, value, ())
            return node_id
        if tval is list:
            add = self.add
            children = tuple([add(item) for item in value])
            return self._node((_LIST_KIND, children), _LIST_KIND, children, children)
        if tval is dict:
            add = self.add
            class_name = value.get("__class__")
            if type(class_name) is str:
                field_names = tuple(value)
                class_key = (class_name, field_names)
                class_id = self.class_ids.get(class_key)
                if class_id is None:
                    class_id = len(self.classes)
                    self.class_ids[class_key] = class_id
                    self.classes.append([class_name, [k for k in field_names if k != "__class__"]])
                children = tuple([add(v) for k, v in value.items() if k != "__class__"])
                return self._node(
                    (_OBJECT_KIND, class_id, children),
                    _OBJECT_KIND,
                    (class_id, children),
                    children,
                )
            children = tuple([node_id for k, v in value.items() for node_id in (add(k), add(v))])
            return self._node((_DICT_KIND, children), _DICT_KIND, children, children)
        if value is None or tval is bool or tval is int or tval is float:
            return self._node((tval, value), _SCALAR_KIND, value, ())
        raise TypeError(f"Unexpected packed value type {tval}")

    def _shared(self, node_id: int) -> bool:
        # Shared nodes are written once in the value table and referenced by index elsewhere.
        # Small values are cheaper to repeat inline than to reference.
        if self.ref_counts[node_id] < 2:
            return False
        kind = self.kinds[node_id]
        payload = self.payloads[node_id]
        if kind == _SCALAR_KIND:
            return type(payload) is str and len(payload) >= _MIN_SHARED_STR_LEN
        if kind == _OBJECT_KIND:
            return True
        return len(payload) > 0

    def encode(self, root_id: int) -> dict[str, Any]:
        kinds, payloads = self.kinds, self.payloads
        shared = [self._shared(node_id) for node_id in range(len(kinds))]
        table: list[Any] = []
        table_index: dict[int, int] = {}

        def emit(node_id: int) -> Any:
            index = table_index.get(node_id)
            if index is not None:
                return index
            kind = kinds[node_id]
            payload = payloads[node_id]
            if kind == _SCALAR_KIND:
                tval = type(payload)
                body = [_NUMBER_TAG, payload] if tval is int or tval is float else payload
            elif kind == _OBJECT_KIND:
                class_id, children = payload
                body = [_FIRST_CLASS_TAG + class_id, *[emit(c) for c in children]]
            else:
                tag = _LIST_TAG if kind == _LIST_KIND else _DICT_TAG
                body = [tag, *[emit(c) for c in payload]]
            if shared[node_id]:
                index = len(table)
                table.append(body)
                table_index[node_id] = index
                return index
            return body

        root = emit(root_id)
        return {
            COMPACT_SERDES_KEY: COMPACT_SERDES_VERSION,
            "classes": self.classes,
            "table": table,
            "root": root,
        }


def dumps_compact(packed_value: Any, **json_kwargs: Any) -> str:
    """Write a packed (JSON-serializable) value in the compact format."""
    encoder = _Encoder()
    root_id = encoder.add(packed_value)
    envelope = encoder.encode(root_id)
    json_kwargs.setdefault("separators", (",", ":"))
    return json.dumps(envelope, **json_kwargs)


def loads_compact(value: str, object_hook: Callable[[dict], Any], expand: bool = False) -> Any:
    """Read a value written by `dumps_compact`.

    `object_hook` is applied bottom-up to every dict of the packed value, like `json.loads`. With
    `expand=True`, every reference is decoded separately instead of reusing table entries, so that
    no Python object is shared between references.
    """
    envelope = json.loads(value)
    version = envelope.get(COMPACT_SERDES_KEY)
    if version != COMPACT_SERDES_VERSION:
        raise ValueError(f"Unsupported compact serdes version {version}")
    classes: Sequence[tuple[str, Sequence[str]]] = [
        (name, fields) for name, fields in envelope["classes"]
    ]
    table: list[Any] = envelope["table"]
    decoded: list[Any] = []

    def decode(encoded: Any) -> Any:
        tval = type(encoded)
        if tval is int:
            return decode(table[encoded]) if expand else decoded[encoded]
        if tval is not list:
            return encoded
        tag = encoded[0]
        if tag >= _FIRST_CLASS_TAG:
            class_name, fields = classes[tag - _FIRST_CLASS_TAG]
            obj: dict[str, Any] = {"__class__": class_name}
            for field, item in zip(fields, encoded[1:]):
                obj[field] = decode(item)
            return object_hook(obj)
        if tag == _LIST_TAG:
            return [decode(item) for item in encoded[1:]]
        if tag == _DICT_TAG:
            items = encoded[1:]
            return object_hook(
                {decode(items[i]): decode(items[i + 1]) for i in range(0, len(items), 2)}
            )
        if tag == _NUMBER_TAG:
            return encoded[1]
        raise ValueError(f"Unexpected compact serdes tag {tag}")

    if not expand:
        # entries only reference earlier entries, so each one can be decoded once in order
        for entry in table:
            decoded.append(decode(entry))  # noqa: PERF401
    return decode(envelope["root"])
