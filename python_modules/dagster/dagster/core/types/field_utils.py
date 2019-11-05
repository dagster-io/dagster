# encoding: utf-8
import re

from dagster import check
from dagster.core.errors import DagsterInvalidDefinitionError

from .config import DEFAULT_TYPE_ATTRIBUTES, ConfigType, ConfigTypeAttributes


def all_optional_type(config_type):
    check.inst_param(config_type, 'config_type', ConfigType)

    if config_type.is_composite:
        for field in config_type.fields.values():
            if not field.is_optional:
                return False
        return True

    return False


class __FieldValueSentinel:
    pass


class __InferOptionalCompositeFieldSentinel:
    pass


FIELD_NO_DEFAULT_PROVIDED = __FieldValueSentinel

INFER_OPTIONAL_COMPOSITE_FIELD = __InferOptionalCompositeFieldSentinel


def check_using_facing_field_param(obj, param_name, error_context_str):
    from dagster.core.types.field import Field, resolve_to_config_type

    check.str_param(param_name, 'param_name')
    check.str_param(error_context_str, 'error_context_str')

    if isinstance(obj, Field):
        return obj

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
    check.str_param(param_name, 'param_name')
    check.str_param(error_context_str, 'error_context_str')
    if obj is None:
        return None
    return check_using_facing_field_param(obj, param_name, error_context_str)


class _ConfigHasFields(ConfigType):
    def __init__(self, fields, *args, **kwargs):
        from dagster.core.types.field import Field

        self.fields = check.dict_param(fields, 'fields', key_type=str, value_type=Field)
        super(_ConfigHasFields, self).__init__(*args, **kwargs)

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


class _ConfigComposite(_ConfigHasFields):
    @property
    def is_composite(self):
        return True

    @property
    def is_permissive_composite(self):
        return False


class _CompositeSolidConfigComposite(_ConfigComposite):
    @property
    def handle(self):
        return self.type_attributes.handle


class _ConfigSelector(_ConfigHasFields):
    @property
    def is_selector(self):
        return True


# HACK HACK HACK
#
# This is not good and a better solution needs to be found. In order
# for the client-side typeahead in dagit to work as currently structured,
# dictionaries need names. While we deal with that we're going to automatically
# name dictionaries. This will cause odd behavior and bugs is you restart
# the server-side process, the type names changes, and you do not refresh the client.
#
# A possible short term mitigation would to name the dictionary based on the hash
# of its member fields to provide stability in between process restarts.
#
class DictCounter:
    _count = 0

    @staticmethod
    def get_next_count():
        DictCounter._count += 1
        return DictCounter._count


def check_user_facing_fields_dict(fields, type_name_msg):
    check.dict_param(fields, 'fields', key_type=str)
    check.str_param(type_name_msg, 'type_name_msg')

    sorted_field_names = sorted(list(fields.keys()))
    for field_name, potential_field in fields.items():
        check_using_facing_field_param(
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

    class _NamedDict(_ConfigComposite):
        def __init__(self):
            super(_NamedDict, self).__init__(
                key=name,
                name=name,
                fields=fields,
                description=description,
                type_attributes=type_attributes,
            )

    return _NamedDict


class DictTypeApi:
    def __call__(self, fields):
        return build_config_dict(fields)

    def __getitem__(self, *args):
        from .python_dict import create_typed_runtime_dict

        check.param_invariant(len(args[0]) == 2, 'args', 'Must be two parameters')
        return create_typed_runtime_dict(args[0][0], args[0][1])


Dict = DictTypeApi()


def build_config_dict(fields):
    '''
    Schema for configuration data with string keys and typed values via :py:class:`Field` .

    Args:
        fields (Dict[str, Field])
    '''
    check_user_facing_fields_dict(fields, 'Dict')

    class _Dict(_ConfigComposite):
        def __init__(self):
            key = 'Dict.' + str(DictCounter.get_next_count())
            super(_Dict, self).__init__(
                name=None,
                key=key,
                fields=fields,
                description='A configuration dictionary with typed fields',
                type_attributes=ConfigTypeAttributes(is_builtin=True),
            )

    return _Dict


def PermissiveDict(fields=None):
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

    class _PermissiveDict(_ConfigComposite):
        def __init__(self):
            key = 'PermissiveDict.' + str(DictCounter.get_next_count())
            super(_PermissiveDict, self).__init__(
                name=None,
                key=key,
                fields=fields or dict(),
                description='A configuration dictionary with typed fields',
                type_attributes=ConfigTypeAttributes(is_builtin=True),
            )

        @property
        def is_permissive_composite(self):
            return True

    return _PermissiveDict


def Selector(fields):
    '''Define a config field requiring the user to select one option.
    
    Selectors are used when you want to be able to present several different options in config but
    allow only one to be selected. For example, a single input might be read in from either a csv
    file or a parquet file, but not both at once.

    Note that in some other type systems this might be called an 'input union'.

    Functionally, a selector is like a :py:class:`Dict`, except that only one key from the dict can
    be specified in valid config.

    Args:
        fields (Dict[str, Field]): The fields from which the user must select.
    
    **Examples**:

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

    class _Selector(_ConfigSelector):
        def __init__(self):
            key = 'Selector.' + str(DictCounter.get_next_count())
            super(_Selector, self).__init__(
                key=key,
                name=None,
                fields=fields,
                # description='A configuration dictionary with typed fields',
                type_attributes=ConfigTypeAttributes(is_builtin=True),
            )

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

    class _NamedSelector(_ConfigSelector):
        def __init__(self):
            super(_NamedSelector, self).__init__(
                key=name,
                name=name,
                fields=fields,
                description=description,
                type_attributes=type_attributes,
            )

    return _NamedSelector
