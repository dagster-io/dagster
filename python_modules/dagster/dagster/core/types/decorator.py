from dagster import check
from .config_schema import InputSchema, OutputSchema
from .marshal import MarshallingStrategy, PickleMarshallingStrategy
from .runtime import PythonObjectType, RuntimeType


def _create_object_type_class(**kwargs):
    class _ObjectType(PythonObjectType):
        def __init__(self):
            super(_ObjectType, self).__init__(**kwargs)

    return _ObjectType


def _decorate_as_dagster_type(
    bare_cls, name, description, input_schema=None, output_schema=None, marshalling_strategy=None
):
    _ObjectType = _create_object_type_class(
        name=name,
        description=description,
        python_type=bare_cls,
        input_schema=input_schema,
        output_schema=output_schema,
        marshalling_strategy=marshalling_strategy,
    )

    type_inst = _ObjectType.inst()

    make_klass_runtime_type_decorated_klass(bare_cls, type_inst)
    return bare_cls


def dagster_type(name=None, description=None):
    def _with_args(bare_cls):
        check.type_param(bare_cls, 'bare_cls')
        return _decorate_as_dagster_type(
            bare_cls=bare_cls, name=name if name else bare_cls.__name__, description=description
        )

    # check for no args, no parens case
    if callable(name):
        klass = name
        return _decorate_as_dagster_type(bare_cls=klass, name=klass.__name__, description=None)

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
    marshalling_strategy=None,
):
    check.type_param(existing_type, 'existing_type')
    check.opt_str_param(name, 'name')
    check.opt_str_param(description, 'description')
    check.opt_inst_param(input_schema, 'input_schema', InputSchema)
    check.opt_inst_param(output_schema, 'output_schema', OutputSchema)
    check.opt_inst_param(marshalling_strategy, 'marshalling_strategy', MarshallingStrategy)

    if marshalling_strategy is None:
        marshalling_strategy = PickleMarshallingStrategy()

    return _decorate_as_dagster_type(
        existing_type,
        name=existing_type.__name__ if name is None else name,
        description=description,
        input_schema=input_schema,
        output_schema=output_schema,
        marshalling_strategy=marshalling_strategy,
    )
