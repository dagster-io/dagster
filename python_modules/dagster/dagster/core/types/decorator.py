from dagster import check
from .config_schema import InputSchema, OutputSchema
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
    input_schema=None,
    output_schema=None,
    serialization_strategy=None,
):
    _ObjectType = _create_object_type_class(
        key=key,
        name=name,
        description=description,
        python_type=bare_cls,
        input_schema=input_schema,
        output_schema=output_schema,
        serialization_strategy=serialization_strategy,
    )

    type_inst = _ObjectType.inst()

    make_klass_runtime_type_decorated_klass(bare_cls, type_inst)
    return bare_cls


def dagster_type(name=None, description=None):
    def _with_args(bare_cls):
        check.type_param(bare_cls, 'bare_cls')
        new_name = name if name else bare_cls.__name__
        return _decorate_as_dagster_type(
            bare_cls=bare_cls, key=new_name, name=new_name, description=description
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
    input_schema=None,
    output_schema=None,
    serialization_strategy=None,
):
    check.type_param(existing_type, 'existing_type')
    check.opt_str_param(name, 'name')
    check.opt_str_param(description, 'description')
    check.opt_inst_param(input_schema, 'input_schema', InputSchema)
    check.opt_inst_param(output_schema, 'output_schema', OutputSchema)
    check.opt_inst_param(serialization_strategy, 'serialization_strategy', SerializationStrategy)

    if serialization_strategy is None:
        serialization_strategy = PickleSerializationStrategy()

    name = existing_type.__name__ if name is None else name

    return _decorate_as_dagster_type(
        existing_type,
        key=name,
        name=name,
        description=description,
        input_schema=input_schema,
        output_schema=output_schema,
        serialization_strategy=serialization_strategy,
    )
