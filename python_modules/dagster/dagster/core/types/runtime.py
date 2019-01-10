import six

from dagster import check

from dagster.core.errors import DagsterRuntimeCoercionError

from .builtin_enum import BuiltinEnum
from .builtin_config_schemas import define_builtin_scalar_output_schema
from .config import Int as ConfigInt
from .config import String as ConfigString
from .config import Any as ConfigAny
from .config import ConfigType
from .config import List as ConfigList
from .config import Nullable as ConfigNullable
from .config_schema import InputSchema, OutputSchema, make_input_schema
from .marshal import MarshallingStrategy
from .dagster_type import check_dagster_type_param
from .wrapping import WrappingListType, WrappingNullableType


def check_opt_config_cls_param(config_cls, param_name):
    if config_cls is None:
        return config_cls
    check.invariant(isinstance(config_cls, type))
    check.param_invariant(issubclass(config_cls, ConfigType), param_name)
    return config_cls


class RuntimeType(object):
    def __init__(
        self,
        name=None,
        description=None,
        input_schema=None,
        output_schema=None,
        marshalling_strategy=None,
    ):

        type_obj = type(self)
        if type_obj in RuntimeType.__cache:
            check.failed(
                (
                    '{type_obj} already in cache. You **must** use the inst() class method '
                    'to construct RuntimeType and not the ctor'.format(type_obj=type_obj)
                )
            )

        self.name = check.opt_str_param(name, 'name', type(self).__name__)
        self.description = check.opt_str_param(description, 'description')
        self.input_schema = check.opt_inst_param(input_schema, 'input_schema', InputSchema)
        self.output_schema = check.opt_inst_param(output_schema, 'output_schema', OutputSchema)
        self.marshalling_strategy = check.opt_inst_param(
            marshalling_strategy, 'marshalling_strategy', MarshallingStrategy
        )

    __cache = {}

    @classmethod
    def inst(cls):
        if cls not in RuntimeType.__cache:
            RuntimeType.__cache[cls] = cls()
        return RuntimeType.__cache[cls]

    @staticmethod
    def from_builtin_enum(builtin_enum):
        check.inst_param(builtin_enum, 'builtin_enum', BuiltinEnum)
        return _RUNTIME_MAP[builtin_enum]

    def coerce_runtime_value(self, value):
        return value

    def throw_if_false(self, fn, value):
        if not fn(value):
            raise DagsterRuntimeCoercionError(
                'Expected valid value for {type_name} but got {value}'.format(
                    type_name=self.name, value=repr(value)
                )
            )
        return value

    def throw_if_not_string(self, value):
        return self.throw_if_false(lambda v: isinstance(v, six.string_types), value)

    @property
    def is_any(self):
        return False

    @property
    def is_scalar(self):
        return False

    @property
    def is_list(self):
        return False

    @property
    def is_nullable(self):
        return False


class BuiltinScalarRuntimeType(RuntimeType):
    @property
    def is_scalar(self):
        return True


INT_INPUT_SCHEMA = make_input_schema(ConfigInt)
INT_OUTPUT_SCHEMA = define_builtin_scalar_output_schema('Int')


class Int(BuiltinScalarRuntimeType):
    def __init__(self):
        super(Int, self).__init__(input_schema=INT_INPUT_SCHEMA, output_schema=INT_OUTPUT_SCHEMA)

    def coerce_runtime_value(self, value):
        return self.throw_if_false(
            lambda v: not isinstance(v, bool) and isinstance(v, six.integer_types), value
        )


STRING_INPUT_SCHEMA = make_input_schema(ConfigString)
STRING_OUTPUT_SCHEMA = define_builtin_scalar_output_schema('String')


class String(BuiltinScalarRuntimeType):
    def __init__(self):
        super(String, self).__init__(
            input_schema=STRING_INPUT_SCHEMA, output_schema=STRING_OUTPUT_SCHEMA
        )

    def coerce_runtime_value(self, value):
        return self.throw_if_not_string(value)


class Path(String):
    pass


class Float(RuntimeType):
    # TODO
    # def __init__(self):
    #     super(String, self).__init__(
    #         input_schema_cls=config.String,
    #         output_schema_cls=define_builtin_scalar_output_schema(name='String'),
    #     )
    def coerce_runtime_value(self, value):
        return self.throw_if_false(lambda v: isinstance(v, float), value)


class Bool(RuntimeType):
    def coerce_runtime_value(self, value):
        return self.throw_if_false(lambda v: isinstance(v, bool), value)


class Any(RuntimeType):
    def __init__(self):
        super(Any, self).__init__(input_schema=make_input_schema(ConfigAny))

    @property
    def is_any(self):
        return True


class PythonObjectType(RuntimeType):
    def __init__(self, python_type, *args, **kwargs):
        super(PythonObjectType, self).__init__(*args, **kwargs)
        self.python_type = check.type_param(python_type, 'python_type')

    def coerce_runtime_value(self, value):
        return self.throw_if_false(lambda v: isinstance(v, self.python_type), value)


class NullableType(RuntimeType):
    def __init__(self, inner_type):
        super(NullableType, self).__init__(
            name='Nullable.' + inner_type.name,
            input_schema=make_input_schema(ConfigNullable(inner_type.input_schema.schema_type))
            if inner_type.input_schema
            else None,
        )
        self.inner_type = inner_type

    def coerce_runtime_value(self, value):
        return None if value is None else self.inner_type.coerce_runtime_value(value)

    @property
    def is_nullable(self):
        return True


class ListType(RuntimeType):
    def __init__(self, inner_type):
        super(ListType, self).__init__(
            name='List.' + inner_type.name,
            input_schema=make_input_schema(ConfigList(inner_type.input_schema.schema_type))
            if inner_type.input_schema
            else None,
        )
        self.inner_type = inner_type

    def coerce_runtime_value(self, value):
        value = self.throw_if_false(lambda v: isinstance(value, list), value)
        return [self.inner_type.coerce_runtime_value(item) for item in value]

    @property
    def is_list(self):
        return True


def Nullable(inner_type):
    check.inst_param(inner_type, 'inner_type', RuntimeType)

    class _Nullable(NullableType):
        def __init__(self):
            super(_Nullable, self).__init__(inner_type)

    return _Nullable.inst()


def List(inner_type):
    check.inst_param(inner_type, 'inner_type', RuntimeType)

    class _List(ListType):
        def __init__(self):
            super(_List, self).__init__(inner_type)

    return _List.inst()


class Stringish(RuntimeType):
    def is_scalar(self):
        return True

    def coerce_runtime_value(self, value):
        return self.throw_if_not_string(value)


_RUNTIME_MAP = {
    BuiltinEnum.ANY: Any.inst(),
    BuiltinEnum.STRING: String.inst(),
    BuiltinEnum.INT: Int.inst(),
    BuiltinEnum.BOOL: Bool.inst(),
    BuiltinEnum.PATH: Path.inst(),
}


def resolve_to_runtime_type(dagster_type):
    # circular dep
    from .decorator import is_runtime_type_decorated_klass, get_runtime_type_on_decorated_klass

    check_dagster_type_param(dagster_type, 'dagster_type', RuntimeType)

    if dagster_type is None:
        return Any.inst()
    if isinstance(dagster_type, BuiltinEnum):
        return RuntimeType.from_builtin_enum(dagster_type)
    if isinstance(dagster_type, WrappingListType):
        return resolve_to_runtime_list(dagster_type)
    if isinstance(dagster_type, WrappingNullableType):
        return resolve_to_runtime_nullable(dagster_type)
    if is_runtime_type_decorated_klass(dagster_type):
        return get_runtime_type_on_decorated_klass(dagster_type)
    if issubclass(dagster_type, RuntimeType):
        return dagster_type.inst()

    check.failed('should not reach')


def resolve_to_runtime_list(list_type):
    check.inst_param(list_type, 'list_type', WrappingListType)
    return List(resolve_to_runtime_type(list_type.inner_type))


def resolve_to_runtime_nullable(nullable_type):
    check.inst_param(nullable_type, 'nullable_type', WrappingNullableType)
    return Nullable(resolve_to_runtime_type(nullable_type.inner_type))
