from dagster import check
from dagster.core.errors import DagsterInvalidDefinitionError, DagsterInvariantViolationError

from .builtin_enum import BuiltinEnum
from .config import ConfigAnyInstance, ConfigType, List, Nullable, Set, Tuple
from .default_applier import apply_default_values
from .field_utils import FIELD_NO_DEFAULT_PROVIDED, all_optional_type
from .typing_api import is_typing_type
from .wrapping import (
    DagsterListApi,
    DagsterSetApi,
    DagsterTupleApi,
    WrappingListType,
    WrappingNullableType,
    WrappingSetType,
    WrappingTupleType,
)


def resolve_to_config_list(list_type):
    check.inst_param(list_type, 'list_type', (WrappingListType, DagsterListApi))

    if isinstance(list_type, DagsterListApi):
        return List(resolve_to_config_type(BuiltinEnum.ANY))

    return List(resolve_to_config_type(list_type.inner_type))


def resolve_to_config_set(set_type):
    check.inst_param(set_type, 'set_type', (WrappingSetType, DagsterSetApi))

    if isinstance(set_type, DagsterSetApi):
        return Set(resolve_to_config_type(BuiltinEnum.ANY))

    return Set(resolve_to_config_type(set_type.inner_type))


def resolve_to_config_tuple(tuple_type):
    check.inst_param(tuple_type, 'list_type', (WrappingTupleType, DagsterTupleApi))

    if isinstance(tuple_type, DagsterTupleApi):
        return List(resolve_to_config_type(BuiltinEnum.ANY))

    if tuple_type.inner_type is None:
        return List(resolve_to_config_type(BuiltinEnum.ANY))

    resolved_types = []
    for type_param in tuple_type.inner_type:
        resolved_type = resolve_to_config_type(type_param)
        if resolved_type is None:
            raise DagsterInvalidDefinitionError(
                'Passed invalid type {type_param} to Tuple'.format(type_param=type_param)
            )
        resolved_types.append(resolved_type)

    return Tuple(resolved_types)


def resolve_to_config_nullable(nullable_type):
    check.inst_param(nullable_type, 'nullable_type', WrappingNullableType)
    return Nullable(resolve_to_config_type(nullable_type.inner_type))


def _is_config_type_class(obj):
    return isinstance(obj, type) and issubclass(obj, ConfigType)


def resolve_to_config_type(dagster_type):
    from .mapping import remap_python_builtin_for_config, is_supported_config_python_builtin
    from .runtime import RuntimeType

    if _is_config_type_class(dagster_type):
        check.param_invariant(
            False,
            'dagster_type',
            'Cannot pass a config type class to resolve_to_config_type. Got {dagster_type}'.format(
                dagster_type=dagster_type
            ),
        )

    check.invariant(
        not (isinstance(dagster_type, type) and issubclass(dagster_type, RuntimeType)),
        'Cannot resolve a runtime type to a config type',
    )

    if is_typing_type(dagster_type):
        raise DagsterInvariantViolationError(
            (
                'You have passed in {dagster_type} in the config system. Types from '
                'the typing module in python are not allowed in the config system. '
                'You must use types that are imported from dagster or primitive types '
                'such as bool, int, etc.'
            ).format(dagster_type=dagster_type)
        )

    # Short circuit if it's already a Config Type
    if isinstance(dagster_type, ConfigType):
        return dagster_type

    # If we are passed here either:
    #  1) We have been passed a python builtin
    #  2) We have been a dagster wrapping type that needs to be convert its config varient
    #     e.g. dagster.List
    #  2) We have been passed an invalid thing. We return False to signify this. It is
    #     up to callers to report a reasonable error.

    if is_supported_config_python_builtin(dagster_type):
        return remap_python_builtin_for_config(dagster_type)

    if dagster_type is None:
        return ConfigAnyInstance
    if BuiltinEnum.contains(dagster_type):
        return ConfigType.from_builtin_enum(dagster_type)
    if isinstance(dagster_type, (WrappingListType, DagsterListApi)):
        return resolve_to_config_list(dagster_type)
    if isinstance(dagster_type, (WrappingSetType, DagsterSetApi)):
        return resolve_to_config_set(dagster_type)
    if isinstance(dagster_type, (WrappingTupleType, DagsterTupleApi)):
        return resolve_to_config_tuple(dagster_type)
    if isinstance(dagster_type, WrappingNullableType):
        return resolve_to_config_nullable(dagster_type)

    # This means that this is an error and we are return False to a callsite
    # We do the error reporting there because those callsites have more context
    return False


class Field(object):
    '''Defines the schema for a configuration field.
 
    Config fields are parsed according to their schemas in order to yield values available at
    pipeline execution time through the config system. Config fields can be set on solids, on custom
    data types (as the :py:func:`@input_hydration_schema <dagster.input_hydration_schema>`), and on
    other pluggable components of the system, such as resources, loggers, and executors.

    Args:
        dagster_type (Any):
            The type of this field. Users should provide one of the
            :ref:`built-in types <builtin>`, a composite constructed using :py:func:`Selector`
            or :py:func:`PermissiveDict`, or a dagster type constructed with
            :py:func:`as_dagster_type`, :py:func:`@dagster_type <dagster_type`, or
            :py:func:`define_python_dagster_type` that has an ``input_hydration_config`` defined.
            Note that these constructs can be nested -- i.e., a :py:class:`Dict` can itself contain
            :py:class:`Fields <Field>` of other types, etc.
        default_value (Any):
            A default value for this field, conformant to the schema set by the
            ``dagster_type`` argument. If a default value is provided, ``is_optional`` should be
            ``True``.
        is_optional (bool):
            Whether the presence of this field is optional. If ``is_optional`` is ``False``, no
            default value should be provided.
        description (str):
            A human-readable description of this config field.

    Examples:
        .. code-block:: python

            @solid(
                config_field=Field(
                    Dict({'word': Field(String, default_value='foo'), 'repeats': Field(Int)})
                )
            )
            def repeat_word(context):
                return context.solid_config['word'] * context.solid_config['repeats']

    '''

    def __init__(
        self,
        dagster_type,
        default_value=FIELD_NO_DEFAULT_PROVIDED,
        is_optional=None,
        description=None,
    ):
        if not isinstance(dagster_type, ConfigType):
            config_type = resolve_to_config_type(dagster_type)
            if not config_type:
                raise DagsterInvalidDefinitionError(
                    (
                        'Attempted to pass {value_repr} to a Field that expects a valid '
                        'dagster type usable in config (e.g. Dict, Int, String et al).'
                    ).format(value_repr=repr(dagster_type))
                )
        else:
            config_type = dagster_type

        self.config_type = check.inst_param(config_type, 'config_type', ConfigType)

        self.description = check.opt_str_param(description, 'description')
        if is_optional is None:
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
        return ('Field({config_type}, default={default}, is_optional={is_optional})').format(
            config_type=self.config_type,
            default='@'
            if self._default_value == FIELD_NO_DEFAULT_PROVIDED
            else self._default_value,
            is_optional=self.is_optional,
        )


def check_field_param(obj, param_name):
    return check.inst_param(obj, param_name, Field)


def check_opt_field_param(obj, param_name):
    return check.opt_inst_param(obj, param_name, Field)
