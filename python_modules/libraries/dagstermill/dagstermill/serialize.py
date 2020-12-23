from dagster import check, seven
from dagster.core.types.dagster_type import DagsterType, DagsterTypeKind

PICKLE_PROTOCOL = 2


def is_json_serializable(value):
    try:
        seven.json.dumps(value)
        return True
    except TypeError:
        return False


def read_value(dagster_type, value):
    check.inst_param(dagster_type, "dagster_type", DagsterType)
    check.dict_param(value, "value")
    check.invariant(
        list(value.keys()) in [["value"], ["file"]],
        "Malformed value received with keys: {bad_keys}, expected ['value'] or ['file']".format(
            bad_keys="[{keys}]".format(
                keys=", ".join(["'{key}'".format(key=key) for key in value.keys()])
            )
        ),
    )
    if "value" in value:
        return value["value"]
    else:
        return dagster_type.serialization_strategy.deserialize_from_file(value["file"])


def write_value(dagster_type, value, target_file):
    check.inst_param(dagster_type, "dagster_type", DagsterType)
    if (
        dagster_type.kind == DagsterTypeKind.SCALAR or dagster_type.kind == DagsterTypeKind.ANY
    ) and is_json_serializable(value):
        return {"value": value}
    else:
        dagster_type.serialization_strategy.serialize_to_file(value, target_file)
        return {"file": target_file}
