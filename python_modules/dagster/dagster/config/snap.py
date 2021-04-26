from collections import namedtuple
from typing import Any

from dagster import check
from dagster.serdes import whitelist_for_serdes

from .config_type import ConfigScalarKind, ConfigType, ConfigTypeKind
from .field import Field


def get_recursive_type_keys(config_type_snap, config_schema_snapshot):
    check.inst_param(config_type_snap, "config_type_snap", ConfigTypeSnap)
    check.inst_param(config_schema_snapshot, "config_schema_snapshot", ConfigSchemaSnapshot)
    result_keys = set()
    for type_key in config_type_snap.get_child_type_keys():
        result_keys.add(type_key)
        for recurse_key in get_recursive_type_keys(
            config_schema_snapshot.get_config_snap(type_key), config_schema_snapshot
        ):
            result_keys.add(recurse_key)
    return result_keys


@whitelist_for_serdes
class ConfigSchemaSnapshot(namedtuple("_ConfigSchemaSnapshot", "all_config_snaps_by_key")):
    def __new__(cls, all_config_snaps_by_key):
        return super(ConfigSchemaSnapshot, cls).__new__(
            cls,
            all_config_snaps_by_key=check.dict_param(
                all_config_snaps_by_key,
                "all_config_snaps_by_key",
                key_type=str,
                value_type=ConfigTypeSnap,
            ),
        )

    @property
    def all_config_keys(self):
        return list(self.all_config_snaps_by_key.keys())

    def get_config_snap(self, key):
        check.str_param(key, "key")
        return self.all_config_snaps_by_key[key]

    def has_config_snap(self, key):
        check.str_param(key, "key")
        return key in self.all_config_snaps_by_key


@whitelist_for_serdes
class ConfigTypeSnap(
    namedtuple(
        "_ConfigTypeSnap",
        "kind key given_name description "
        "type_param_keys "  # only valid for closed generics (Set, Tuple, List, Optional)
        "enum_values "  # only valid for enums
        "fields "  # only valid for dicts and selectors
        "scalar_kind",  # only valid for scalars
    )
):
    # serdes log
    # * Adding scalar_kind
    def __new__(
        cls,
        kind,
        key,
        given_name,
        description,
        type_param_keys,
        enum_values,
        fields,
        scalar_kind=None,  # Old version of object will not have this property
    ):
        return super(ConfigTypeSnap, cls).__new__(
            cls,
            kind=check.inst_param(kind, "kind", ConfigTypeKind),
            key=check.str_param(key, "key"),
            given_name=check.opt_str_param(given_name, "given_name"),
            type_param_keys=None
            if type_param_keys is None
            else check.list_param(type_param_keys, "type_param_keys", of_type=str),
            enum_values=None
            if enum_values is None
            else check.list_param(enum_values, "enum_values", of_type=ConfigEnumValueSnap),
            fields=None
            if fields is None
            else sorted(
                check.list_param(fields, "field", of_type=ConfigFieldSnap), key=lambda ct: ct.name
            ),
            description=check.opt_str_param(description, "description"),
            scalar_kind=check.opt_inst_param(scalar_kind, "scalar_kind", ConfigScalarKind),
        )

    @property
    def inner_type_key(self):
        # valid for Noneable and Array
        check.invariant(self.kind == ConfigTypeKind.NONEABLE or self.kind == ConfigTypeKind.ARRAY)
        check.invariant(len(self.type_param_keys) == 1)
        return self.type_param_keys[0]

    @property
    def scalar_type_key(self):
        check.invariant(self.kind == ConfigTypeKind.SCALAR_UNION)
        return self.type_param_keys[0]

    @property
    def non_scalar_type_key(self):
        check.invariant(self.kind == ConfigTypeKind.SCALAR_UNION)
        return self.type_param_keys[1]

    def _get_field(self, name):
        check.str_param(name, "name")
        check.invariant(ConfigTypeKind.has_fields(self.kind))

        for f in self.fields:
            if f.name == name:
                return f

        return None

    def get_field(self, name):
        field = self._get_field(name)
        if not field:
            check.failed("Field {name} not found".format(name=name))
        return field

    def has_field(self, name):
        return bool(self._get_field(name))

    @property
    def field_names(self):
        return [fs.name for fs in self.fields]

    def get_child_type_keys(self):
        if ConfigTypeKind.is_closed_generic(self.kind):
            return self.type_param_keys
        elif ConfigTypeKind.has_fields(self.kind):
            return [field.type_key for field in self.fields]
        else:
            return []

    def has_enum_value(self, value):
        check.invariant(self.kind == ConfigTypeKind.ENUM)
        for enum_value in self.enum_values:
            if enum_value.value == value:
                return True
        return False


@whitelist_for_serdes
class ConfigEnumValueSnap(namedtuple("_ConfigEnumValueSnap", "value description")):
    def __new__(cls, value, description):
        return super(ConfigEnumValueSnap, cls).__new__(
            cls,
            value=check.str_param(value, "value"),
            description=check.opt_str_param(description, "description"),
        )


@whitelist_for_serdes
class ConfigFieldSnap(
    namedtuple(
        "_ConfigFieldSnap",
        "name type_key is_required default_provided default_value_as_json_str description",
    )
):
    def __new__(
        cls, name, type_key, is_required, default_provided, default_value_as_json_str, description
    ):
        return super(ConfigFieldSnap, cls).__new__(
            cls,
            name=check.opt_str_param(name, "name"),
            type_key=check.str_param(type_key, "type_key"),
            is_required=check.bool_param(is_required, "is_required"),
            default_provided=check.bool_param(default_provided, "default_provided"),
            default_value_as_json_str=check.opt_str_param(
                default_value_as_json_str, "default_value_as_json_str"
            ),
            description=check.opt_str_param(description, "description"),
        )


def snap_from_field(name, field):
    check.str_param(name, "name")
    check.inst_param(field, "field", Field)
    return ConfigFieldSnap(
        name=name,
        type_key=field.config_type.key,
        is_required=field.is_required,
        default_provided=field.default_provided,
        default_value_as_json_str=field.default_value_as_json_str
        if field.default_provided
        else None,
        description=field.description,
    )


def snap_from_config_type(config_type):
    check.inst_param(config_type, "config_type", ConfigType)
    return ConfigTypeSnap(
        key=config_type.key,
        given_name=config_type.given_name,
        kind=config_type.kind,
        description=config_type.description,
        type_param_keys=[ct.key for ct in config_type.type_params] if config_type.type_params
        # jam scalar union types into type_param_keys
        else [config_type.scalar_type.key, config_type.non_scalar_type.key]
        if config_type.kind == ConfigTypeKind.SCALAR_UNION
        else None,
        enum_values=[
            ConfigEnumValueSnap(ev.config_value, ev.description) for ev in config_type.enum_values
        ]
        if config_type.kind == ConfigTypeKind.ENUM
        else None,
        fields=[snap_from_field(name, field) for name, field in config_type.fields.items()]
        if ConfigTypeKind.has_fields(config_type.kind)
        else None,
        scalar_kind=config_type.scalar_kind if config_type.kind == ConfigTypeKind.SCALAR else None,
    )


def minimal_config_for_type_snap(
    config_schema_snap: ConfigSchemaSnapshot, config_type_snap: ConfigTypeSnap
) -> Any:

    check.inst_param(config_schema_snap, "config_schema_snap", ConfigSchemaSnapshot)
    check.inst_param(config_type_snap, "config_type_snap", ConfigTypeSnap)

    if ConfigTypeKind.has_fields(config_type_snap.kind):
        default_dict = {}
        if ConfigTypeKind.is_selector(config_type_snap.kind):
            return "<selector>"
        for field in config_type_snap.fields:
            if not field.is_required:
                continue

            default_dict[field.name] = minimal_config_for_type_snap(
                config_schema_snap, config_schema_snap.get_config_snap(field.type_key)
            )
        return default_dict
    elif config_type_snap.kind == ConfigTypeKind.ANY:
        return "AnyType"
    elif config_type_snap.kind == ConfigTypeKind.SCALAR:
        defaults = {"String": "...", "Int": 0, "Float": 0.0, "Bool": True}

        return defaults.get(config_type_snap.given_name, "<unknown>")
    elif config_type_snap.kind == ConfigTypeKind.ARRAY:
        return []
    elif config_type_snap.kind == ConfigTypeKind.ENUM:
        return "|".join(sorted(map(lambda v: v.config_value, config_type_snap.enum_values)))
    elif config_type_snap.kind == ConfigTypeKind.SCALAR_UNION:
        return minimal_config_for_type_snap(
            config_schema_snap,
            config_schema_snap.get_config_snap(config_type_snap.type_param_keys[0]),
        )
    else:
        return "<unknown>"
