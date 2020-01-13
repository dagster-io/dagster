from functools import partial

import six

from dagster import check
from dagster.builtins import BuiltinEnum
from dagster.config.config_type import Array
from dagster.config.config_type import Noneable as ConfigNoneable
from dagster.core.definitions.events import TypeCheck
from dagster.core.errors import DagsterInvalidDefinitionError
from dagster.core.storage.type_storage import TypeStoragePlugin

from .builtin_config_schemas import BuiltinSchemas
from .config_schema import InputHydrationConfig, OutputMaterializationConfig
from .marshal import PickleSerializationStrategy, SerializationStrategy


class RuntimeType(object):
    '''Dagster types resolve to objects of this type during execution.'''

    def __init__(
        self,
        key,
        name,
        type_check_fn,
        is_builtin=False,
        description=None,
        input_hydration_config=None,
        output_materialization_config=None,
        serialization_strategy=None,
        auto_plugins=None,
    ):
        self.key = check.str_param(key, 'key')
        self.name = check.opt_str_param(name, 'name')
        self.description = check.opt_str_param(description, 'description')
        self.input_hydration_config = check.opt_inst_param(
            input_hydration_config, 'input_hydration_config', InputHydrationConfig
        )
        self.output_materialization_config = check.opt_inst_param(
            output_materialization_config,
            'output_materialization_config',
            OutputMaterializationConfig,
        )
        self.serialization_strategy = check.opt_inst_param(
            serialization_strategy,
            'serialization_strategy',
            SerializationStrategy,
            PickleSerializationStrategy(),
        )

        self.type_check = check.callable_param(type_check_fn, 'type_check_fn')

        auto_plugins = check.opt_list_param(auto_plugins, 'auto_plugins', of_type=type)

        check.param_invariant(
            all(
                issubclass(auto_plugin_type, TypeStoragePlugin) for auto_plugin_type in auto_plugins
            ),
            'auto_plugins',
        )

        self.auto_plugins = auto_plugins

        self.is_builtin = check.bool_param(is_builtin, 'is_builtin')
        check.invariant(
            self.display_name is not None,
            'All types must have a valid display name, got None for key {}'.format(key),
        )

    def __eq__(self, other):
        check.inst_param(other, 'other', RuntimeType)

        if isinstance(other, self.__class__):
            return len(self.inner_types) == len(other.inner_types) and all(
                t1 == t2 for t1, t2 in zip(self.inner_types, other.inner_types)
            )
        else:
            return False

    @staticmethod
    def from_builtin_enum(builtin_enum):
        check.invariant(BuiltinEnum.contains(builtin_enum), 'must be member of BuiltinEnum')
        return _RUNTIME_MAP[builtin_enum]

    @property
    def display_name(self):
        return self.name

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
    def __init__(self, name, type_check_fn, *args, **kwargs):
        super(BuiltinScalarRuntimeType, self).__init__(
            key=name, name=name, type_check_fn=type_check_fn, is_builtin=True, *args, **kwargs
        )

    @property
    def is_scalar(self):
        return True

    def type_check_method(self, _value):
        raise NotImplementedError()


class _Int(BuiltinScalarRuntimeType):
    def __init__(self):
        super(_Int, self).__init__(
            name='Int',
            input_hydration_config=BuiltinSchemas.INT_INPUT,
            output_materialization_config=BuiltinSchemas.INT_OUTPUT,
            type_check_fn=self.type_check_method,
        )

    def type_check_method(self, value):
        return _fail_if_not_of_type(value, six.integer_types, 'int')


def _typemismatch_error_str(value, expected_type_desc):
    return 'Value "{value}" of python type "{python_type}" must be a {type_desc}.'.format(
        value=value, python_type=type(value).__name__, type_desc=expected_type_desc
    )


def _fail_if_not_of_type(value, value_type, value_type_desc):

    if not isinstance(value, value_type):
        return TypeCheck(success=False, description=_typemismatch_error_str(value, value_type_desc))

    return TypeCheck(success=True)


class _String(BuiltinScalarRuntimeType):
    def __init__(self):
        super(_String, self).__init__(
            name='String',
            input_hydration_config=BuiltinSchemas.STRING_INPUT,
            output_materialization_config=BuiltinSchemas.STRING_OUTPUT,
            type_check_fn=self.type_check_method,
        )

    def type_check_method(self, value):
        return _fail_if_not_of_type(value, six.string_types, 'string')


class _Path(BuiltinScalarRuntimeType):
    def __init__(self):
        super(_Path, self).__init__(
            name='Path',
            input_hydration_config=BuiltinSchemas.PATH_INPUT,
            output_materialization_config=BuiltinSchemas.PATH_OUTPUT,
            type_check_fn=self.type_check_method,
        )

    def type_check_method(self, value):
        return _fail_if_not_of_type(value, six.string_types, 'string')


class _Float(BuiltinScalarRuntimeType):
    def __init__(self):
        super(_Float, self).__init__(
            name='Float',
            input_hydration_config=BuiltinSchemas.FLOAT_INPUT,
            output_materialization_config=BuiltinSchemas.FLOAT_OUTPUT,
            type_check_fn=self.type_check_method,
        )

    def type_check_method(self, value):
        return _fail_if_not_of_type(value, float, 'float')


class _Bool(BuiltinScalarRuntimeType):
    def __init__(self):
        super(_Bool, self).__init__(
            name='Bool',
            input_hydration_config=BuiltinSchemas.BOOL_INPUT,
            output_materialization_config=BuiltinSchemas.BOOL_OUTPUT,
            type_check_fn=self.type_check_method,
        )

    def type_check_method(self, value):
        return _fail_if_not_of_type(value, bool, 'bool')


class Anyish(RuntimeType):
    def __init__(
        self,
        key,
        name,
        input_hydration_config=None,
        output_materialization_config=None,
        serialization_strategy=None,
        is_builtin=False,
        description=None,
    ):
        super(Anyish, self).__init__(
            key=key,
            name=name,
            input_hydration_config=input_hydration_config,
            output_materialization_config=output_materialization_config,
            serialization_strategy=serialization_strategy,
            is_builtin=is_builtin,
            type_check_fn=self.type_check_method,
            description=description,
        )

    def type_check_method(self, _value):
        return TypeCheck(success=True)

    @property
    def is_any(self):
        return True


class _Any(Anyish):
    def __init__(self):
        super(_Any, self).__init__(
            key='Any',
            name='Any',
            input_hydration_config=BuiltinSchemas.ANY_INPUT,
            output_materialization_config=BuiltinSchemas.ANY_OUTPUT,
            is_builtin=True,
        )


def create_any_type(
    name,
    input_hydration_config=None,
    output_materialization_config=None,
    serialization_strategy=None,
    description=None,
):
    return Anyish(
        key=name,
        name=name,
        description=description,
        input_hydration_config=input_hydration_config,
        output_materialization_config=output_materialization_config,
        serialization_strategy=serialization_strategy,
    )


class _Nothing(RuntimeType):
    def __init__(self):
        super(_Nothing, self).__init__(
            key='Nothing',
            name='Nothing',
            input_hydration_config=None,
            output_materialization_config=None,
            type_check_fn=self.type_check_method,
            is_builtin=True,
        )

    @property
    def is_nothing(self):
        return True

    def type_check_method(self, value):
        if value is not None:
            return TypeCheck(
                success=False,
                description='Value must be None, got a {value_type}'.format(value_type=type(value)),
            )

        return TypeCheck(success=True)


class PythonObjectType(RuntimeType):
    def __init__(self, python_type=None, key=None, name=None, type_check=None, **kwargs):
        name = check.opt_str_param(name, 'name', type(self).__name__)
        key = check.opt_str_param(key, 'key', name)
        super(PythonObjectType, self).__init__(
            key=key, name=name, type_check_fn=self.type_check_method, **kwargs
        )
        self.python_type = check.type_param(python_type, 'python_type')
        self._user_type_check = check.opt_callable_param(type_check, 'type_check')

    def type_check_method(self, value):
        if self._user_type_check is not None:
            res = self._user_type_check(value)
            check.invariant(
                isinstance(res, bool) or isinstance(res, TypeCheck),
                'Invalid return type from user-defined type check on Dagster type {dagster_type} '
                'when evaluated on value of type {value_type}: expected bool or TypeCheck, got '
                '{return_type}'.format(
                    dagster_type=self.name, value_type=type(value), return_type=type(res)
                ),
            )
            if res is False:
                return TypeCheck(success=False)
            elif res is True:
                return TypeCheck(success=True)

            return res

        elif not isinstance(value, self.python_type):
            return TypeCheck(
                success=False,
                description=(
                    'Value of type {value_type} failed type check for Dagster type {dagster_type}, '
                    'expected value to be of Python type {expected_type}.'
                ).format(
                    value_type=type(value),
                    dagster_type=self.name,
                    expected_type=self.python_type.__name__,
                ),
            )

        return TypeCheck(success=True)


def define_python_dagster_type(
    python_type,
    name=None,
    description=None,
    input_hydration_config=None,
    output_materialization_config=None,
    serialization_strategy=None,
    auto_plugins=None,
    type_check=None,
):
    '''Core machinery for defining a Dagster type corresponding to an existing python type.

    Users should generally use the :py:func:`@dagster_type` decorator or :py:func:`as_dagster_type`,
    both of which defer to this function.

    Args:
        python_type (cls): The python type to wrap as a Dagster type.
        name (Optional[str]): Name of the new Dagster type. If ``None``, the name (``__name__``) of
            the ``python_type`` will be used.
        description (Optional[str]): A user-readable description of the type.
        input_hydration_config (Optional[InputHydrationConfig]): An instance of a class constructed
            using the :py:func:`@input_hydration_config <dagster.InputHydrationConfig>` decorator
            that can map config data to a value of this type.
        output_materialization_config (Optiona[OutputMaterializationConfig]): An instance of a class
            constructed using the
            :py:func:`@output_materialization_config <dagster.output_materialization_config>`
            decorator that can persist values of this type.
        serialization_strategy (Optional[SerializationStrategy]): An instance of a class that
            inherits from :py:class:`SerializationStrategy`. The default strategy for serializing
            this value when automatically persisting it between execution steps. You should set
            this value if the ordinary serialization machinery (e.g., pickle) will not be adequate
            for this type.
        auto_plugins (Optional[List[TypeStoragePlugin]]): If types must be serialized differently
            depending on the storage being used for intermediates, they should specify this
            argument. In these cases the serialization_strategy argument is not sufficient because
            serialization requires specialized API calls, e.g. to call an S3 API directly instead
            of using a generic file object. See ``dagster_pyspark.DataFrame`` for an example.
        type_check (Optional[Callable[[Any], Union[bool, TypeCheck]]]): If specified, this function
            will be called in place of the default isinstance type check. This function should
            return ``True`` if the type check succeds, ``False`` if it fails, or, if additional
            metadata should be emitted along with the type check success or failure, an instance of
            :py:class:`TypeCheck` with the ``success`` field set appropriately.
    '''

    check.type_param(python_type, 'python_type')
    check.opt_str_param(name, 'name', python_type.__name__)
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

    check.opt_callable_param(type_check, 'type_check')

    return PythonObjectType(
        python_type=python_type,
        name=name,
        description=description,
        input_hydration_config=input_hydration_config,
        output_materialization_config=output_materialization_config,
        serialization_strategy=serialization_strategy,
        auto_plugins=auto_plugins,
        type_check=type_check,
    )


class NoneableInputSchema(InputHydrationConfig):
    def __init__(self, inner_runtime_type):
        self._inner_runtime_type = check.inst_param(
            inner_runtime_type, 'inner_runtime_type', RuntimeType
        )
        check.param_invariant(inner_runtime_type.input_hydration_config, 'inner_runtime_type')
        self._schema_type = ConfigNoneable(inner_runtime_type.input_hydration_config.schema_type)

    @property
    def schema_type(self):
        return self._schema_type

    def construct_from_config_value(self, context, config_value):
        if config_value is None:
            return None
        return self._inner_runtime_type.input_hydration_config.construct_from_config_value(
            context, config_value
        )


def _create_nullable_input_schema(inner_type):
    if not inner_type.input_hydration_config:
        return None

    return NoneableInputSchema(inner_type)


class OptionalType(RuntimeType):
    def __init__(self, inner_type):
        inner_type = resolve_to_runtime_type(inner_type)

        if inner_type is Nothing:
            raise DagsterInvalidDefinitionError(
                'Type Nothing can not be wrapped in List or Optional'
            )

        key = 'Optional.' + inner_type.key
        self.inner_type = inner_type
        super(OptionalType, self).__init__(
            key=key,
            name=None,
            type_check_fn=self.type_check_method,
            input_hydration_config=_create_nullable_input_schema(inner_type),
        )

    @property
    def display_name(self):
        return self.inner_type.display_name + '?'

    def type_check_method(self, value):
        return TypeCheck(success=True) if value is None else self.inner_type.type_check(value)

    @property
    def is_nullable(self):
        return True

    @property
    def inner_types(self):
        return [self.inner_type] + self.inner_type.inner_types


class ListInputSchema(InputHydrationConfig):
    def __init__(self, inner_runtime_type):
        self._inner_runtime_type = check.inst_param(
            inner_runtime_type, 'inner_runtime_type', RuntimeType
        )
        check.param_invariant(inner_runtime_type.input_hydration_config, 'inner_runtime_type')
        self._schema_type = Array(inner_runtime_type.input_hydration_config.schema_type)

    @property
    def schema_type(self):
        return self._schema_type

    def construct_from_config_value(self, context, config_value):
        convert_item = partial(
            self._inner_runtime_type.input_hydration_config.construct_from_config_value, context
        )
        return list(map(convert_item, config_value))


def _create_list_input_schema(inner_type):
    if not inner_type.input_hydration_config:
        return None

    return ListInputSchema(inner_type)


class ListType(RuntimeType):
    def __init__(self, inner_type):
        key = 'List.' + inner_type.key
        self.inner_type = inner_type
        super(ListType, self).__init__(
            key=key,
            name=None,
            type_check_fn=self.type_check_method,
            input_hydration_config=_create_list_input_schema(inner_type),
        )

    @property
    def display_name(self):
        return '[' + self.inner_type.display_name + ']'

    def type_check_method(self, value):
        value_check = _fail_if_not_of_type(value, list, 'list')
        if not value_check.success:
            return value_check

        for item in value:
            item_check = self.inner_type.type_check(item)
            if not item_check.success:
                return item_check

        return TypeCheck(success=True)

    @property
    def is_list(self):
        return True

    @property
    def inner_types(self):
        return [self.inner_type] + self.inner_type.inner_types


class DagsterListApi:
    def __getitem__(self, inner_type):
        check.not_none_param(inner_type, 'inner_type')
        return _List(resolve_to_runtime_type(inner_type))

    def __call__(self, inner_type):
        check.not_none_param(inner_type, 'inner_type')
        return _List(inner_type)


List = DagsterListApi()


def _List(inner_type):
    check.inst_param(inner_type, 'inner_type', RuntimeType)
    if inner_type is Nothing:
        raise DagsterInvalidDefinitionError('Type Nothing can not be wrapped in List or Optional')
    return ListType(inner_type)


class Stringish(RuntimeType):
    def __init__(self, key=None, name=None, **kwargs):
        name = check.opt_str_param(name, 'name', type(self).__name__)
        key = check.opt_str_param(key, 'key', name)
        super(Stringish, self).__init__(
            key=key,
            name=name,
            type_check_fn=self.type_check_method,
            input_hydration_config=BuiltinSchemas.STRING_INPUT,
            output_materialization_config=BuiltinSchemas.STRING_OUTPUT,
            **kwargs
        )

    @property
    def is_scalar(self):
        return True

    def type_check_method(self, value):
        return _fail_if_not_of_type(value, six.string_types, 'string')


def create_string_type(name, description):
    return Stringish(name=name, key=name, description=description)


Any = _Any()
Bool = _Bool()
Float = _Float()
Int = _Int()
Path = _Path()
String = _String()
Nothing = _Nothing()

_RUNTIME_MAP = {
    BuiltinEnum.ANY: Any,
    BuiltinEnum.BOOL: Bool,
    BuiltinEnum.FLOAT: Float,
    BuiltinEnum.INT: Int,
    BuiltinEnum.PATH: Path,
    BuiltinEnum.STRING: String,
    BuiltinEnum.NOTHING: Nothing,
}

__RUNTIME_TYPE_REGISTRY = {}
'''Python types corresponding to user-defined RunTime types created using @dagster_type or
as_dagster_type are registered here so that we can remap the Python types to runtime types.'''


__ANONYMOUS_TYPE_REGISTRY = {}
'''Python types autogenerated by the system are registered here so that we can remap the
Python types to runtime types.'''


def _clear_runtime_type_registry():
    '''Intended to support tests.'''
    __RUNTIME_TYPE_REGISTRY = {}


def register_python_type(python_type, runtime_type):
    check.inst_param(runtime_type, 'runtime_type', RuntimeType)
    if python_type in __RUNTIME_TYPE_REGISTRY:
        # This would be just a great place to insert a short URL pointing to the type system
        # documentation into the error message
        # https://github.com/dagster-io/dagster/issues/1831
        raise DagsterInvalidDefinitionError(
            'A Dagster runtime type has already been registered for the Python type {python_type}. '
            'You can resolve this collision by decorating a subclass of {python_type} with the '
            '@dagster_type decorator, instead of decorating {python_type} or passing it to '
            'as_dagster_type directly.'.format(python_type=python_type)
        )

    __RUNTIME_TYPE_REGISTRY[python_type] = runtime_type


def create_anonymous_type(ttype):

    if ttype in __ANONYMOUS_TYPE_REGISTRY:
        return __ANONYMOUS_TYPE_REGISTRY[ttype]

    dagster_type = define_python_dagster_type(
        name='Implicit[' + ttype.__name__ + ']',
        # Again, https://github.com/dagster-io/dagster/issues/1831 -- would be great to link to
        # type system docs here
        description=(
            'Anonymous Dagster type autogenerated to wrap the Python type {python_type}. In '
            'general, you may prefer to define your own types using the @dagster_type decorator '
            'or the as_dagster_type function.'
        ),
        python_type=ttype,
    )

    __ANONYMOUS_TYPE_REGISTRY[ttype] = dagster_type

    return dagster_type


DAGSTER_INVALID_TYPE_ERROR_MESSAGE = (
    'Invalid type: dagster_type must be a Python type, a type constructed using '
    'python.typing, a type imported from the dagster module, or a class annotated using '
    'as_dagster_type or @dagster_type: got {dagster_type}{additional_msg}'
)


def resolve_to_runtime_type(dagster_type):
    # circular dep
    from .python_dict import PythonDict, Dict
    from .python_set import PythonSet, DagsterSetApi
    from .python_tuple import PythonTuple, DagsterTupleApi
    from .transform_typing import transform_typing_type
    from dagster.config.config_type import ConfigType
    from dagster.primitive_mapping import (
        remap_python_builtin_for_runtime,
        is_supported_runtime_python_builtin,
    )
    from dagster.utils.typing_api import is_typing_type

    check.invariant(
        not (isinstance(dagster_type, type) and issubclass(dagster_type, ConfigType)),
        'Cannot resolve a config type to a runtime type',
    )

    check.invariant(
        not (isinstance(dagster_type, type) and issubclass(dagster_type, RuntimeType)),
        'Do not pass runtime type classes. Got {}'.format(dagster_type),
    )

    # First check to see if it part of python's typing library
    if is_typing_type(dagster_type):
        dagster_type = transform_typing_type(dagster_type)

    if isinstance(dagster_type, RuntimeType):
        return dagster_type

    # Test for unhashable objects -- this is if, for instance, someone has passed us an instance of
    # a dict where they meant to pass dict or Dict, etc.
    try:
        hash(dagster_type)
    except TypeError:
        raise DagsterInvalidDefinitionError(
            DAGSTER_INVALID_TYPE_ERROR_MESSAGE.format(
                additional_msg=(
                    ', which isn\'t hashable. Did you pass an instance of a type instead of '
                    'the type?'
                ),
                dagster_type=str(dagster_type),
            )
        )

    if is_supported_runtime_python_builtin(dagster_type):
        return remap_python_builtin_for_runtime(dagster_type)

    if dagster_type is None:
        return Any

    if dagster_type in __RUNTIME_TYPE_REGISTRY:
        return __RUNTIME_TYPE_REGISTRY[dagster_type]

    if dagster_type is Dict:
        return PythonDict
    if isinstance(dagster_type, DagsterTupleApi):
        return PythonTuple
    if isinstance(dagster_type, DagsterSetApi):
        return PythonSet
    if isinstance(dagster_type, DagsterListApi):
        return List(Any)
    if BuiltinEnum.contains(dagster_type):
        return RuntimeType.from_builtin_enum(dagster_type)
    if not isinstance(dagster_type, type):
        raise DagsterInvalidDefinitionError(
            DAGSTER_INVALID_TYPE_ERROR_MESSAGE.format(
                dagster_type=str(dagster_type), additional_msg='.'
            )
        )

    check.inst(dagster_type, type)

    if dagster_type in __ANONYMOUS_TYPE_REGISTRY:
        return __ANONYMOUS_TYPE_REGISTRY[dagster_type]

    return create_anonymous_type(dagster_type)


ALL_RUNTIME_BUILTINS = list(_RUNTIME_MAP.values())


def construct_runtime_type_dictionary(solid_defs):
    type_dict = {t.name: t for t in ALL_RUNTIME_BUILTINS}
    for solid_def in solid_defs:
        for runtime_type in solid_def.all_runtime_types():
            if not runtime_type.name:
                continue
            if runtime_type.name not in type_dict:
                type_dict[runtime_type.name] = runtime_type
                continue

            if type_dict[runtime_type.name] is not runtime_type:
                raise DagsterInvalidDefinitionError(
                    (
                        'You have created two dagster types with the same name "{type_name}". '
                        'Dagster types have must have unique names.'
                    ).format(type_name=runtime_type.name)
                )

    return type_dict


class DagsterOptionalApi:
    def __getitem__(self, inner_type):
        check.not_none_param(inner_type, 'inner_type')
        return OptionalType(inner_type)


Optional = DagsterOptionalApi()
