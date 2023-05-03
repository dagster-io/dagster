import json
from typing import Any, Optional

from dagster._config.snap import ConfigSchemaSnapshot, ConfigTypeSnap
from dagster._utils.yaml_utils import dump_run_config_yaml


def _safe_json_loads(json_str: Optional[str]) -> object:
    try:
        return json.loads(json_str) if json_str else None
    except json.JSONDecodeError:
        return None


def default_values_yaml_from_type_snap(
    snapshot: ConfigSchemaSnapshot,
    type_snap: ConfigTypeSnap,
) -> str:
    return dump_run_config_yaml(default_values_from_type_snap(type_snap, snapshot))


def default_values_from_type_snap(type_snap: ConfigTypeSnap, snapshot: ConfigSchemaSnapshot) -> Any:
    defaults_by_field = {}

    for field_name in type_snap.field_names:
        field = type_snap.get_field(field_name)

        # no default placeholder
        default_value = ...

        default_value_as_json = field.default_value_as_json_str
        if default_value_as_json:
            default_value = _safe_json_loads(default_value_as_json)
        if not default_value_as_json and snapshot:
            key = field.type_key
            snap = snapshot.get_config_snap(key)

            if snap.fields:
                default_value = default_values_from_type_snap(snap, snapshot)

        if default_value is not ...:
            defaults_by_field[field_name] = default_value

    return defaults_by_field
