from dagster import check
from dagster.core.decorator_utils import (
    split_function_parameters,
    validate_decorated_fn_positionals,
)
from dagster.core.errors import DagsterInvalidDefinitionError
from dagster.utils import ensure_single_item

from .builtin_enum import BuiltinEnum
from .config import ConfigType, List, Nullable
from .wrapping import WrappingListType, WrappingNullableType


class InputHydrationConfig(object):
    @property
    def schema_type(self):
        check.not_implemented(
            'Must override schema_type in {klass}'.format(klass=type(self).__name__)
        )

    def construct_from_config_value(self, _context, config_value):
        '''
        How to create a runtime value from config data.
        '''
        return config_value


def resolve_config_cls_arg(config_cls):
    if BuiltinEnum.contains(config_cls):
        return ConfigType.from_builtin_enum(config_cls)
    elif isinstance(config_cls, WrappingListType):
        return List(resolve_config_cls_arg(config_cls.inner_type))
    elif isinstance(config_cls, WrappingNullableType):
        return Nullable(resolve_config_cls_arg(config_cls.inner_type))
    else:
        check.type_param(config_cls, 'config_cls')
        check.param_invariant(issubclass(config_cls, ConfigType), 'config_cls')
        return config_cls.inst()


def make_bare_input_schema(config_cls):
    config_type = resolve_config_cls_arg(config_cls)

    class _InputSchema(InputHydrationConfig):
        @property
        def schema_type(self):
            return config_type

    return _InputSchema()


class OutputMaterializationConfig(object):
    @property
    def schema_type(self):
        check.not_implemented(
            'Must override schema_type in {klass}'.format(klass=type(self).__name__)
        )

    def materialize_runtime_value(self, _context, _config_value, _runtime_value):
        '''
        How to materialize a runtime value given configuration.
        '''
        check.not_implemented('Must implement')


def _create_input_schema(config_type, func):
    class _InputSchema(InputHydrationConfig):
        @property
        def schema_type(self):
            return config_type

        def construct_from_config_value(self, context, config_value):
            return func(context, config_value)

    return _InputSchema()


def input_hydration_config(config_cls):
    '''Create an input hydration config that maps config data to a runtime value.

    The decorated function should take the execution context and parsed config value and return the
    appropriate runtime value.

    Args:
        config_cls (Any): The type of the config data expected by the decorated function. Users
            should provide one of the :ref:`built-in types <builtin>`, or a composite constructed
            using :py:func:`Selector` or :py:func:`PermissiveDict`.
    
    Examples:

    .. code-block:: python

        @input_hydration_config(PermissiveDict())
        def _dict_input(_context, value):
            return value
    '''
    config_type = resolve_config_cls_arg(config_cls)
    EXPECTED_POSITIONALS = ['context', '*']

    def wrapper(func):
        fn_positionals, _ = split_function_parameters(func, EXPECTED_POSITIONALS)
        missing_positional = validate_decorated_fn_positionals(fn_positionals, EXPECTED_POSITIONALS)
        if missing_positional:
            raise DagsterInvalidDefinitionError(
                "@input_hydration_config '{solid_name}' decorated function does not have required positional "
                "parameter '{missing_param}'. Solid functions should only have keyword arguments "
                "that match input names and a first positional parameter named 'context'.".format(
                    solid_name=func.__name__, missing_param=missing_positional
                )
            )
        return _create_input_schema(config_type, func)

    return wrapper


def input_selector_schema(config_cls):
    '''
    A decorator for annotating a function that can take the selected properties
    from a ``config_value`` in to an instance of a custom type.

    Args:
        config_cls (Selector)
    '''
    config_type = resolve_config_cls_arg(config_cls)
    check.param_invariant(config_type.is_selector, 'config_cls')

    def _wrap(func):
        def _selector(context, config_value):
            selector_key, selector_value = ensure_single_item(config_value)
            return func(context, selector_key, selector_value)

        return _create_input_schema(config_type, _selector)

    return _wrap


def _create_output_schema(config_type, func):
    class _OutputSchema(OutputMaterializationConfig):
        @property
        def schema_type(self):
            return config_type

        def materialize_runtime_value(self, context, config_value, runtime_value):
            return func(context, config_value, runtime_value)

    return _OutputSchema()


def output_materialization_config(config_cls):
    '''Create an output materialization hydration config that configurably materializes a runtime
    value.

    The decorated function should take the execution context, the parsed config value, and the
    runtime value and the parsed config data, should materialize the runtime value, and should
    return an appropriate :py:class:`Materialization`.

    Args:
        config_cls (Any): The type of the config data expected by the decorated function. Users
            should provide one of the :ref:`built-in types <builtin>`, or a composite constructed
            using :py:func:`Selector` or :py:func:`PermissiveDict`.

    Examples:

    .. code-block:: python

        # Takes a list of dicts such as might be read in using csv.DictReader, as well as a config
        value, and writes 
        @output_materialization_config(Path)
        def df_output_schema(_context, path, value):
            with open(path, 'w') as fd:
                writer = csv.DictWriter(fd, fieldnames=value[0].keys())
                writer.writeheader()
                writer.writerows(rowdicts=value)

            return Materialization.file(path)

    '''
    config_type = resolve_config_cls_arg(config_cls)
    return lambda func: _create_output_schema(config_type, func)


def output_selector_schema(config_cls):
    '''
    A decorator for a annotating a function that can take the selected properties
    of a ``config_value`` and an instance of a custom type and materialize it.

    Args:
        config_cls (Selector):
    '''
    config_type = resolve_config_cls_arg(config_cls)
    check.param_invariant(config_type.is_selector, 'config_cls')

    def _wrap(func):
        def _selector(context, config_value, runtime_value):
            selector_key, selector_value = ensure_single_item(config_value)
            return func(context, selector_key, selector_value, runtime_value)

        return _create_output_schema(config_type, _selector)

    return _wrap
