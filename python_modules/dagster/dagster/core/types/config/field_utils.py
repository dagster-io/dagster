# encoding: utf-8
import hashlib

from dagster import check
from dagster.core.errors import DagsterInvalidDefinitionError

from .config_type import DEFAULT_TYPE_ATTRIBUTES, ConfigType, ConfigTypeAttributes, ConfigTypeKind


def all_optional_type(config_type):
    check.inst_param(config_type, 'config_type', ConfigType)

    if config_type.is_dict:
        for field in config_type.fields.values():
            if not field.is_optional:
                return False
        return True

    return False


class __FieldValueSentinel(object):
    pass


class __InferOptionalCompositeFieldSentinel(object):
    pass


FIELD_NO_DEFAULT_PROVIDED = __FieldValueSentinel

INFER_OPTIONAL_COMPOSITE_FIELD = __InferOptionalCompositeFieldSentinel


def raise_bad_user_facing_field_argument(obj, param_name, error_context_str):
    from .field import resolve_to_config_type
    from .type_printer import print_config_type_to_string

    raise DagsterInvalidDefinitionError(
        (
            'You have passed an object {value_repr} of incorrect type '
            '"{type_name}" in the parameter "{param_name}" '
            '{error_context_str} where a Field, dict, or type was expected.'
        ).format(
            error_context_str=error_context_str,
            param_name=param_name,
            value_repr=repr(obj),
            type_name=type(obj).__name__,
        )
    )


def check_user_facing_opt_config_param(obj, param_name, error_context_str):
    check.str_param(param_name, 'param_name')

    if obj is None:
        return None

    return coerce_potential_field(
        obj,
        lambda potential_field: raise_bad_user_facing_field_argument(
            potential_field, param_name, error_context_str
        ),
    )


class _ConfigHasFields(ConfigType):
    def __init__(self, fields, **kwargs):
        from dagster.core.types.config.field import Field

        self.fields = check.dict_param(fields, 'fields', key_type=str, value_type=Field)
        super(_ConfigHasFields, self).__init__(**kwargs)

    @property
    def recursive_config_types(self):
        return list(set(self._yield_recursive_config_types()))

    def _yield_recursive_config_types(self):
        for field in self.fields.values():
            yield field.config_type
            for recursive_config_type in field.config_type.recursive_config_types:
                yield recursive_config_type


def is_potential_field(potential_field):
    from .field import Field, resolve_to_config_type

    return isinstance(potential_field, (Field, dict)) or resolve_to_config_type(potential_field)


def coerce_potential_field(potential_field, raise_error_callback):
    from .field import Field, resolve_to_config_type

    if not is_potential_field(potential_field):
        raise_error_callback(potential_field)

    return (
        potential_field
        if isinstance(potential_field, Field)
        else Field(Dict(_process_fields_dict(potential_field, raise_error_callback)))
        if isinstance(potential_field, dict)
        else Field(resolve_to_config_type(potential_field))
    )


def _process_fields_dict(fields, throw_error_callback):
    check.dict_param(fields, 'fields', key_type=str)
    check.callable_param(throw_error_callback, 'throw_error_callback')

    return {
        name: coerce_potential_field(value, throw_error_callback) for name, value in fields.items()
    }


def process_user_facing_fields_dict(fields, type_name_msg):
    check.dict_param(fields, 'fields', key_type=str)
    check.str_param(type_name_msg, 'type_name_msg')

    return {
        name: coerce_potential_field(
            value, lambda: _throw_for_bad_fields_dict(fields, type_name_msg)
        )
        for name, value in fields.items()
    }


def _throw_for_bad_fields_dict(fields, type_name_msg):
    from .field import Field

    sorted_field_names = sorted(list(fields.keys()))

    for field_name, potential_field in fields.items():
        if isinstance(potential_field, (Field, dict)):
            continue

        raise_bad_user_facing_field_argument(
            potential_field,
            'fields',
            (
                'and it is in the "{field_name}" entry of that dict. It is from '
                'a {type_name_msg} with fields {field_names}'
            ).format(
                type_name_msg=type_name_msg, field_name=field_name, field_names=sorted_field_names
            ),
        )


class NamedDict(_ConfigHasFields):
    def __init__(self, name, fields, description=None, type_attributes=DEFAULT_TYPE_ATTRIBUTES):
        process_user_facing_fields_dict(fields, 'NamedDict named "{}"'.format(name))
        super(NamedDict, self).__init__(
            key=name,
            name=name,
            kind=ConfigTypeKind.DICT,
            fields=fields,
            description=description,
            type_attributes=type_attributes,
        )


FIELD_HASH_CACHE = {}


def _memoize_inst_in_field_cache(passed_cls, defined_cls, key):
    if key in FIELD_HASH_CACHE:
        return FIELD_HASH_CACHE[key]

    defined_cls_inst = super(defined_cls, passed_cls).__new__(defined_cls)

    FIELD_HASH_CACHE[key] = defined_cls_inst
    return defined_cls_inst


def _add_hash(m, string):
    m.update(string.encode())


def _compute_fields_hash(fields, description, is_system_config):

    m = hashlib.sha1()  # so that hexdigest is 40, not 64 bytes
    if description:
        _add_hash(m, ':description: ' + description)

    _add_hash(m, ':is_system_config: ' + str(is_system_config))

    for field_name in sorted(list(fields.keys())):
        field = fields[field_name]
        _add_hash(m, ':fieldname:' + field_name)
        if field.default_provided:
            _add_hash(m, ':default_value: ' + field.default_value_as_str)
        _add_hash(m, ':is_optional: ' + str(field.is_optional))
        _add_hash(m, ':type_key: ' + field.config_type.key)
        if field.description:
            _add_hash(m, ':description: ' + field.description)

    return m.hexdigest()


def _define_dict_key_hash(fields, description, is_system_config):
    return 'Dict.' + _compute_fields_hash(fields, description, is_system_config)


class Dict(_ConfigHasFields):
    '''
    Schema for configuration data with string keys and typed values via :py:class:`Field` .

    Args:
        fields (Dict[str, Field])
    '''

    def __new__(cls, fields, description=None, is_system_config=False):
        fields = process_user_facing_fields_dict(fields, 'Dict')
        return _memoize_inst_in_field_cache(
            cls, Dict, _define_dict_key_hash(fields, description, is_system_config)
        )

    def __init__(self, fields, description=None, is_system_config=False):
        fields = process_user_facing_fields_dict(fields, 'Dict')
        super(Dict, self).__init__(
            name=None,
            kind=ConfigTypeKind.DICT,
            key=_define_dict_key_hash(fields, description, is_system_config),
            description=description,
            fields=fields,
            type_attributes=ConfigTypeAttributes(
                is_builtin=True, is_system_config=is_system_config,
            ),
        )


def build_config_dict(fields, description=None, is_system_config=False):
    return Dict(fields, description, is_system_config)


def _define_permissive_dict_key(fields, description):
    return (
        'PermissiveDict.'
        + _compute_fields_hash(fields, description=description, is_system_config=False)
        if fields
        else 'PermissiveDict'
    )


class PermissiveDict(_ConfigHasFields):
    '''Defines a config dict with a partially specified schema.
    
    A permissive dict allows partial specification of the config schema. Any fields with a
    specified schema will be type checked. Other fields will be allowed, but will be ignored by
    the type checker.

    Args:
        fields (Dict[str, Field]): The partial specification of the config dict.
    
    **Examples**

    .. code-block:: python

        @solid(config=Field(PermissiveDict({'required': Field(String)})))
        def partially_specified_config(context) -> List:
            return sorted(list(context.solid_config.items()))
    '''

    def __new__(cls, fields=None, description=None):
        if fields:
            fields = process_user_facing_fields_dict(fields, 'PermissiveDict')

        return _memoize_inst_in_field_cache(
            cls, PermissiveDict, _define_permissive_dict_key(fields, description)
        )

    def __init__(self, fields=None, description=None):
        if fields:
            fields = process_user_facing_fields_dict(fields, 'PermissiveDict')
        super(PermissiveDict, self).__init__(
            key=_define_permissive_dict_key(fields, description),
            name=None,
            kind=ConfigTypeKind.PERMISSIVE_DICT,
            fields=fields or dict(),
            type_attributes=ConfigTypeAttributes(is_builtin=True),
            description=description,
        )


def _define_selector_key(fields, description, is_system_config):
    return 'Selector.' + _compute_fields_hash(
        fields, description=description, is_system_config=is_system_config
    )


class Selector(_ConfigHasFields):
    '''Define a config field requiring the user to select one option.
    
    Selectors are used when you want to be able to present several different options in config but
    allow only one to be selected. For example, a single input might be read in from either a csv
    file or a parquet file, but not both at once.

    Note that in some other type systems this might be called an 'input union'.

    Functionally, a selector is like a :py:class:`Dict`, except that only one key from the dict can
    be specified in valid config.

    Args:
        fields (Dict[str, Field]): The fields from which the user must select.
    
    Examples:

    .. code-block:: python

        @solid(
            config=Field(
                Selector(
                    {
                        'haw': {'whom': Field(String, default_value='honua', is_optional=True)},
                        'cn': {'whom': Field(String, default_value='世界', is_optional=True)},
                        'en': {'whom': Field(String, default_value='world', is_optional=True)},
                    }
                ),
                is_optional=True,
                default_value={'en': {'whom': 'world'}},
            )
        )
        def hello_world_with_default(context):
            if 'haw' in context.solid_config:
                return 'Aloha {whom}!'.format(whom=context.solid_config['haw']['whom'])
            if 'cn' in context.solid_config:
                return '你好，{whom}!'.format(whom=context.solid_config['cn']['whom'])
            if 'en' in context.solid_config:
                return 'Hello, {whom}!'.format(whom=context.solid_config['en']['whom'])
    '''

    def __new__(cls, fields, description=None, is_system_config=False):
        fields = process_user_facing_fields_dict(fields, 'Selector')
        return _memoize_inst_in_field_cache(
            cls, Selector, _define_selector_key(fields, description, is_system_config)
        )

    def __init__(self, fields, description=None, is_system_config=False):
        fields = process_user_facing_fields_dict(fields, 'Selector')
        super(Selector, self).__init__(
            key=_define_selector_key(fields, description, is_system_config),
            name=None,
            kind=ConfigTypeKind.SELECTOR,
            fields=fields,
            type_attributes=ConfigTypeAttributes(
                is_builtin=True, is_system_config=is_system_config
            ),
            description=description,
        )


class NamedSelector(_ConfigHasFields):
    def __init__(self, name, fields, description=None, type_attributes=DEFAULT_TYPE_ATTRIBUTES):
        check.str_param(name, 'name')
        fields = process_user_facing_fields_dict(fields, 'NamedSelector named "{}"'.format(name))
        super(NamedSelector, self).__init__(
            key=name,
            name=name,
            kind=ConfigTypeKind.SELECTOR,
            fields=fields,
            description=description,
            type_attributes=type_attributes,
        )
