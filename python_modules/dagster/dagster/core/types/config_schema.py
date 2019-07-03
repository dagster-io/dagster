from dagster import check
from dagster.utils import single_item

from .builtin_enum import BuiltinEnum
from .config import ConfigType, List, Nullable
from .wrapping import WrappingListType, WrappingNullableType


class InputHydrationConfig:
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


class OutputMaterializationConfig:
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
    '''
    A decorator for annotating a function that can turn a ``config_value`` in to
    an instance of a custom type.

    Args:
        config_cls (Any):
    '''
    config_type = resolve_config_cls_arg(config_cls)
    return lambda func: _create_input_schema(config_type, func)


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
            selector_key, selector_value = single_item(config_value)
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
    '''
    A decorator for a annotating a function that can take a ``config_value``
    and an instance of a custom type and materialize it.

    Args:
        config_cls (Any):
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
            selector_key, selector_value = single_item(config_value)
            return func(context, selector_key, selector_value, runtime_value)

        return _create_output_schema(config_type, _selector)

    return _wrap
