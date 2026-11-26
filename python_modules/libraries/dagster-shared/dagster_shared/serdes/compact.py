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

Decoding produces the same packed value as the legacy format, including the key order of dicts
and serdes objects (sorted, as the legacy format writes with `sort_keys=True`), and unpacks it with
the same object hook, so readers keep their backcompat behavior.

Unlike the legacy format, decoding shares deeply immutable values: a table entry that deserializes
to a scalar, an enum, or a tuple (including NamedTuples and records) or frozenset of deeply
immutable values is reused at every reference, so equal subtrees deserialize to the same Python
object. Other values, such as lists, dicts, sets, dataclasses and records with a list or dict field,
are decoded again at each reference, so mutating a deserialized value never changes another one.
"""

import json
from collections.abc import Callable, Sequence
from enum import Enum
from json.encoder import encode_basestring_ascii  # type: ignore
from typing import Any

COMPACT_SERDES_KEY = "__compact_serdes__"
COMPACT_SERDES_VERSION = 1
# The compact format is written without whitespace and the legacy format with it, so this prefix
# only matches a legacy value written with non-default `separators` whose first key is
# `__compact_serdes__`.
COMPACT_SERDES_PREFIX = f'{{"{COMPACT_SERDES_KEY}":{COMPACT_SERDES_VERSION},"classes":'

_NUMBER_TAG = 0
LIST_TAG = 1
DICT_TAG = 2
_FIRST_CLASS_TAG = 3

# Strings shorter than this are repeated inline rather than referenced, since a reference would not
# be meaningfully shorter.
_MIN_SHARED_STR_LEN = 6

# Containers with more children than this are written top-down rather than as text, along with their
# ancestors up to this depth below the root.
_MIN_STREAMED_CHILDREN = 1000
_MAX_STREAMED_DEPTH = 4


def json_scalar(value: Any) -> Any:
    """Convert a scalar to the exact type `json.loads(json.dumps(value))` would return, e.g. a str
    or int subclass (such as a str or int enum) to its plain value.
    """
    if isinstance(value, str):
        return str.__str__(value)
    if isinstance(value, bool):
        return bool(value)
    if isinstance(value, int):
        return int(value)
    if isinstance(value, float):
        return float(value)
    raise TypeError(f"Object of type {type(value).__name__} is not JSON serializable")


def json_key(key: Any) -> str:
    """Convert a dict key the way `json.dumps` does, so that decoded dicts match the legacy format."""
    if type(key) is str:
        return key
    if isinstance(key, str):
        return str.__str__(key)
    if key is None or isinstance(key, (int, float)):
        return json.dumps(json_scalar(key) if key is not None else None)
    raise TypeError(f"keys must be str, int, float, bool or None, not {type(key).__name__}")


def scalar_key(value: Any) -> tuple[type, Any]:
    """Node key of a non-str JSON scalar. Floats are keyed by their text, so that equal but distinct
    values (`0.0` and `-0.0`) aren't merged.
    """
    tval = type(value)
    return (tval, repr(value)) if tval is float else (tval, value)


# Mark decoded table entries that are not deeply immutable, so not shared between references:
# _FLAT entries are copied at each reference, _MUTABLE ones are decoded again.
_MUTABLE = object()
_FLAT = object()


_SCALAR_TYPES = (str, int, float, Enum)


def _is_shareable(value: Any, shared_ids: set[int]) -> bool:
    """Whether a decoded value is deeply immutable, so that it can be reused at every reference to
    its table entry: scalars, enums, and tuples (including NamedTuples and records) and frozensets
    whose items are deeply immutable. `shared_ids` holds the ids of the values already known to be.
    """
    if value is None or isinstance(value, _SCALAR_TYPES) or id(value) in shared_ids:
        return True
    if isinstance(value, tuple):
        # `@record` classes disallow iteration, but are tuples
        return all(_is_shareable(item, shared_ids) for item in tuple.__iter__(value))
    if isinstance(value, frozenset):
        return all(_is_shareable(item, shared_ids) for item in value)
    return False


def _first(item: tuple[Any, Any]) -> Any:
    return item[0]


def is_compact_serialized(value: str) -> bool:
    return value.startswith(COMPACT_SERDES_PREFIX)


class Encoder:
    """Builds the compact encoding of a value.

    Values are hash-consed into nodes: equal subtrees get the same node id. A node is identified by
    its key, which is also what `dumps` writes:

    * a `str` for strings;
    * `(type, value)` for other scalars (see `scalar_key`);
    * `(tag, *child_node_ids)` for lists, dicts and serdes objects, using the tags of the format.

    Children always get lower ids than their parents, so the nodes are in topological order.
    """

    def __init__(self) -> None:
        self.node_ids: dict[Any, int] = {}
        # Node 0 is a placeholder that is never written, so that node ids are truthy and lookups
        # can be written `node_ids.get(key) or ...`.
        self.nodes: list[Any] = [None]
        self.class_ids: dict[tuple[str, tuple[str, ...]], int] = {}
        self.classes: list[list[Any]] = []

    def intern(self, key: Any) -> int:
        node_id = self.node_ids.get(key)
        if node_id is None:
            node_id = self.node_ids[key] = len(self.nodes)
            self.nodes.append(key)
        return node_id

    def class_tag(self, class_name: str, field_names: tuple[str, ...]) -> int:
        class_key = (class_name, field_names)
        class_id = self.class_ids.get(class_key)
        if class_id is None:
            class_id = self.class_ids[class_key] = len(self.classes)
            self.classes.append([class_name, list(field_names)])
        return _FIRST_CLASS_TAG + class_id

    def add(self, value: Any) -> int:
        """Add a packed (JSON-serializable) value. Accepts what `json.dumps` accepts in a packed
        value: subclasses of JSON types, and tuples as lists.
        """
        tval = type(value)
        if tval is str:
            return self.intern(value)
        if tval is list or tval is tuple:
            return self.intern((LIST_TAG, *[self.add(item) for item in value]))
        if tval is dict:
            class_name = value.get("__class__")
            if type(class_name) is str:
                tag = self.class_tag(class_name, tuple([k for k in value if k != "__class__"]))
                return self.intern(
                    (tag, *[self.add(v) for k, v in value.items() if k != "__class__"])
                )
            return self.add_dict_items(value.items(), self.add)
        if value is None or tval is bool or tval is int or tval is float:
            return self.intern(scalar_key(value))
        if isinstance(value, (list, tuple, dict)):
            return self.add(
                dict(value) if isinstance(value, dict) else list(value)  # ty: ignore[no-matching-overload]
            )
        value = json_scalar(value)
        return self.intern(value if type(value) is str else scalar_key(value))

    def add_dict_items(self, items: Any, add_value: Callable[[Any], int]) -> int:
        """Add a dict that isn't a serdes object, given its items and how to add each value.

        Keys are converted like `json.dumps` does, and sorted like the legacy format (which writes
        with `sort_keys=True`), so that decoded dicts have the same key order.
        """
        # Sorting the original keys raises on mixed key types, like the legacy format does.
        converted = [(json_key(key), value) for key, value in sorted(items, key=_first)]
        intern = self.intern
        return intern(
            (
                DICT_TAG,
                *[
                    node_id
                    for key, value in converted
                    for node_id in (intern(key), add_value(value))
                ],
            )
        )

    def release(self) -> None:
        """Free the state only needed to add values, before writing."""
        self.node_ids = {}

    def dumps(self, root_id: int) -> str:
        """Write the nodes reachable from `root_id`, in the compact format.

        The encoder can't be used afterwards: its state is released while writing.
        """
        self.release()
        nodes = self.nodes
        self.nodes = []
        num_nodes = len(nodes)

        # Find which nodes are referenced by several distinct parents (each distinct parent is
        # written once). Only container keys, which start with an int tag, have children.
        used = bytearray(num_nodes)
        multi = bytearray(num_nodes)
        for key in nodes:
            if type(key) is tuple and type(key[0]) is int:
                for child in key[1:]:
                    if used[child]:
                        multi[child] = 1
                    else:
                        used[child] = 1
        used[root_id] = 1
        streamed = self._find_streamed(nodes, multi, root_id)

        # Text of each node: the index of its value table entry for shared nodes, or its encoding
        # to inline in its parent. Nodes are written in id order, so children come first and table
        # entries only reference earlier entries. Once a node's text is part of its parent's text,
        # it's released unless other parents need it.
        texts: list[Any] = [None] * num_nodes
        table: list[str] = []
        tag_texts = [str(tag) for tag in range(_FIRST_CLASS_TAG + len(self.classes))]
        get_text = texts.__getitem__
        streamed_keys: dict[int, tuple] = {}
        for node_id, key in enumerate(nodes):
            if not used[node_id]:
                continue  # unreachable from the root
            nodes[node_id] = None
            if streamed[node_id]:
                streamed_keys[node_id] = key
                continue
            if type(key) is str:
                text = encode_basestring_ascii(key)
                if multi[node_id] and len(key) >= _MIN_SHARED_STR_LEN:
                    table.append(text)
                    text = str(len(table) - 1)
            elif type(key[0]) is int:
                children = key[1:]
                text = f"[{','.join([tag_texts[key[0]], *map(get_text, children)])}]"
                for child in children:
                    if not multi[child]:
                        texts[child] = None
                if multi[node_id] and children:
                    table.append(text)
                    text = str(len(table) - 1)
            else:
                # non-str scalar: `(type, value)`, with floats as their repr (see `scalar_key`)
                text = json.dumps(float(key[1]) if key[0] is float else key[1])
                if key[0] is int or key[0] is float:
                    text = f"[{_NUMBER_TAG},{text}]"
            texts[node_id] = text
        del nodes

        out: list[str] = []
        write = out.append
        write(
            f'{{"{COMPACT_SERDES_KEY}":{COMPACT_SERDES_VERSION},'
            f'"classes":{json.dumps(self.classes, separators=(",", ":"))},"table":['
        )
        write(",".join(table))
        del table
        write('],"root":')
        # Streamed nodes are written top-down, without building their text.
        stack: list[Any] = [root_id]
        while stack:
            item = stack.pop()
            if type(item) is str:
                write(item)
                continue
            key = streamed_keys.pop(item, None)
            if key is None:
                write(texts[item])
                continue
            write(f"[{tag_texts[key[0]]}")
            stack.append("]")
            for child in reversed(key[1:]):
                stack.append(child)
                stack.append(",")
        write("}")
        del texts, get_text
        return "".join(out)

    @staticmethod
    def _find_streamed(nodes: list[Any], multi: bytearray, root_id: int) -> bytearray:
        """Find the nodes to write top-down rather than as text: containers with many children
        (e.g. the list of all asset nodes) and their ancestors, if they are used once.

        Their text would be about as large as the output, so building it would hold the output
        twice.
        """
        streamed = bytearray(len(nodes))

        # Large containers are close to the root, so the search is shallow.
        def search(node_id: int, depth: int) -> bool:
            key = nodes[node_id]
            if type(key) is not tuple or type(key[0]) is not int or multi[node_id]:
                return False
            if len(key) > _MIN_STREAMED_CHILDREN:
                streamed[node_id] = 1
                return True
            found = False
            if depth:
                for child in key[1:]:
                    if search(child, depth - 1):
                        found = True
            if found:
                streamed[node_id] = 1
            return found

        search(root_id, _MAX_STREAMED_DEPTH)
        return streamed


def dumps_compact(packed_value: Any) -> str:
    """Write a packed (JSON-serializable) value in the compact format."""
    encoder = Encoder()
    return encoder.dumps(encoder.add(packed_value))


def loads_compact(value: str, object_hook: Callable[[dict], Any]) -> Any:
    """Read a value written by `dumps_compact`.

    `object_hook` is applied bottom-up to every dict of the packed value, like `json.loads`.
    """
    envelope = json.loads(value)
    version = envelope.get(COMPACT_SERDES_KEY)
    if version != COMPACT_SERDES_VERSION:
        raise ValueError(f"Unsupported compact serdes version {version}")
    # Fields are passed to the object hook in sorted order, as the legacy format writes them with
    # `sort_keys=True`: (class name, [(field name, position in the entry), ...]).
    classes: Sequence[tuple[str, Sequence[tuple[str, int]]]] = [
        (name, sorted((field, index + 1) for index, field in enumerate(fields)))
        for name, fields in envelope["classes"]
    ]
    table: list[Any] = envelope["table"]
    # Decoded table entries, by index. Values that are not deeply immutable must not be shared
    # between references, so their entries are replaced by a marker and decoded again (or copied)
    # at each reference.
    decoded: list[Any] = []
    # Plain lists and dicts whose items are all shared, by index. A shallow copy of their first
    # decoding is the same as decoding them again.
    flat: dict[int, Any] = {}

    def ref(index: int) -> Any:
        value = decoded[index]
        if value is _FLAT:
            return flat[index].copy()
        if value is _MUTABLE:
            return decode(table[index])
        return value

    def decode(encoded: Any) -> Any:
        tval = type(encoded)
        if tval is int:
            return ref(encoded)
        if tval is not list:
            return encoded
        tag = encoded[0]
        # Most items are strings, None, bools or references to shared entries: they are handled
        # inline rather than by a recursive call.
        if tag >= _FIRST_CLASS_TAG:
            class_name, fields = classes[tag - _FIRST_CLASS_TAG]
            obj: dict[str, Any] = {"__class__": class_name}
            for field, index in fields:
                item = encoded[index]
                titem = type(item)
                if titem is int:
                    value = decoded[item]
                    obj[field] = (
                        value if value is not _MUTABLE and value is not _FLAT else ref(item)
                    )
                elif titem is list:
                    obj[field] = decode(item)
                else:
                    obj[field] = item
            return object_hook(obj)
        if tag == LIST_TAG:
            out = []
            append = out.append
            for item in encoded[1:]:
                titem = type(item)
                if titem is int:
                    value = decoded[item]
                    append(value if value is not _MUTABLE and value is not _FLAT else ref(item))
                elif titem is list:
                    append(decode(item))
                else:
                    append(item)
            return out
        if tag == DICT_TAG:
            items = encoded[1:]
            return object_hook(
                {decode(items[i]): decode(items[i + 1]) for i in range(0, len(items), 2)}
            )
        if tag == _NUMBER_TAG:
            return encoded[1]
        raise ValueError(f"Unexpected compact serdes tag {tag}")

    def is_flat(entry: list[Any], value: Any) -> bool:
        """Whether a decoded list or dict entry is the same as its shallow copy would be if it was
        decoded again: all of its items are scalars, numbers or shared entries.
        """
        tag = entry[0]
        if tag == DICT_TAG:
            # The object hook can turn a dict into another value, e.g. a set.
            if type(value) is not dict or len(value) * 2 != len(entry) - 1:
                return False
        elif tag != LIST_TAG or type(value) is not list:
            return False
        for item in entry[1:]:
            titem = type(item)
            if titem is int:
                if decoded[item] is _MUTABLE or decoded[item] is _FLAT:
                    return False
            elif titem is list and item[0] != _NUMBER_TAG:
                return False
        return True

    # Entries only reference earlier entries, so each one can be decoded once in order.
    shared_ids: set[int] = set()
    for index, entry in enumerate(table):
        value = decode(entry)
        if _is_shareable(value, shared_ids):
            shared_ids.add(id(value))
        elif is_flat(entry, value):
            flat[index] = value
            value = _FLAT
        else:
            value = _MUTABLE
        decoded.append(value)
    root = decode(envelope["root"])
    return root
