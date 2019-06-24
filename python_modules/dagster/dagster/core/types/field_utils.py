from dagster import check
from dagster.core.errors import DagsterInvalidDefinitionError
from .config import ConfigType, ConfigTypeAttributes, DEFAULT_TYPE_ATTRIBUTES
from .default_applier import apply_default_values


def all_optional_type(config_type):
    check.inst_param(config_type, 'config_type', ConfigType)

    if config_type.is_composite or config_type.is_selector:
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
    check.str_param(param_name, 'param_name')
    check.str_param(error_context_str, 'error_context_str')

    if isinstance(obj, FieldImpl):
        return obj

    from dagster.core.types.field import resolve_to_config_type
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


def check_field_param(obj, param_name):
    return check.inst_param(obj, param_name, FieldImpl)


def check_opt_field_param(obj, param_name):
    return check.opt_inst_param(obj, param_name, FieldImpl)


class FieldImpl:
    '''
    A field in a config object.

    Attributes:
        config_type (ConfigType): The type of the field.
        default_value (Any):
            If the Field is optional, a default value can be provided when the field value
            is not specified.
        is_optional (bool): Is the field optional.
        description (str): Description of the field.
    '''

    def __init__(
        self,
        config_type,
        default_value=FIELD_NO_DEFAULT_PROVIDED,
        is_optional=INFER_OPTIONAL_COMPOSITE_FIELD,
        is_secret=False,
        description=None,
    ):
        self.config_type = check.inst_param(config_type, 'config_type', ConfigType)

        self.description = check.opt_str_param(description, 'description')
        if is_optional == INFER_OPTIONAL_COMPOSITE_FIELD:
            is_optional = all_optional_type(self.config_type)
            if is_optional is True:
                self._default_value = apply_default_values(self.config_type, None)
            else:
                self._default_value = default_value
        else:
            is_optional = check.bool_param(is_optional, 'is_optional')
            self._default_value = default_value

        if is_optional is False:
            check.param_invariant(
                default_value == FIELD_NO_DEFAULT_PROVIDED,
                'default_value',
                'required arguments should not specify default values',
            )

        if config_type.is_scalar and self._default_value != FIELD_NO_DEFAULT_PROVIDED:
            check.param_invariant(
                config_type.is_config_scalar_valid(self._default_value),
                'default_value',
                'default value not valid for config type {name}, got value {val} of type {type}'.format(
                    name=config_type.name, val=self._default_value, type=type(self._default_value)
                ),
            )

        self.is_optional = is_optional

        self.is_secret = check.bool_param(is_secret, 'is_secret')

    @property
    def is_required(self):
        return not self.is_optional

    @property
    def default_provided(self):
        '''Was a default value provided

        Returns:
            bool: Yes or no
        '''
        return self._default_value != FIELD_NO_DEFAULT_PROVIDED

    @property
    def default_value(self):
        check.invariant(self.default_provided, 'Asking for default value when none was provided')

        if callable(self._default_value):
            return self._default_value()

        return self._default_value

    @property
    def default_value_as_str(self):
        check.invariant(self.default_provided, 'Asking for default value when none was provided')

        if callable(self._default_value):
            return repr(self._default_value)

        return str(self._default_value)

    def __repr__(self):
        return (
            'Field({config_type}, default={default}, is_optional={is_optional}, '
            'is_secret={is_secret})'
        ).format(
            config_type=self.config_type,
            default='@'
            if self._default_value == FIELD_NO_DEFAULT_PROVIDED
            else self._default_value,
            is_optional=self.is_optional,
            is_secret=self.is_secret,
        )


class _ConfigHasFields(ConfigType):
    def __init__(self, fields, *args, **kwargs):
        self.fields = check.dict_param(fields, 'fields', key_type=str, value_type=FieldImpl)
        super(_ConfigHasFields, self).__init__(*args, **kwargs)

    @property
    def inner_types(self):
        return list(set(self._yield_inner_types()))

    def _yield_inner_types(self):
        for field in self.fields.values():
            yield field.config_type
            for inner_type in field.config_type.inner_types:
                yield inner_type


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


def Dict(fields):
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
    '''A permissive dict will permit the user to partially specify the permitted fields. Any fields
    that are specified and passed in will be type checked. Other fields will be allowed, but
    will be ignored by the type checker.
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
    '''Selectors are used when you want to be able present several different options to the user but
    force them to select one. For example, it would not make much sense to allow them
    to say that a single input should be sourced from a csv and a parquet file: They must choose.

    Note that in other type systems this might be called an "input union."

    Args:
        fields (Dict[str, Field]):
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
