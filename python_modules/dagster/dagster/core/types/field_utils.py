# encoding: utf-8
import hashlib
import re

from dagster import check
from dagster.core.errors import DagsterInvalidDefinitionError

from .config import DEFAULT_TYPE_ATTRIBUTES, ConfigType, ConfigTypeAttributes, ConfigTypeKind


def all_optional_type(config_type):
    check.inst_param(config_type, 'config_type', ConfigType)

    if config_type.is_composite:
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

    config_type = resolve_to_config_type(obj)
    if config_type:
        raise DagsterInvalidDefinitionError(
            (
                'You have passed a config type "{printed_type}" in the parameter '
                '"{param_name}" {error_context_str}. '
                'You have likely forgot to wrap this type in a Field.'
            ).format(
                printed_type=print_config_type_to_string(config_type, with_lines=False),
                error_context_str=error_context_str,
                param_name=param_name,
            )
        )
    else:
        raise DagsterInvalidDefinitionError(
            (
                'You have passed an object {value_repr} of incorrect type '
                '"{type_name}" in the parameter "{param_name}" '
                '{error_context_str} where a Field was expected.'
            ).format(
                error_context_str=error_context_str,
                param_name=param_name,
                value_repr=repr(obj),
                type_name=type(obj).__name__,
            )
        )


def check_user_facing_opt_field_param(obj, param_name, error_context_str):
    from .field import Field

    check.str_param(param_name, 'param_name')
    if obj is None or isinstance(obj, Field):
        return obj

    return raise_bad_user_facing_field_argument(obj, param_name, error_context_str)


class _ConfigHasFields(ConfigType):
    def __init__(self, fields, **kwargs):
        from dagster.core.types.field import Field

        self.fields = check.dict_param(fields, 'fields', key_type=str, value_type=Field)
        super(_ConfigHasFields, self).__init__(**kwargs)

    @property
    def inner_types(self):
        return list(set(self._yield_inner_types()))

    def _yield_inner_types(self):
        for field in self.fields.values():
            yield field.config_type
            for inner_type in field.config_type.inner_types:
                yield inner_type

    def debug_str(self):
        def left_pad(line, n=2, char=" "):
            lines = line.splitlines()
            return "\n".join(map(lambda x: (char * n) + x, lines))

        def format_fields(fields):
            lines = map(left_pad, fields)
            return '{{\n{lines}\n}}'.format(lines="\n".join(lines))

        def field_to_string(field_key, field_value):
            s = "{k}{opt}: ".format(k=field_key, opt="?" if field_value.is_optional else "")

            if field_value.config_type.is_scalar:
                typ = re.search(r'\.([^\.]*) object', str(field_value.config_type)).group(1)
                s += "[" + typ + "] "
            elif field_value.config_type.is_selector:
                fields = [
                    field_to_string("-" + k, v)
                    for k, v in field_value.config_type.inst().fields.items()
                ]
                fields = map(lambda x: left_pad(x, 1, "|"), fields)
                s += format_fields(fields)
            elif field_value.config_type.is_enum:
                fields = [
                    field_to_string(k, v) for k, v in field_value.config_type.inst().fields.items()
                ]
                s += format_fields(fields)
            elif field_value.config_type.is_composite:
                fields = [
                    field_to_string(k, v) for k, v in field_value.config_type.inst().fields.items()
                ]
                s += format_fields(fields)
            elif field_value.config_type.is_list:
                fields = [
                    field_to_string(k, v)
                    for k, v in field_value.config_type.inst().inner_type.inst().fields.items()
                ]
                s += format_fields(fields)
            elif field_value.config_type.is_any:
                s += "[Any]"

            s += (
                " default=" + str(field_value.default_value) if field_value.default_provided else ""
            )
            return s

        fields = [field_to_string(k, v) for k, v in self.fields.items()]
        return format_fields(fields)


def check_user_facing_fields_dict(fields, type_name_msg):
    check.dict_param(fields, 'fields', key_type=str)
    check.str_param(type_name_msg, 'type_name_msg')
    from .field import Field

    # early check of all values
    if all(map(lambda f: isinstance(f, Field), fields.values())):
        return

    # now do potentially expensive error check and string building

    sorted_field_names = sorted(list(fields.keys()))

    for field_name, potential_field in fields.items():
        if isinstance(potential_field, Field):
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


def NamedDict(name, fields, description=None, type_attributes=DEFAULT_TYPE_ATTRIBUTES):
    '''
    A :py:class:`Dict` with a name allowing it to be referenced by that name.
    '''
    check_user_facing_fields_dict(fields, 'NamedDict named "{}"'.format(name))

    class _NamedDict(_ConfigHasFields):
        def __init__(self):
            super(_NamedDict, self).__init__(
                key=name,
                name=name,
                kind=ConfigTypeKind.DICT,
                fields=fields,
                description=description,
                type_attributes=type_attributes,
            )

    return _NamedDict


class DictTypeApi(object):
    def __call__(self, fields):
        return build_config_dict(fields)

    def __getitem__(self, *args):
        from .python_dict import create_typed_runtime_dict

        check.param_invariant(len(args[0]) == 2, 'args', 'Must be two parameters')
        return create_typed_runtime_dict(args[0][0], args[0][1])


Dict = DictTypeApi()


FIELD_HASH_CACHE = {}


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


def build_config_dict(fields, description=None, is_system_config=False):
    '''
    Schema for configuration data with string keys and typed values via :py:class:`Field` .

    Args:
        fields (Dict[str, Field])
    '''
    check_user_facing_fields_dict(fields, 'Dict')

    key = 'Dict.' + _compute_fields_hash(fields, description, is_system_config)

    if key in FIELD_HASH_CACHE:
        return FIELD_HASH_CACHE[key]

    class _Dict(_ConfigHasFields):
        def __init__(self):
            super(_Dict, self).__init__(
                name=None,
                kind=ConfigTypeKind.DICT,
                key=key,
                fields=fields,
                description='A configuration dictionary with typed fields',
                type_attributes=ConfigTypeAttributes(
                    is_builtin=True, is_system_config=is_system_config,
                ),
            )

    FIELD_HASH_CACHE[key] = _Dict

    return _Dict


def PermissiveDict(fields=None, description=None):
    '''Defines a config dict with a partially specified schema.
    
    A permissive dict allows partial specification of the config schema. Any fields with a
    specified schema will be type checked. Other fields will be allowed, but will be ignored by
    the type checker.

    Args:
        fields (Dict[str, Field]): The partial specification of the config dict.
    
    **Examples**

    .. code-block:: python

        @solid(config_field=Field(PermissiveDict({'required': Field(String)})))
        def partially_specified_config(context) -> List:
            return sorted(list(context.solid_config.items()))
    '''

    if fields:
        check_user_facing_fields_dict(fields, 'PermissiveDict')

    key = (
        'PermissiveDict.'
        + _compute_fields_hash(fields, description=description, is_system_config=False)
        if fields
        else 'PermissiveDict'
    )

    if key in FIELD_HASH_CACHE:
        return FIELD_HASH_CACHE[key]

    class _PermissiveDict(_ConfigHasFields):
        def __init__(self):
            super(_PermissiveDict, self).__init__(
                name=None,
                key=key,
                kind=ConfigTypeKind.PERMISSIVE_DICT,
                fields=fields or dict(),
                description='A configuration dictionary with typed fields',
                type_attributes=ConfigTypeAttributes(is_builtin=True),
            )

        @property
        def is_permissive_composite(self):
            return True

    FIELD_HASH_CACHE[key] = _PermissiveDict

    return _PermissiveDict


def Selector(fields, description=None, is_system_config=False):
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
            config_field=Field(
                Selector(
                    {
                        'haw': Field(
                            Dict({'whom': Field(String, default_value='honua', is_optional=True)})
                        ),
                        'cn': Field(
                            Dict({'whom': Field(String, default_value='世界', is_optional=True)})
                        ),
                        'en': Field(
                            Dict({'whom': Field(String, default_value='world', is_optional=True)})
                        )
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
    check_user_facing_fields_dict(fields, 'Selector')

    key = 'Selector.' + _compute_fields_hash(
        fields, description=description, is_system_config=is_system_config
    )

    if key in FIELD_HASH_CACHE:
        return FIELD_HASH_CACHE[key]

    class _Selector(_ConfigHasFields):
        def __init__(self):
            super(_Selector, self).__init__(
                key=key,
                name=None,
                kind=ConfigTypeKind.SELECTOR,
                fields=fields,
                type_attributes=ConfigTypeAttributes(is_builtin=True),
            )

    FIELD_HASH_CACHE[key] = _Selector

    return _Selector


def NamedSelector(name, fields, description=None, type_attributes=DEFAULT_TYPE_ATTRIBUTES):
    '''
    A :py:class`Selector` with a name, allowing it to be referenced by that name.

    Args:
        name (str):
        fields (Dict[str, Field])
    '''
    check.str_param(name, 'name')
    check_user_facing_fields_dict(fields, 'NamedSelector named "{}"'.format(name))

    class _NamedSelector(_ConfigHasFields):
        def __init__(self):
            super(_NamedSelector, self).__init__(
                key=name,
                name=name,
                kind=ConfigTypeKind.SELECTOR,
                fields=fields,
                description=description,
                type_attributes=type_attributes,
            )

    return _NamedSelector
