from dagster import check
from dagster.builtins import BuiltinEnum
from dagster.core.errors import DagsterInvalidDefinitionError, DagsterInvariantViolationError
from dagster.utils.backcompat import canonicalize_backcompat_args
from dagster.utils.typing_api import is_typing_type

from .config_type import Array, ConfigAnyInstance, ConfigType, ConfigTypeKind
from .field_utils import FIELD_NO_DEFAULT_PROVIDED, all_optional_type
from .post_process import post_process_config


def _is_config_type_class(obj):
    return isinstance(obj, type) and issubclass(obj, ConfigType)


def helpful_list_error_string():
    return 'Please use a python list (e.g. [int]) or dagster.Array (e.g. Array(int)) instead.'


def resolve_to_config_type(dagster_type):
    from .field_utils import convert_fields_to_dict_type

    # Short circuit if it's already a Config Type
    if isinstance(dagster_type, ConfigType):
        return dagster_type

    if isinstance(dagster_type, dict):
        return convert_fields_to_dict_type(dagster_type)

    if isinstance(dagster_type, list):
        if len(dagster_type) != 1:
            raise DagsterInvalidDefinitionError('Array specifications must only be of length 1')

        inner_type = resolve_to_config_type(dagster_type[0])

        if not inner_type:
            raise DagsterInvalidDefinitionError(
                'Invalid member of array specification: {value} in list {the_list}'.format(
                    value=repr(dagster_type[0]), the_list=dagster_type
                )
            )
        return Array(inner_type)

    from dagster.core.types.dagster_type import DagsterType, List, ListType
    from dagster.core.types.python_set import Set, _TypedPythonSet
    from dagster.core.types.python_tuple import Tuple, _TypedPythonTuple

    if _is_config_type_class(dagster_type):
        check.param_invariant(
            False,
            'dagster_type',
            'Cannot pass a config type class to resolve_to_config_type. Got {dagster_type}'.format(
                dagster_type=dagster_type
            ),
        )

    check.invariant(
        not (isinstance(dagster_type, type) and issubclass(dagster_type, DagsterType)),
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

    if dagster_type is List or isinstance(dagster_type, ListType):
        raise DagsterInvalidDefinitionError(
            'Cannot use List in the context of a config file. ' + helpful_list_error_string()
        )

    if dagster_type is Set or isinstance(dagster_type, _TypedPythonSet):
        raise DagsterInvalidDefinitionError(
            'Cannot use Set in the context of a config field. ' + helpful_list_error_string()
        )

    if dagster_type is Tuple or isinstance(dagster_type, _TypedPythonTuple):
        raise DagsterInvalidDefinitionError(
            'Cannot use Tuple in the context of a config field. ' + helpful_list_error_string()
        )

    check.invariant(
        not (isinstance(dagster_type, DagsterType)),
        'Cannot resolve a runtime type to a config type',
    )

    # If we are passed here either:
    #  1) We have been passed a python builtin
    #  2) We have been a dagster wrapping type that needs to be convert its config varient
    #     e.g. dagster.List
    #  2) We have been passed an invalid thing. We return False to signify this. It is
    #     up to callers to report a reasonable error.

    from dagster.primitive_mapping import (
        remap_python_builtin_for_config,
        is_supported_config_python_builtin,
    )

    if is_supported_config_python_builtin(dagster_type):
        return remap_python_builtin_for_config(dagster_type)

    if dagster_type is None:
        return ConfigAnyInstance
    if BuiltinEnum.contains(dagster_type):
        return ConfigType.from_builtin_enum(dagster_type)

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
            or :py:func:`Permissive`, or a dagster type constructed with
            :py:func:`as_dagster_type`, :py:func:`@dagster_type <dagster_type`, or
            :py:func:`PythonObjectDagsterType` that has an ``input_hydration_config`` defined.
            Note that these constructs can be nested -- i.e., a :py:class:`Dict` can itself contain
            :py:class:`Fields <Field>` of other types, etc.
        default_value (Any):
            A default value for this field, conformant to the schema set by the
            ``dagster_type`` argument. If a default value is provided, ``is_optional`` should be
            ``True``.
        is_required (bool):
            Whether the presence of this field is required. Defaults to true. If ``is_required``
            is ``True``, no default value should be provided.
        is_optional (bool) (deprecated):
            Whether the presence of this field is optional. If ``is_optional`` is ``False``, no
            default value should be provided. Deprecated. Use ``is_required`` instead.
        description (str):
            A human-readable description of this config field.

    Examples:
        .. code-block:: python

            @solid(
                config=Field(
                    Dict({'word': Field(String, default_value='foo'), 'repeats': Int})
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
        is_required=None,
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

        check.opt_bool_param(is_optional, 'is_optional')
        check.opt_bool_param(is_required, 'is_required')

        canonical_is_required = canonicalize_backcompat_args(
            new_val=is_required,
            new_arg='is_required',
            old_val=is_optional,
            old_arg='is_optional',
            coerce_old_to_new=lambda val: not val,
            additional_warn_txt='"is_optional" deprecated in 0.7.0 and will be removed in 0.8.0.',
        )

        if canonical_is_required is True:
            check.param_invariant(
                default_value == FIELD_NO_DEFAULT_PROVIDED,
                'default_value',
                'required arguments should not specify default values',
            )

        if canonical_is_required is None:
            # neither is_required nor is_optional where specified
            canonical_is_required = not all_optional_type(self.config_type)

            self._default_value = (
                default_value
                if canonical_is_required
                else post_process_config(self.config_type, None)
            )
        else:
            self._default_value = default_value

        if (
            config_type.kind == ConfigTypeKind.SCALAR
            and self._default_value != FIELD_NO_DEFAULT_PROVIDED
        ):
            check.param_invariant(
                config_type.is_config_scalar_valid(self._default_value),
                'default_value',
                (
                    'default value not valid for config type {name}, '
                    'got value {val} of type {type}'
                ).format(
                    name=config_type.given_name,
                    val=self._default_value,
                    type=type(self._default_value),
                ),
            )

        self.is_optional = not canonical_is_required

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
