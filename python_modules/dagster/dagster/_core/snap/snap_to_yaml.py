import json
from typing import Optional

from dagster._config.snap import ConfigTypeSnap
from dagster._utils.yaml_utils import dump_run_config_yaml


def _safe_json_loads(json_str: Optional[str]) -> object:
    try:
        return json.loads(json_str) if json_str else None
    except json.JSONDecodeError:
        return None


def default_values_yaml_from_type_snap(type_snap: ConfigTypeSnap) -> str:
    defaults_by_field = {}

    for field_name in type_snap.field_names:
        default_value_as_json = type_snap.get_field(field_name).default_value_as_json_str
        default_value = _safe_json_loads(default_value_as_json)
        defaults_by_field[field_name] = default_value

    return dump_run_config_yaml(defaults_by_field)
