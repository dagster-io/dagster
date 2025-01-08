from functools import partial
from typing import Callable

import msgpack

from .serdes import (
    JsonSerializableValue,
    _pack_object,
    deserialize_value,
    deserialize_values,
    serialize_value,
)


def _msgpack_pack(obj: JsonSerializableValue):
    packer = msgpack.Packer()
    return packer.pack(obj)


def _msgpack_unpack(packed_message: bytes, object_hook: Callable):
    return msgpack.unpackb(packed_message, object_hook=object_hook)


serialize_value_with_msgpack = partial(
    serialize_value, json_dumps=_msgpack_pack, object_handler=_pack_object
)
deserialize_value_with_msgpack = partial(deserialize_value, json_loads=_msgpack_unpack)
deserialize_values_with_msgpack = partial(
    deserialize_values, json_loads=_msgpack_unpack
)
