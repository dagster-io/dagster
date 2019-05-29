from enum import Enum

from dagster import check, RuntimeType, seven
from dagster.core.types.marshal import PickleSerializationStrategy


PICKLE_PROTOCOL = 2


def is_json_serializable(value):
    try:
        seven.json.dumps(value)
        return True
    except TypeError:
        return False


def read_value(runtime_type, value):
    check.inst_param(runtime_type, 'runtime_type', RuntimeType)
    if runtime_type.is_scalar:
        return value
    elif runtime_type.is_any and is_json_serializable(value):
        return value
    else:
        return runtime_type.serialization_strategy.deserialize_from_file(value)


def write_value(runtime_type, value, target_file):
    check.inst_param(runtime_type, 'runtime_type', RuntimeType)
    if runtime_type.is_scalar:
        return value
    elif runtime_type.is_any and is_json_serializable(value):
        return value
    else:
        runtime_type.serialization_strategy.serialize_to_file(value, target_file)
        return target_file


class SerializableRuntimeType(Enum):
    SCALAR = 'scalar'
    ANY = 'any'
    PICKLE_SERIALIZABLE = 'pickle'
    JSON_SERIALIZABLE = 'json'
    NONE = ''


def input_name_serialization_enum(runtime_type, value):
    runtime_type_enum = runtime_type_to_enum(runtime_type)

    if runtime_type_enum == SerializableRuntimeType.ANY:
        if is_json_serializable(value):
            return SerializableRuntimeType.JSON_SERIALIZABLE
        else:
            return SerializableRuntimeType.NONE

    return runtime_type_enum


def output_name_serialization_enum(runtime_type):
    return runtime_type_to_enum(runtime_type)


def dict_to_enum(runtime_type_dict):
    return {k: SerializableRuntimeType(v) for k, v in runtime_type_dict.items()}


def runtime_type_to_enum(runtime_type):
    if runtime_type.is_scalar:
        return SerializableRuntimeType.SCALAR
    elif runtime_type.is_any:
        return SerializableRuntimeType.ANY
    elif runtime_type.serialization_strategy and isinstance(
        runtime_type.serialization_strategy, PickleSerializationStrategy
    ):
        return SerializableRuntimeType.PICKLE_SERIALIZABLE

    return SerializableRuntimeType.NONE
