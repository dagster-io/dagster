from dagster import check, seven
from dagster.core.types.dagster_type import DagsterType

PICKLE_PROTOCOL = 2


def is_json_serializable(value):
    try:
        seven.json.dumps(value)
        return True
    except TypeError:
        return False


def read_value(runtime_type, value):
    check.inst_param(runtime_type, 'runtime_type', DagsterType)
    if runtime_type.is_scalar:
        return value
    elif runtime_type.is_any and is_json_serializable(value):
        return value
    else:
        return runtime_type.serialization_strategy.deserialize_from_file(value)


def write_value(runtime_type, value, target_file):
    check.inst_param(runtime_type, 'runtime_type', DagsterType)
    if runtime_type.is_scalar:
        return value
    elif runtime_type.is_any and is_json_serializable(value):
        return value
    else:
        runtime_type.serialization_strategy.serialize_to_file(value, target_file)
        return target_file
