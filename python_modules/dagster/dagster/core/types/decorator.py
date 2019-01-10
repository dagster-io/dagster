from dagster import check
from .runtime import PythonObjectType, RuntimeType


def create_inner_class(
    bare_cls, name, description, input_schema=None, output_schema=None, marshalling_strategy=None
):
    class _ObjectType(PythonObjectType):
        def __init__(self):
            super(_ObjectType, self).__init__(
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
        return create_inner_class(
            bare_cls=bare_cls, name=name if name else bare_cls.__name__, description=description
        )

    # check for no args, no parens case
    if callable(name):
        klass = name
        return create_inner_class(bare_cls=klass, name=klass.__name__, description=None)

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


def make_dagster_type(
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
    return create_inner_class(
        existing_type,
        name=existing_type.__name__ if name is None else name,
        description=description,
        input_schema=input_schema,
        output_schema=output_schema,
        marshalling_strategy=marshalling_strategy,
    )
