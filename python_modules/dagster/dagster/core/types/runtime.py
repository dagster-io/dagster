from functools import partial
from io import BytesIO
import six

from dagster import check

from dagster.core.errors import DagsterRuntimeCoercionError

from .builtin_enum import BuiltinEnum
from .builtin_config_schemas import BuiltinSchemas

from .config import ConfigType
from .config import List as ConfigList
from .config import Nullable as ConfigNullable

from .config_schema import InputSchema, OutputSchema

from .marshal import SerializationStrategy, PickleSerializationStrategy
from .dagster_type import check_dagster_type_param
from .wrapping import WrappingListType, WrappingNullableType


def check_opt_config_cls_param(config_cls, param_name):
    if config_cls is None:
        return config_cls
    check.invariant(isinstance(config_cls, type))
    check.param_invariant(issubclass(config_cls, ConfigType), param_name)
    return config_cls


class RuntimeType(object):
    '''
    The class backing DagsterTypes as they are used during execution.
    '''

    def __init__(
        self,
        key,
        name,
        is_builtin=False,
        description=None,
        input_schema=None,
        output_schema=None,
        serialization_strategy=None,
        storage_plugins=None,
    ):

        type_obj = type(self)
        if type_obj in RuntimeType.__cache:
            check.failed(
                (
                    '{type_obj} already in cache. You **must** use the inst() class method '
                    'to construct RuntimeType and not the ctor'.format(type_obj=type_obj)
                )
            )

        self.key = check.str_param(key, 'key')
        self.name = check.opt_str_param(name, 'name')
        self.description = check.opt_str_param(description, 'description')
        self.input_schema = check.opt_inst_param(input_schema, 'input_schema', InputSchema)
        self.output_schema = check.opt_inst_param(output_schema, 'output_schema', OutputSchema)
        self.serialization_strategy = check.opt_inst_param(
            serialization_strategy,
            'serialization_strategy',
            SerializationStrategy,
            PickleSerializationStrategy(),
        )
        self.storage_plugins = check.opt_dict_param(storage_plugins, 'storage_plugins')

        self.is_builtin = check.bool_param(is_builtin, 'is_builtin')

    __cache = {}

    @classmethod
    def inst(cls):
        if cls not in RuntimeType.__cache:
            RuntimeType.__cache[cls] = cls()  # pylint: disable=E1120
        return RuntimeType.__cache[cls]

    @staticmethod
    def from_builtin_enum(builtin_enum):
        check.inst_param(builtin_enum, 'builtin_enum', BuiltinEnum)
        return _RUNTIME_MAP[builtin_enum]

    @property
    def display_name(self):
        return self.name

    def coerce_runtime_value(self, value):
        return value

    def throw_if_false(self, fn, value):
        if not fn(value):
            raise DagsterRuntimeCoercionError(
                (
                    'Invalid value for Dagster type {type_name}, got value '
                    '{value} of Python type {type}'
                ).format(type_name=self.name, value=repr(value), type=type(value))
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

    @property
    def inner_types(self):
        return []

    @property
    def is_nothing(self):
        return False


class BuiltinScalarRuntimeType(RuntimeType):
    def __init__(self, *args, **kwargs):
        name = type(self).__name__
        super(BuiltinScalarRuntimeType, self).__init__(
            key=name, name=name, is_builtin=True, *args, **kwargs
        )

    @property
    def is_scalar(self):
        return True


class Int(BuiltinScalarRuntimeType):
    def __init__(self):
        super(Int, self).__init__(
            input_schema=BuiltinSchemas.INT_INPUT, output_schema=BuiltinSchemas.INT_OUTPUT
        )

    def coerce_runtime_value(self, value):
        return self.throw_if_false(
            lambda v: not isinstance(v, bool) and isinstance(v, six.integer_types), value
        )


class String(BuiltinScalarRuntimeType):
    def __init__(self):
        super(String, self).__init__(
            input_schema=BuiltinSchemas.STRING_INPUT, output_schema=BuiltinSchemas.STRING_OUTPUT
        )

    def coerce_runtime_value(self, value):
        return self.throw_if_not_string(value)


class Path(BuiltinScalarRuntimeType):
    def __init__(self):
        super(Path, self).__init__(
            input_schema=BuiltinSchemas.PATH_INPUT, output_schema=BuiltinSchemas.PATH_OUTPUT
        )

    def coerce_runtime_value(self, value):
        return self.throw_if_not_string(value)


class Float(BuiltinScalarRuntimeType):
    def __init__(self):
        super(Float, self).__init__(
            input_schema=BuiltinSchemas.FLOAT_INPUT, output_schema=BuiltinSchemas.FLOAT_OUTPUT
        )

    def coerce_runtime_value(self, value):
        return self.throw_if_false(lambda v: isinstance(v, float), value)


class Bool(BuiltinScalarRuntimeType):
    def __init__(self):
        super(Bool, self).__init__(
            input_schema=BuiltinSchemas.BOOL_INPUT, output_schema=BuiltinSchemas.BOOL_OUTPUT
        )

    def coerce_runtime_value(self, value):
        return self.throw_if_false(lambda v: isinstance(v, bool), value)


class Bytes(RuntimeType, BytesIO):
    def __init__(self):
        from dagster import RunStorageMode

        storage_plugins = {}
        try:
            from dagster_aws.s3 import BytesIOS3StoragePlugin

            storage_plugins[RunStorageMode.S3] = BytesIOS3StoragePlugin
        except ImportError:
            pass

        super(Bytes, self).__init__('Bytes', 'Bytes')

    def coerce_runtime_value(self, value):
        if isinstance(value, BytesIO):
            return value
        if isinstance(value, bytes):
            return BytesIO(value)


class Anyish(RuntimeType):
    def __init__(
        self, key, name, input_schema=None, output_schema=None, is_builtin=False, description=None
    ):
        super(Anyish, self).__init__(
            key=key,
            name=name,
            input_schema=input_schema,
            output_schema=output_schema,
            is_builtin=is_builtin,
            description=description,
        )

    @property
    def is_any(self):
        return True


class Any(Anyish):
    def __init__(self):
        super(Any, self).__init__(
            key='Any',
            name='Any',
            input_schema=BuiltinSchemas.ANY_INPUT,
            output_schema=BuiltinSchemas.ANY_OUTPUT,
            is_builtin=True,
        )


def define_any_type(name, description=None):
    class NamedAnyType(Anyish):
        def __init__(self):
            super(NamedAnyType, self).__init__(key=name, name=name, description=description)

    return NamedAnyType


class Nothing(RuntimeType):
    def __init__(self):
        super(Nothing, self).__init__(
            key='Nothing', name='Nothing', input_schema=None, output_schema=None, is_builtin=True
        )

    @property
    def is_nothing(self):
        return True

    def coerce_runtime_value(self, value):
        return self.throw_if_false(lambda v: v is None, value)


class PythonObjectType(RuntimeType):
    def __init__(self, python_type, key=None, name=None, **kwargs):
        name = check.opt_str_param(name, 'name', type(self).__name__)
        key = check.opt_str_param(key, 'key', name)
        super(PythonObjectType, self).__init__(key=key, name=name, **kwargs)
        self.python_type = check.type_param(python_type, 'python_type')

    def coerce_runtime_value(self, value):
        return self.throw_if_false(lambda v: isinstance(v, self.python_type), value)


def _create_nullable_input_schema(inner_type):
    if not inner_type.input_schema:
        return None

    nullable_type = ConfigNullable(inner_type.input_schema.schema_type).inst()

    class _NullableSchema(InputSchema):
        @property
        def schema_type(self):
            return nullable_type

        def construct_from_config_value(self, context, config_value):
            if config_value is None:
                return None
            return inner_type.input_schema.construct_from_config_value(context, config_value)

    return _NullableSchema()


class NullableType(RuntimeType):
    def __init__(self, inner_type):
        key = 'Nullable.' + inner_type.key
        super(NullableType, self).__init__(
            key=key, name=None, input_schema=_create_nullable_input_schema(inner_type)
        )
        self.inner_type = inner_type

    @property
    def display_name(self):
        return self.inner_type.display_name + '?'

    def coerce_runtime_value(self, value):
        return None if value is None else self.inner_type.coerce_runtime_value(value)

    @property
    def is_nullable(self):
        return True

    @property
    def inner_types(self):
        return [self.inner_type] + self.inner_type.inner_types


def _create_list_input_schema(inner_type):
    if not inner_type.input_schema:
        return None

    list_type = ConfigList(inner_type.input_schema.schema_type).inst()

    class _ListSchema(InputSchema):
        @property
        def schema_type(self):
            return list_type

        def construct_from_config_value(self, context, config_value):
            convert_item = partial(inner_type.input_schema.construct_from_config_value, context)
            return list(map(convert_item, config_value))

    return _ListSchema()


class ListType(RuntimeType):
    def __init__(self, inner_type):
        key = 'List.' + inner_type.key
        super(ListType, self).__init__(
            key=key, name=None, input_schema=_create_list_input_schema(inner_type)
        )
        self.inner_type = inner_type

    @property
    def display_name(self):
        return '[' + self.inner_type.display_name + ']'

    def coerce_runtime_value(self, value):
        value = self.throw_if_false(lambda v: isinstance(value, list), value)
        return [self.inner_type.coerce_runtime_value(item) for item in value]

    @property
    def is_list(self):
        return True

    @property
    def inner_types(self):
        return [self.inner_type] + self.inner_type.inner_types


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
    def __init__(self, key=None, name=None, **kwargs):
        name = check.opt_str_param(name, 'name', type(self).__name__)
        key = check.opt_str_param(key, 'key', name)
        super(Stringish, self).__init__(key=key, name=name, **kwargs)

    def is_scalar(self):
        return True

    def coerce_runtime_value(self, value):
        return self.throw_if_not_string(value)


_RUNTIME_MAP = {
    BuiltinEnum.ANY: Any.inst(),
    BuiltinEnum.BOOL: Bool.inst(),
    BuiltinEnum.FLOAT: Float.inst(),
    BuiltinEnum.INT: Int.inst(),
    BuiltinEnum.PATH: Path.inst(),
    BuiltinEnum.STRING: String.inst(),
    BuiltinEnum.NOTHING: Nothing.inst(),
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


ALL_RUNTIME_BUILTINS = set(_RUNTIME_MAP.values())
