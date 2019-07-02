from dagster import check
from dagster.core.storage.type_storage import TypeStoragePlugin

from .config_schema import InputHydrationConfig, OutputMaterializationConfig
from .marshal import SerializationStrategy, PickleSerializationStrategy
from .runtime import PythonObjectType, RuntimeType


def _create_object_type_class(**kwargs):
    class _ObjectType(PythonObjectType):
        def __init__(self):
            super(_ObjectType, self).__init__(**kwargs)

    return _ObjectType


def _decorate_as_dagster_type(
    bare_cls,
    key,
    name,
    description,
    input_hydration_config=None,
    output_materialization_config=None,
    serialization_strategy=None,
    auto_plugins=None,
    metadata_fn=None,
):
    _ObjectType = _create_object_type_class(
        key=key,
        name=name,
        description=description,
        python_type=bare_cls,
        input_hydration_config=input_hydration_config,
        output_materialization_config=output_materialization_config,
        serialization_strategy=serialization_strategy,
        auto_plugins=auto_plugins,
        metadata_fn=metadata_fn,
    )

    type_inst = _ObjectType.inst()

    make_klass_runtime_type_decorated_klass(bare_cls, type_inst)
    return bare_cls


def dagster_type(
    name=None,
    description=None,
    input_hydration_config=None,
    output_materialization_config=None,
    serialization_strategy=None,
    auto_plugins=None,
):
    '''
    Decorator version of as_dagster_type. See documentation for :py:func:`as_dagster_type` .
    '''

    def _with_args(bare_cls):
        check.type_param(bare_cls, 'bare_cls')
        new_name = name if name else bare_cls.__name__
        return _decorate_as_dagster_type(
            bare_cls=bare_cls,
            key=new_name,
            name=new_name,
            description=description,
            input_hydration_config=input_hydration_config,
            output_materialization_config=output_materialization_config,
            serialization_strategy=serialization_strategy,
            auto_plugins=auto_plugins,
        )

    # check for no args, no parens case
    if callable(name):
        klass = name
        new_name = klass.__name__
        return _decorate_as_dagster_type(
            bare_cls=klass, key=new_name, name=new_name, description=None
        )

    return _with_args


MAGIC_RUNTIME_TYPE_NAME = '__runtime_type'


def is_runtime_type_decorated_klass(klass):
    check.type_param(klass, 'klass')
    return hasattr(klass, MAGIC_RUNTIME_TYPE_NAME)


def get_runtime_type_on_decorated_klass(klass):
    check.type_param(klass, 'klass')
    return getattr(klass, MAGIC_RUNTIME_TYPE_NAME)


def make_klass_runtime_type_decorated_klass(klass, runtime_type):
    check.type_param(klass, 'klass')
    check.inst_param(runtime_type, 'runtime_type', RuntimeType)
    setattr(klass, MAGIC_RUNTIME_TYPE_NAME, runtime_type)


def as_dagster_type(
    existing_type,
    name=None,
    description=None,
    input_hydration_config=None,
    output_materialization_config=None,
    serialization_strategy=None,
    auto_plugins=None,
    metadata_fn=None,
):
    '''
    Takes a python cls and creates a type for it in the Dagster domain.

    Args:
        existing_type (cls)
            The python type you want to project in to the Dagster type system.
        name (Optional[str]):
        description (Optiona[str]):
        input_hydration_config (Optional[InputHydrationConfig]):
            An instance of a class that inherits from :py:class:`InputHydrationConfig` that
            can map config data to a value of this type.

        output_materialization_config (Optiona[OutputMaterializationConfig]):
            An instance of a class that inherits from :py:class:`OutputMaterializationConfig` that
            can map config data to persisting values of this type.

        serialization_strategy (Optional[SerializationStrategy]):
            The default behavior for how to serialize this value for
            persisting between execution steps.

    '''
    check.type_param(existing_type, 'existing_type')
    check.opt_str_param(name, 'name')
    check.opt_str_param(description, 'description')
    check.opt_inst_param(input_hydration_config, 'input_hydration_config', InputHydrationConfig)
    check.opt_inst_param(
        output_materialization_config, 'output_materialization_config', OutputMaterializationConfig
    )
    check.opt_inst_param(
        serialization_strategy,
        'serialization_strategy',
        SerializationStrategy,
        default=PickleSerializationStrategy(),
    )

    auto_plugins = check.opt_list_param(auto_plugins, 'auto_plugins', of_type=type)
    check.param_invariant(
        all(issubclass(auto_plugin_type, TypeStoragePlugin) for auto_plugin_type in auto_plugins),
        'auto_plugins',
    )

    check.opt_callable_param(metadata_fn, 'metadata_fn')

    name = name or existing_type.__name__

    return _decorate_as_dagster_type(
        existing_type,
        key=name,
        name=name,
        description=description,
        input_hydration_config=input_hydration_config,
        output_materialization_config=output_materialization_config,
        serialization_strategy=serialization_strategy,
        auto_plugins=auto_plugins,
        metadata_fn=metadata_fn,
    )
