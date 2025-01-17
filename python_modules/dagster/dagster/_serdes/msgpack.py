from enum import Enum
from functools import partial
from typing import Callable

import amazon.ion.simpleion as ion
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
    SET = 2
    FROZENSET = 3
    ENUM = 4
    CLASS = 5
    MAPPING_ITEMS = 6


class SerdesSpecialKeys(str, Enum):
    SET = "__set__"
    FROZENSET = "__frozenset__"
    ENUM = "__enum__"
    MAPPING_ITEMS = "__mapping_items__"
    CLASS = "__class__"


def _msgpack_pack_compat(obj):
    if isinstance(obj, int) and (obj > 2**64 - 1 or obj < -(2**63)):
        return msgpack.ExtType(
            MsgPackExtType.LARGE_INT, obj.to_bytes(16, byteorder="big", signed=True)
        )
    elif isinstance(obj, dict):
        if {SerdesSpecialKeys.SET} == obj.keys():
            return msgpack.ExtType(MsgPackExtType.SET, _msgpack_pack(obj[SerdesSpecialKeys.SET]))
        elif {SerdesSpecialKeys.FROZENSET} == obj.keys():
            return msgpack.ExtType(
                MsgPackExtType.FROZENSET, _msgpack_pack(obj[SerdesSpecialKeys.FROZENSET])
            )
        elif {SerdesSpecialKeys.ENUM} == obj.keys():
            return msgpack.ExtType(
                MsgPackExtType.ENUM,
                obj[SerdesSpecialKeys.ENUM].encode("utf-8"),
            )
        elif {SerdesSpecialKeys.CLASS} == obj.keys():
            return msgpack.ExtType(
                MsgPackExtType.CLASS,
                obj[SerdesSpecialKeys.CLASS].encode("utf-8"),
            )
    return obj


def _msgpack_unpack_compat(code, data):
    if code == MsgPackExtType.LARGE_INT:
        return int.from_bytes(data, byteorder="big", signed=True)
    elif code == MsgPackExtType.SET:
        return {"__set__": data}
    elif code == MsgPackExtType.FROZENSET:
        return {"__frozenset__": data}
    elif code == MsgPackExtType.ENUM:
        return {"__enum__": data}
    elif code == MsgPackExtType.CLASS:
        return {"__class__": data}
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


def traverse_and_transform(obj, object_hook):
    if isinstance(obj, dict):
        # First transform the dictionary contents recursively
        transformed_dict = {k: traverse_and_transform(v, object_hook) for k, v in obj.items()}
        # Then apply the object hook to the transformed dictionary
        return object_hook(transformed_dict)
    elif isinstance(obj, list):
        # Transform each element of the list recursively
        return [traverse_and_transform(item, object_hook) for item in obj]
    else:
        # Base case: return primitive values as-is
        return obj


def _ion_pack(obj: JsonSerializableValue):
    return ion.dumps(obj)


def _ion_unpack(packed_message: bytes, object_hook: Callable):
    return traverse_and_transform(
        ion.loads(
            packed_message,
            value_model=ion.IonPyValueModel.MAY_BE_BARE | ion.IonPyValueModel.STRUCT_AS_STD_DICT,
        ),
        object_hook,
    )


serialize_value_with_ion = partial(
    serialize_value, json_dumps=_ion_pack, object_handler=_pack_object
)
deserialize_value_with_ion = partial(deserialize_value, json_loads=_ion_unpack)
deserialize_values_with_ion = partial(deserialize_values, json_loads=_ion_unpack)
