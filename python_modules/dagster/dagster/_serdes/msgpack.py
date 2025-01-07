from functools import partial
from typing import Callable
from .serdes import _LazySerializationWrapper, serialize_value, deserialize_values, deserialize_value

import msgpack


def _msgpack_pack(obj: _LazySerializationWrapper):
    packer = msgpack.Packer()
    return packer.pack_map_pairs(list(obj.items()))

def _msgpack_unpack(packed_message: bytes, object_hook: Callable):
    return msgpack.unpackb(packed_message, object_hook=object_hook)

serialize_value_with_msgpack = partial(serialize_value, json_dumps=_msgpack_pack)
deserialize_value_with_msgpack = partial(deserialize_value, json_loads=_msgpack_unpack)
deserialize_values_with_msgpack = partial(deserialize_values, json_loads=_msgpack_unpack)