from enum import Enum
from functools import partial
from typing import Callable

import cbor2
import msgpack

from dagster._serdes.serdes import (
    JsonSerializableValue,
    _pack_object,
    deserialize_value,
    deserialize_values,
    serialize_value,
)


class MsgPackExtType(int, Enum):
    LARGE_INT = 1


def _msgpack_pack_compat(obj):
    if isinstance(obj, int) and (obj > 2**64 - 1 or obj < -(2**63)):
        return msgpack.ExtType(
            MsgPackExtType.LARGE_INT, obj.to_bytes(16, byteorder="big", signed=True)
        )
    return obj


def _msgpack_unpack_compat(code, data):
    if code == MsgPackExtType.LARGE_INT:
        return int.from_bytes(data, byteorder="big", signed=True)
    return msgpack.ExtType(code, data)


def _msgpack_pack(obj: JsonSerializableValue):
    return msgpack.packb(obj, default=_msgpack_pack_compat, use_bin_type=True)


def _msgpack_unpack(packed_message: bytes, object_hook: Callable):
    return msgpack.unpackb(
        packed_message,
        ext_hook=_msgpack_unpack_compat,
        object_hook=object_hook,
    )


serialize_value_with_msgpack = partial(
    serialize_value, json_dumps=_msgpack_pack, object_handler=_pack_object
)
deserialize_value_with_msgpack = partial(deserialize_value, json_loads=_msgpack_unpack)
deserialize_values_with_msgpack = partial(deserialize_values, json_loads=_msgpack_unpack)


def _cbor_pack(obj: JsonSerializableValue):
    return cbor2.dumps(obj)


def _cbor_unpack(packed_message: bytes, object_hook: Callable):
    return cbor2.loads(packed_message, object_hook=lambda _, obj: object_hook(obj))


serialize_value_with_cbor = partial(
    serialize_value, json_dumps=_cbor_pack, object_handler=_pack_object
)
deserialize_value_with_cbor = partial(deserialize_value, json_loads=_cbor_unpack)
deserialize_values_with_cbor = partial(deserialize_values, json_loads=_cbor_unpack)
