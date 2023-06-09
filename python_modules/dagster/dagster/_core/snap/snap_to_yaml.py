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
    """Returns a YAML representation of the default values for the given type snap."""
    return dump_run_config_yaml(default_values_from_type_snap(type_snap, snapshot))


def default_values_from_type_snap(type_snap: ConfigTypeSnap, snapshot: ConfigSchemaSnapshot) -> Any:
    """Given a type snap and a snapshot, returns a dictionary of default values for the type
    snap, recursively assembling a default if the type snap does not have a default value
    explicitly set.
    """
    if not type_snap.fields:
        return {}

    defaults_by_field = {}
    for field_name in type_snap.field_names:
        field = type_snap.get_field(field_name)

        default_value_as_json = field.default_value_as_json_str
        field_snap = (
            snapshot.get_config_snap(field.type_key)
            if snapshot.has_config_snap(field.type_key)
            else None
        )

        # First, we try to get the default value from the field itself
        # this is usually only set for primitive field types with user-supplied defaults
        if default_value_as_json:
            defaults_by_field[field_name] = _safe_json_loads(default_value_as_json)
        # If there is no default value on the field, if the field has child fields, we recurse
        # to assemble the default values for the child fields
        elif field_snap and field_snap.fields:
            defaults_by_field[field_name] = default_values_from_type_snap(field_snap, snapshot)

    return defaults_by_field
