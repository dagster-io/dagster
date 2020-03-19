from dagster import check
from dagster.config.config_type import ConfigType, ConfigTypeKind
from dagster.core.decorator_utils import (
    split_function_parameters,
    validate_decorated_fn_positionals,
)
from dagster.core.errors import DagsterInvalidDefinitionError
from dagster.utils import ensure_gen, ensure_single_item


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

    def required_resource_keys(self):
        return frozenset()


class BareInputSchema(InputHydrationConfig):
    def __init__(self, config_type):
        self.config_type = check.inst_param(config_type, 'config_type', ConfigType)

    @property
    def schema_type(self):
        return self.config_type


def make_bare_input_schema(config_cls):
    from dagster.config.field import resolve_to_config_type

    config_type = resolve_to_config_type(config_cls)
    return BareInputSchema(config_type)


class OutputMaterializationConfig(object):
    @property
    def schema_type(self):
        check.not_implemented(
            'Must override schema_type in {klass}'.format(klass=type(self).__name__)
        )

    def materialize_runtime_values(self, _context, _config_value, _runtime_value):
        '''
        How to materialize a runtime value given configuration.
        '''
        check.not_implemented('Must implement')

    def required_resource_keys(self):
        return frozenset()


class InputSchemaFromDecorator(InputHydrationConfig):
    def __init__(self, config_type, func, required_resource_keys):
        self._config_type = check.inst_param(config_type, 'config_type', ConfigType)
        self._func = check.callable_param(func, 'func')
        self._required_resource_keys = check.opt_set_param(
            required_resource_keys, 'required_resource_keys', of_type=str
        )

    @property
    def schema_type(self):
        return self._config_type

    def construct_from_config_value(self, context, config_value):
        return self._func(context, config_value)

    def required_resource_keys(self):
        return frozenset(self._required_resource_keys)


def _create_input_schema_for_decorator(config_type, func, required_resource_keys):
    return InputSchemaFromDecorator(config_type, func, required_resource_keys)


def input_hydration_config(config_cls, required_resource_keys=None):
    '''Create an input hydration config that maps config data to a runtime value.

    The decorated function should take the execution context and parsed config value and return the
    appropriate runtime value.

    Args:
        config_cls (Any): The type of the config data expected by the decorated function. Users
            should provide one of the :ref:`built-in types <builtin>`, or a composite constructed
            using :py:func:`Selector` or :py:func:`Permissive`.

    Examples:

    .. code-block:: python

        @input_hydration_config(Permissive())
        def _dict_input(_context, value):
            return value
    '''
    from dagster.config.field import resolve_to_config_type

    config_type = resolve_to_config_type(config_cls)
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
        return _create_input_schema_for_decorator(config_type, func, required_resource_keys)

    return wrapper


def input_selector_schema(config_cls, required_resource_keys=None):
    '''
    A decorator for annotating a function that can take the selected properties
    from a ``config_value`` in to an instance of a custom type.

    Args:
        config_cls (Selector)
    '''
    from dagster.config.field import resolve_to_config_type

    config_type = resolve_to_config_type(config_cls)
    check.param_invariant(config_type.kind == ConfigTypeKind.SELECTOR, 'config_cls')

    def _wrap(func):
        def _selector(context, config_value):
            selector_key, selector_value = ensure_single_item(config_value)
            return func(context, selector_key, selector_value)

        return _create_input_schema_for_decorator(config_type, _selector, required_resource_keys)

    return _wrap


class OutputSchemaForDecorator(OutputMaterializationConfig):
    def __init__(self, config_type, func, required_resource_keys):
        self._config_type = check.inst_param(config_type, 'config_type', ConfigType)
        self._func = check.callable_param(func, 'func')
        self._required_resource_keys = check.opt_set_param(
            required_resource_keys, 'required_resource_keys', of_type=str
        )

    @property
    def schema_type(self):
        return self._config_type

    def materialize_runtime_values(self, context, config_value, runtime_value):
        return ensure_gen(self._func(context, config_value, runtime_value))

    def required_resource_keys(self):
        return frozenset(self._required_resource_keys)


def _create_output_schema(config_type, func, required_resource_keys):
    return OutputSchemaForDecorator(config_type, func, required_resource_keys)


def output_materialization_config(config_cls, required_resource_keys=None):
    '''Create an output materialization hydration config that configurably materializes a runtime
    value.

    The decorated function should take the execution context, the parsed config value, and the
    runtime value and the parsed config data, should materialize the runtime value, and should
    return an appropriate :py:class:`Materialization`.

    Args:
        config_cls (Any): The type of the config data expected by the decorated function. Users
            should provide one of the :ref:`built-in types <builtin>`, or a composite constructed
            using :py:func:`Selector` or :py:func:`Permissive`.

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
    from dagster.config.field import resolve_to_config_type

    config_type = resolve_to_config_type(config_cls)
    return lambda func: _create_output_schema(config_type, func, required_resource_keys)


def output_selector_schema(config_cls, required_resource_keys=None):
    '''
    A decorator for a annotating a function that can take the selected properties
    of a ``config_value`` and an instance of a custom type and materialize it.

    Args:
        config_cls (Selector):
    '''
    from dagster.config.field import resolve_to_config_type

    config_type = resolve_to_config_type(config_cls)
    check.param_invariant(config_type.kind == ConfigTypeKind.SELECTOR, 'config_cls')

    def _wrap(func):
        def _selector(context, config_value, runtime_value):
            selector_key, selector_value = ensure_single_item(config_value)
            return func(context, selector_key, selector_value, runtime_value)

        return _create_output_schema(config_type, _selector, required_resource_keys)

    return _wrap
