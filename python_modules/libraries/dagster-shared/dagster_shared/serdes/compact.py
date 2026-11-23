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
from json.encoder import encode_basestring_ascii  # type: ignore
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

# Containers with more children than this are written top-down rather than as text, along with their
# ancestors up to this depth below the root.
_MIN_STREAMED_CHILDREN = 1000
_MAX_STREAMED_DEPTH = 4


def json_key(key: Any) -> str:
    """Convert a dict key the way `json.dumps` does, so that decoded dicts match the legacy format."""
    if type(key) is str:
        return key
    if key is None or type(key) in (bool, int, float):
        return json.dumps(key)
    if isinstance(key, str):
        return str(key)
    raise TypeError(f"keys must be str, int, float, bool or None, not {type(key).__name__}")


def is_compact_serialized(value: str) -> bool:
    return value.startswith(COMPACT_SERDES_PREFIX)


class _Encoder:
    """Builds the compact encoding of a value.

    Values are hash-consed into nodes: equal subtrees get the same node id. A node is identified by
    its key, which is also what `dumps` writes:

    * a `str` for strings;
    * `(type, value)` for other scalars;
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
        """Add a packed (JSON-serializable) value."""
        tval = type(value)
        if tval is str:
            return self.intern(value)
        if tval is list:
            return self.intern((_LIST_TAG, *[self.add(item) for item in value]))
        if tval is dict:
            class_name = value.get("__class__")
            if type(class_name) is str:
                tag = self.class_tag(class_name, tuple([k for k in value if k != "__class__"]))
                return self.intern(
                    (tag, *[self.add(v) for k, v in value.items() if k != "__class__"])
                )
            return self.intern(
                (
                    _DICT_TAG,
                    *[
                        node_id
                        for k, v in value.items()
                        for node_id in (self.intern(json_key(k)), self.add(v))
                    ],
                )
            )
        if value is None or tval is bool or tval is int or tval is float:
            return self.intern((tval, value))
        raise TypeError(f"Unexpected packed value type {tval}")

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
                text = json.dumps(key[1])
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
    encoder = _Encoder()
    return encoder.dumps(encoder.add(packed_value))


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
