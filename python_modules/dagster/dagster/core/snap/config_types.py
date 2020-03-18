from collections import namedtuple

from dagster import check
from dagster.config.config_type import ConfigType, ConfigTypeKind
from dagster.config.field import Field
from dagster.core.definitions.pipeline import PipelineDefinition
from dagster.core.serdes import whitelist_for_serdes
from dagster.utils import merge_dicts


def build_config_schema_snapshot(pipeline_def):
    check.inst_param(pipeline_def, 'pipeline_def', PipelineDefinition)
    all_config_snaps_by_key = {}
    for mode in pipeline_def.available_modes:
        environment_schema = pipeline_def.get_environment_schema(mode)
        all_config_snaps_by_key = merge_dicts(
            all_config_snaps_by_key,
            {ct.key: snap_from_config_type(ct) for ct in environment_schema.all_config_types()},
        )

    return ConfigSchemaSnapshot(all_config_snaps_by_key)


@whitelist_for_serdes
class ConfigSchemaSnapshot(namedtuple('_ConfigSchemaSnapshot', 'all_config_snaps_by_key')):
    def __new__(cls, all_config_snaps_by_key):
        return super(ConfigSchemaSnapshot, cls).__new__(
            cls,
            all_config_snaps_by_key=check.dict_param(
                all_config_snaps_by_key,
                'all_config_snaps_by_key',
                key_type=str,
                value_type=ConfigTypeSnap,
            ),
        )

    def get_config_snap(self, key):
        check.str_param(key, 'key')
        return self.all_config_snaps_by_key[key]


@whitelist_for_serdes
class ConfigTypeSnap(
    namedtuple(
        '_ConfigTypeSnap',
        'kind key given_name description '
        'type_param_keys '  # only valid for closed generics (Set, Tuple, List, Optional)
        'enum_values '  # only valid for enums
        'fields',  # only valid for dicts and selectors
    )
):
    def __new__(
        cls, kind, key, given_name, type_param_keys, enum_values, fields, description,
    ):
        return super(ConfigTypeSnap, cls).__new__(
            cls,
            kind=check.inst_param(kind, 'kind', ConfigTypeKind),
            key=check.str_param(key, 'key'),
            given_name=check.opt_str_param(given_name, 'given_name'),
            type_param_keys=None
            if type_param_keys is None
            else check.list_param(type_param_keys, 'type_param_keys', of_type=str),
            enum_values=None
            if enum_values is None
            else check.list_param(enum_values, 'enum_values', of_type=ConfigEnumValueSnap),
            fields=None
            if fields is None
            else check.list_param(fields, 'field', of_type=ConfigFieldSnap),
            description=check.opt_str_param(description, 'description'),
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

    def get_field(self, name):
        check.str_param(name, 'name')
        check.invariant(ConfigTypeKind.has_fields(self.kind))

        for f in self.fields:
            if f.name == name:
                return f

        check.failed('Field {name} not found'.format(name=name))

    def get_child_type_keys(self):
        if ConfigTypeKind.is_closed_generic(self.kind):
            return self.type_param_keys
        elif ConfigTypeKind.has_fields(self.kind):
            return [field.type_key for field in self.fields]
        else:
            return []


@whitelist_for_serdes
class ConfigEnumValueSnap(namedtuple('_ConfigEnumValueSnap', 'value description')):
    def __new__(cls, value, description):
        return super(ConfigEnumValueSnap, cls).__new__(
            cls,
            value=check.str_param(value, 'value'),
            description=check.opt_str_param(description, 'description'),
        )


@whitelist_for_serdes
class ConfigFieldSnap(
    namedtuple(
        '_ConfigFieldSnap',
        'name type_key is_required default_provided default_value_as_str description',
    )
):
    def __new__(
        cls, name, type_key, is_required, default_provided, default_value_as_str, description
    ):
        return super(ConfigFieldSnap, cls).__new__(
            cls,
            name=check.opt_str_param(name, 'name'),
            type_key=check.str_param(type_key, 'type_key'),
            is_required=check.bool_param(is_required, 'is_required'),
            default_provided=check.bool_param(default_provided, 'default_provided'),
            default_value_as_str=check.opt_str_param(default_value_as_str, 'default_value_as_str'),
            description=check.opt_str_param(description, 'description'),
        )


def snap_from_field(name, field):
    check.str_param(name, 'name')
    check.inst_param(field, 'field', Field)
    return ConfigFieldSnap(
        name=name,
        type_key=field.config_type.key,
        is_required=field.is_required,
        default_provided=field.default_provided,
        default_value_as_str=field.default_value_as_str if field.default_provided else None,
        description=field.description,
    )


def snap_from_config_type(config_type):
    check.inst_param(config_type, 'config_type', ConfigType)
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
    )
