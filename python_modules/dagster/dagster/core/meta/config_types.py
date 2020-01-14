from collections import namedtuple

from dagster import check
from dagster.config.config_type import ConfigType, ConfigTypeKind
from dagster.config.field import Field
from dagster.core.serdes import whitelist_for_serdes


@whitelist_for_serdes
class NonGenericTypeRefMeta(namedtuple('_NonGenericTypeRefMeta', 'key')):
    def __new__(cls, key):
        return super(NonGenericTypeRefMeta, cls).__new__(cls, check.str_param(key, 'key'))


@whitelist_for_serdes
class ConfigTypeMeta(
    namedtuple(
        '_ConfigTypeMeta',
        'kind key given_name description '
        'type_param_refs '  # only valid for closed generics (Set, Tuple, List, Optional)
        'enum_values '  # only valid for enums
        'fields',  # only valid for dicts and selectors
    )
):
    def __new__(
        cls, kind, key, given_name, type_param_refs, enum_values, fields, description,
    ):
        return super(ConfigTypeMeta, cls).__new__(
            cls,
            kind=check.inst_param(kind, 'kind', ConfigTypeKind),
            key=check.str_param(key, 'key'),
            given_name=check.opt_str_param(given_name, 'given_name'),
            type_param_refs=None
            if type_param_refs is None
            else check.list_param(type_param_refs, 'type_param_refs', of_type=TypeRef),
            enum_values=None
            if enum_values is None
            else check.list_param(enum_values, 'enum_values', of_type=ConfigEnumValueMeta),
            fields=None
            if fields is None
            else check.list_param(fields, 'field', of_type=ConfigFieldMeta),
            description=check.opt_str_param(description, 'description'),
        )

    @property
    def inner_type_refs(self):
        '''
        This recurses through the type references with non-generic types as leaves.
        '''

        def _doit():
            next_level_refs = _get_next_level_refs(self)
            if next_level_refs:
                for next_level in next_level_refs:
                    for inner_ref in _recurse_through_generics(next_level):
                        yield inner_ref

        # there might be duplicate keys (esp for scalars)
        refs_by_key = {}

        for ref in _doit():
            if ref.key not in refs_by_key:
                refs_by_key[ref.key] = ref

        return list(refs_by_key.values())


# This function is used by the recursive descent
# through all the inner types. This does *not*
# recursively descend through the type parameters
# of generic types. It just gets the next level of
# types. Either the direct type parameters of a
# generic type. Or the type refs of all the fields
# if it is a type with fields.
def _get_next_level_refs(ref):
    # if a generic type, get type params
    # if a type with fields, get refs of the fields
    if ConfigTypeKind.is_closed_generic(ref.kind):
        return ref.type_param_refs
    elif (
        ConfigTypeKind.has_fields(ref.kind) and ref.fields
    ):  # still check fields because permissive
        return [field_meta.type_ref for field_meta in ref.fields]


def _recurse_through_generics(ref):
    yield ref
    if isinstance(ref, ConfigTypeMeta) and ConfigTypeKind.is_closed_generic(ref.kind):
        for type_param_ref in ref.type_param_refs:
            for inner_ref in _recurse_through_generics(type_param_ref):
                yield inner_ref


# A type reference in these serializable data structures are one of two things
# 1) A closed generic type (e.g. List[Int] of Optional[Set[str]])
# 2) Or a reference to a non-generic type, such as Dict, Selector, or a Scalar.
# Upon deserialization and when hydrated back to the graphql query, it will
# be the responsibility of that module to maintain a dictionary of the
# non-generic types and then do lookups into the dictionary in order to
# to explode the entire type hierarchy requested by the client

TypeRef = (ConfigTypeMeta, NonGenericTypeRefMeta)


@whitelist_for_serdes
class ConfigEnumValueMeta(namedtuple('_ConfigEnumValueMeta', 'value description')):
    def __new__(cls, value, description):
        return super(ConfigEnumValueMeta, cls).__new__(
            cls,
            value=check.str_param(value, 'value'),
            description=check.opt_str_param(description, 'description'),
        )


@whitelist_for_serdes
class ConfigFieldMeta(
    namedtuple(
        '_ConfigFieldMeta',
        'name type_ref is_optional default_provided default_value_as_str description',
    )
):
    def __new__(
        cls, name, type_ref, is_optional, default_provided, default_value_as_str, description
    ):
        return super(ConfigFieldMeta, cls).__new__(
            cls,
            name=check.opt_str_param(name, 'name'),
            type_ref=check.inst_param(type_ref, 'type_ref', TypeRef),
            is_optional=check.bool_param(is_optional, 'is_optional'),
            default_provided=check.bool_param(default_provided, 'default_provided'),
            default_value_as_str=check.opt_str_param(default_value_as_str, 'default_value_as_str'),
            description=check.opt_str_param(description, 'description'),
        )


def meta_from_field(name, field):
    check.str_param(name, 'name')
    check.inst_param(field, 'field', Field)
    return ConfigFieldMeta(
        name=name,
        type_ref=type_ref_of(field.config_type),
        is_optional=field.is_optional,
        default_provided=field.default_provided,
        default_value_as_str=field.default_value_as_str if field.default_provided else None,
        description=field.description,
    )


def type_ref_of(config_type):
    check.inst_param(config_type, 'config_type', ConfigType)
    if ConfigTypeKind.is_closed_generic(config_type.kind):
        return meta_from_config_type(config_type)
    else:
        return NonGenericTypeRefMeta(key=config_type.key)


def type_refs_of(type_list):
    return list(map(type_ref_of, type_list)) if type_list is not None else None


def meta_from_config_type(config_type):
    check.inst_param(config_type, 'config_type', ConfigType)
    return ConfigTypeMeta(
        key=config_type.key,
        given_name=config_type.given_name,
        kind=config_type.kind,
        description=config_type.description,
        type_param_refs=type_refs_of(config_type.type_params),
        enum_values=[
            ConfigEnumValueMeta(ev.config_value, ev.description) for ev in config_type.enum_values
        ]
        if config_type.kind == ConfigTypeKind.ENUM
        else None,
        fields=[meta_from_field(name, field) for name, field in config_type.fields.items()]
        if ConfigTypeKind.has_fields(config_type.kind)
        else None,
    )
