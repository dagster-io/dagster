from dagster import check
from dagster.core.errors import DagsterInvalidDefinitionError

from .builtin_enum import BuiltinEnum
from .config import Any, ConfigType, List, Nullable, Set, Tuple
from .default_applier import apply_default_values
from .field_utils import FIELD_NO_DEFAULT_PROVIDED, all_optional_type
from .wrapping import WrappingListType, WrappingNullableType, WrappingSetType, WrappingTupleType


def resolve_to_config_list(list_type):
    check.inst_param(list_type, 'list_type', WrappingListType)
    return List(resolve_to_config_type(list_type.inner_type))


def resolve_to_config_set(set_type):
    check.inst_param(set_type, 'set_type', WrappingSetType)
    return Set(resolve_to_config_type(set_type.inner_type))


def resolve_to_config_tuple(tuple_type):
    check.inst_param(tuple_type, 'list_type', WrappingTupleType)
    if tuple_type.inner_type is None:
        return List(resolve_to_config_type(tuple_type.inner_type))
    inner_types = [resolve_to_config_type(inner_type) for inner_type in tuple_type.inner_type]
    return Tuple(inner_types)


def resolve_to_config_nullable(nullable_type):
    check.inst_param(nullable_type, 'nullable_type', WrappingNullableType)
    return Nullable(resolve_to_config_type(nullable_type.inner_type))


def resolve_to_config_type(dagster_type):
    from .mapping import remap_python_type
    from .runtime import RuntimeType

    check.invariant(
        not (isinstance(dagster_type, type) and issubclass(dagster_type, RuntimeType)),
        'Cannot resolve a runtime type to a config type',
    )

    dagster_type = remap_python_type(dagster_type)

    if dagster_type is None:
        return Any.inst()
    if BuiltinEnum.contains(dagster_type):
        return ConfigType.from_builtin_enum(dagster_type)
    if isinstance(dagster_type, WrappingListType):
        return resolve_to_config_list(dagster_type).inst()
    if isinstance(dagster_type, WrappingSetType):
        return resolve_to_config_set(dagster_type).inst()
    if isinstance(dagster_type, WrappingTupleType):
        return resolve_to_config_tuple(dagster_type).inst()
    if isinstance(dagster_type, WrappingNullableType):
        return resolve_to_config_nullable(dagster_type).inst()
    if isinstance(dagster_type, type) and issubclass(dagster_type, ConfigType):
        return dagster_type.inst()

    return None


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
