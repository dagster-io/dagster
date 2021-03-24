import typing
from abc import abstractmethod
from enum import Enum as PythonEnum
from functools import partial

from dagster import check
from dagster.builtins import BuiltinEnum
from dagster.config.config_type import Array
from dagster.config.config_type import Noneable as ConfigNoneable
from dagster.core.definitions.events import TypeCheck
from dagster.core.errors import DagsterInvalidDefinitionError, DagsterInvariantViolationError
from dagster.core.storage.type_storage import TypeStoragePlugin
from dagster.serdes import whitelist_for_serdes

from .builtin_config_schemas import BuiltinSchemas
from .config_schema import DagsterTypeLoader, DagsterTypeMaterializer
from .marshal import PickleSerializationStrategy, SerializationStrategy


@whitelist_for_serdes
class DagsterTypeKind(PythonEnum):
    ANY = "ANY"
    SCALAR = "SCALAR"
    LIST = "LIST"
    NOTHING = "NOTHING"
    NULLABLE = "NULLABLE"
    REGULAR = "REGULAR"


class DagsterType:
    """Define a type in dagster. These can be used in the inputs and outputs of solids.

    Args:
        type_check_fn (Callable[[TypeCheckContext, Any], [Union[bool, TypeCheck]]]):
            The function that defines the type check. It takes the value flowing
            through the input or output of the solid. If it passes, return either
            ``True`` or a :py:class:`~dagster.TypeCheck` with ``success`` set to ``True``. If it fails,
            return either ``False`` or a :py:class:`~dagster.TypeCheck` with ``success`` set to ``False``.
            The first argument must be named ``context`` (or, if unused, ``_``, ``_context``, or ``context_``).
            Use ``required_resource_keys`` for access to resources.
        key (Optional[str]): The unique key to identify types programatically.
            The key property always has a value. If you omit key to the argument
            to the init function, it instead receives the value of ``name``. If
            neither ``key`` nor ``name`` is provided, a ``CheckError`` is thrown.

            In the case of a generic type such as ``List`` or ``Optional``, this is
            generated programatically based on the type parameters.

            For most use cases, name should be set and the key argument should
            not be specified.
        name (Optional[str]): A unique name given by a user. If ``key`` is ``None``, ``key``
            becomes this value. Name is not given in a case where the user does
            not specify a unique name for this type, such as a generic class.
        description (Optional[str]): A markdown-formatted string, displayed in tooling.
        loader (Optional[DagsterTypeLoader]): An instance of a class that
            inherits from :py:class:`~dagster.DagsterTypeLoader` and can map config data to a value of
            this type. Specify this argument if you will need to shim values of this type using the
            config machinery. As a rule, you should use the
            :py:func:`@dagster_type_loader <dagster.dagster_type_loader>` decorator to construct
            these arguments.
        materializer (Optional[DagsterTypeMaterializer]): An instance of a class
            that inherits from :py:class:`~dagster.DagsterTypeMaterializer` and can persist values of
            this type. As a rule, you should use the
            :py:func:`@dagster_type_materializer <dagster.dagster_type_materializer>`
            decorator to construct these arguments.
        serialization_strategy (Optional[SerializationStrategy]): An instance of a class that
            inherits from :py:class:`~dagster.SerializationStrategy`. The default strategy for serializing
            this value when automatically persisting it between execution steps. You should set
            this value if the ordinary serialization machinery (e.g., pickle) will not be adequate
            for this type.
        auto_plugins (Optional[List[Type[TypeStoragePlugin]]]): If types must be serialized differently
            depending on the storage being used for intermediates, they should specify this
            argument. In these cases the serialization_strategy argument is not sufficient because
            serialization requires specialized API calls, e.g. to call an S3 API directly instead
            of using a generic file object. See ``dagster_pyspark.DataFrame`` for an example.
        required_resource_keys (Optional[Set[str]]): Resource keys required by the ``type_check_fn``.
        is_builtin (bool): Defaults to False. This is used by tools to display or
            filter built-in types (such as :py:class:`~dagster.String`, :py:class:`~dagster.Int`) to visually distinguish
            them from user-defined types. Meant for internal use.
        kind (DagsterTypeKind): Defaults to None. This is used to determine the kind of runtime type
            for InputDefinition and OutputDefinition type checking.
    """

    def __init__(
        self,
        type_check_fn,
        key=None,
        name=None,
        is_builtin=False,
        description=None,
        loader=None,
        materializer=None,
        serialization_strategy=None,
        auto_plugins=None,
        required_resource_keys=None,
        kind=DagsterTypeKind.REGULAR,
    ):
        check.opt_str_param(key, "key")
        check.opt_str_param(name, "name")

        check.invariant(not (name is None and key is None), "Must set key or name")

        if name is None:
            check.param_invariant(
                bool(key),
                "key",
                "If name is not provided, must provide key.",
            )
            self.key, self._name = key, None
        elif key is None:
            check.param_invariant(
                bool(name),
                "name",
                "If key is not provided, must provide name.",
            )
            self.key, self._name = name, name
        else:
            check.invariant(key and name)
            self.key, self._name = key, name

        self.description = check.opt_str_param(description, "description")
        self.loader = check.opt_inst_param(loader, "loader", DagsterTypeLoader)
        self.materializer = check.opt_inst_param(
            materializer, "materializer", DagsterTypeMaterializer
        )

        self.serialization_strategy = check.opt_inst_param(
            serialization_strategy,
            "serialization_strategy",
            SerializationStrategy,
            PickleSerializationStrategy(),
        )
        self.required_resource_keys = check.opt_set_param(
            required_resource_keys,
            "required_resource_keys",
        )

        self._type_check_fn = check.callable_param(type_check_fn, "type_check_fn")
        _validate_type_check_fn(self._type_check_fn, self._name)

        auto_plugins = check.opt_list_param(auto_plugins, "auto_plugins", of_type=type)

        check.param_invariant(
            all(
                issubclass(auto_plugin_type, TypeStoragePlugin) for auto_plugin_type in auto_plugins
            ),
            "auto_plugins",
        )

        self.auto_plugins = auto_plugins

        self.is_builtin = check.bool_param(is_builtin, "is_builtin")
        check.invariant(
            self.display_name is not None,
            "All types must have a valid display name, got None for key {}".format(key),
        )

        self.kind = check.inst_param(kind, "kind", DagsterTypeKind)

    def type_check(self, context, value):
        retval = self._type_check_fn(context, value)

        if not isinstance(retval, (bool, TypeCheck)):
            raise DagsterInvariantViolationError(
                (
                    "You have returned {retval} of type {retval_type} from the type "
                    'check function of type "{type_key}". Return value must be instance '
                    "of TypeCheck or a bool."
                ).format(retval=repr(retval), retval_type=type(retval), type_key=self.key)
            )

        return TypeCheck(success=retval) if isinstance(retval, bool) else retval

    def __eq__(self, other):
        return isinstance(other, DagsterType) and self.key == other.key

    def __ne__(self, other):
        return not self.__eq__(other)

    @staticmethod
    def from_builtin_enum(builtin_enum):
        check.invariant(BuiltinEnum.contains(builtin_enum), "must be member of BuiltinEnum")
        return _RUNTIME_MAP[builtin_enum]

    @property
    def metadata_entries(self):
        return []

    @property
    def display_name(self):
        """Asserted in __init__ to be not None, overridden in many subclasses"""
        return self._name

    @property
    def unique_name(self):
        """The unique name of this type. Can be None if the type is not unique, such as container types"""
        check.invariant(
            self._name is not None,
            "unique_name requested but is None for type {}".format(self.display_name),
        )
        return self._name

    @property
    def has_unique_name(self):
        return self._name is not None

    @property
    def inner_types(self):
        return []

    @property
    def loader_schema_key(self):
        return self.loader.schema_type.key if self.loader else None

    @property
    def materializer_schema_key(self):
        return self.materializer.schema_type.key if self.materializer else None

    @property
    def type_param_keys(self):
        return []

    @property
    def is_nothing(self):
        return self.kind == DagsterTypeKind.NOTHING

    @property
    def supports_fan_in(self):
        return False

    def get_inner_type_for_fan_in(self):
        check.invariant(
            "DagsterType {name} does not support fan-in, should have checked supports_fan_in before calling getter.".format(
                name=self.display_name
            )
        )


def _validate_type_check_fn(fn, name):
    from dagster.seven import get_args

    args = get_args(fn)

    # py2 doesn't filter out self
    if len(args) >= 1 and args[0] == "self":
        args = args[1:]

    if len(args) == 2:
        possible_names = {
            "_",
            "context",
            "_context",
            "context_",
        }
        if args[0] not in possible_names:
            DagsterInvalidDefinitionError(
                'type_check function on type "{name}" must have first '
                'argument named "context" (or _, _context, context_).'.format(
                    name=name,
                )
            )
        return True

    raise DagsterInvalidDefinitionError(
        'type_check_fn argument on type "{name}" must take 2 arguments, '
        "received {count}.".format(name=name, count=len(args))
    )


class BuiltinScalarDagsterType(DagsterType):
    def __init__(self, name, type_check_fn, *args, **kwargs):
        super(BuiltinScalarDagsterType, self).__init__(
            key=name,
            name=name,
            kind=DagsterTypeKind.SCALAR,
            type_check_fn=type_check_fn,
            is_builtin=True,
            *args,
            **kwargs,
        )

    def type_check_fn(self, _context, value):
        return self.type_check_scalar_value(value)

    @abstractmethod
    def type_check_scalar_value(self, _value):
        raise NotImplementedError()


class _Int(BuiltinScalarDagsterType):
    def __init__(self):
        super(_Int, self).__init__(
            name="Int",
            loader=BuiltinSchemas.INT_INPUT,
            materializer=BuiltinSchemas.INT_OUTPUT,
            type_check_fn=self.type_check_fn,
        )

    def type_check_scalar_value(self, value):
        return _fail_if_not_of_type(value, int, "int")


def _typemismatch_error_str(value, expected_type_desc):
    return 'Value "{value}" of python type "{python_type}" must be a {type_desc}.'.format(
        value=value, python_type=type(value).__name__, type_desc=expected_type_desc
    )


def _fail_if_not_of_type(value, value_type, value_type_desc):

    if not isinstance(value, value_type):
        return TypeCheck(success=False, description=_typemismatch_error_str(value, value_type_desc))

    return TypeCheck(success=True)


class _String(BuiltinScalarDagsterType):
    def __init__(self):
        super(_String, self).__init__(
            name="String",
            loader=BuiltinSchemas.STRING_INPUT,
            materializer=BuiltinSchemas.STRING_OUTPUT,
            type_check_fn=self.type_check_fn,
        )

    def type_check_scalar_value(self, value):
        return _fail_if_not_of_type(value, str, "string")


class _Float(BuiltinScalarDagsterType):
    def __init__(self):
        super(_Float, self).__init__(
            name="Float",
            loader=BuiltinSchemas.FLOAT_INPUT,
            materializer=BuiltinSchemas.FLOAT_OUTPUT,
            type_check_fn=self.type_check_fn,
        )

    def type_check_scalar_value(self, value):
        return _fail_if_not_of_type(value, float, "float")


class _Bool(BuiltinScalarDagsterType):
    def __init__(self):
        super(_Bool, self).__init__(
            name="Bool",
            loader=BuiltinSchemas.BOOL_INPUT,
            materializer=BuiltinSchemas.BOOL_OUTPUT,
            type_check_fn=self.type_check_fn,
        )

    def type_check_scalar_value(self, value):
        return _fail_if_not_of_type(value, bool, "bool")


class Anyish(DagsterType):
    def __init__(
        self,
        key,
        name,
        loader=None,
        materializer=None,
        serialization_strategy=None,
        is_builtin=False,
        description=None,
        auto_plugins=None,
    ):
        super(Anyish, self).__init__(
            key=key,
            name=name,
            kind=DagsterTypeKind.ANY,
            loader=loader,
            materializer=materializer,
            serialization_strategy=serialization_strategy,
            is_builtin=is_builtin,
            type_check_fn=self.type_check_method,
            description=description,
            auto_plugins=auto_plugins,
        )

    def type_check_method(self, _context, _value):
        return TypeCheck(success=True)

    @property
    def supports_fan_in(self):
        return True

    def get_inner_type_for_fan_in(self):
        # Anyish all the way down
        return self


class _Any(Anyish):
    def __init__(self):
        super(_Any, self).__init__(
            key="Any",
            name="Any",
            loader=BuiltinSchemas.ANY_INPUT,
            materializer=BuiltinSchemas.ANY_OUTPUT,
            is_builtin=True,
        )


def create_any_type(
    name,
    loader=None,
    materializer=None,
    serialization_strategy=None,
    description=None,
    auto_plugins=None,
):
    return Anyish(
        key=name,
        name=name,
        description=description,
        loader=loader,
        materializer=materializer,
        serialization_strategy=serialization_strategy,
        auto_plugins=auto_plugins,
    )


class _Nothing(DagsterType):
    def __init__(self):
        super(_Nothing, self).__init__(
            key="Nothing",
            name="Nothing",
            kind=DagsterTypeKind.NOTHING,
            loader=None,
            materializer=None,
            type_check_fn=self.type_check_method,
            is_builtin=True,
        )

    def type_check_method(self, _context, value):
        if value is not None:
            return TypeCheck(
                success=False,
                description="Value must be None, got a {value_type}".format(value_type=type(value)),
            )

        return TypeCheck(success=True)

    @property
    def supports_fan_in(self):
        return True

    def get_inner_type_for_fan_in(self):
        return self


def isinstance_type_check_fn(
    expected_python_type: typing.Type, dagster_type_name: str, expected_python_type_str: str
):
    def type_check(_context, value):
        if not isinstance(value, expected_python_type):
            return TypeCheck(
                success=False,
                description=(
                    f"Value of type {type(value)} failed type check for Dagster type {dagster_type_name}, "
                    f"expected value to be of Python type {expected_python_type_str}."
                ),
            )

        return TypeCheck(success=True)

    return type_check


class PythonObjectDagsterType(DagsterType):
    """Define a type in dagster whose typecheck is an isinstance check.

    Specifically, the type can either be a single python type (e.g. int),
    or a tuple of types (e.g. (int, float)) which is treated as a union.

    Examples:
        .. code-block:: python

            ntype = PythonObjectDagsterType(python_type=int)
            assert ntype.name == 'int'
            assert_success(ntype, 1)
            assert_failure(ntype, 'a')

        .. code-block:: python

            ntype = PythonObjectDagsterType(python_type=(int, float))
            assert ntype.name == 'Union[int, float]'
            assert_success(ntype, 1)
            assert_success(ntype, 1.5)
            assert_failure(ntype, 'a')


    Args:
        python_type (Union[Type, Tuple[Type, ...]): The dagster typecheck function calls instanceof on
            this type.
        name (Optional[str]): Name the type. Defaults to the name of ``python_type``.
        key (Optional[str]): Key of the type. Defaults to name.
        description (Optional[str]): A markdown-formatted string, displayed in tooling.
        loader (Optional[DagsterTypeLoader]): An instance of a class that
            inherits from :py:class:`~dagster.DagsterTypeLoader` and can map config data to a value of
            this type. Specify this argument if you will need to shim values of this type using the
            config machinery. As a rule, you should use the
            :py:func:`@dagster_type_loader <dagster.dagster_type_loader>` decorator to construct
            these arguments.
        materializer (Optional[DagsterTypeMaterializer]): An instance of a class
            that inherits from :py:class:`~dagster.DagsterTypeMaterializer` and can persist values of
            this type. As a rule, you should use the
            :py:func:`@dagster_type_mate <dagster.dagster_type_mate>`
            decorator to construct these arguments.
        serialization_strategy (Optional[SerializationStrategy]): An instance of a class that
            inherits from :py:class:`SerializationStrategy`. The default strategy for serializing
            this value when automatically persisting it between execution steps. You should set
            this value if the ordinary serialization machinery (e.g., pickle) will not be adequate
            for this type.
        auto_plugins (Optional[List[Type[TypeStoragePlugin]]]): If types must be serialized differently
            depending on the storage being used for intermediates, they should specify this
            argument. In these cases the serialization_strategy argument is not sufficient because
            serialization requires specialized API calls, e.g. to call an S3 API directly instead
            of using a generic file object. See ``dagster_pyspark.DataFrame`` for an example.

    """

    def __init__(self, python_type, key=None, name=None, **kwargs):
        if isinstance(python_type, tuple):
            self.python_type = check.tuple_param(
                python_type, "python_type", of_type=tuple(type for item in python_type)
            )
            self.type_str = "Union[{}]".format(
                ", ".join(python_type.__name__ for python_type in python_type)
            )
        else:
            self.python_type = check.type_param(python_type, "python_type")
            self.type_str = python_type.__name__
        name = check.opt_str_param(name, "name", self.type_str)
        key = check.opt_str_param(key, "key", name)
        super(PythonObjectDagsterType, self).__init__(
            key=key,
            name=name,
            type_check_fn=isinstance_type_check_fn(python_type, name, self.type_str),
            **kwargs,
        )


class NoneableInputSchema(DagsterTypeLoader):
    def __init__(self, inner_dagster_type):
        self._inner_dagster_type = check.inst_param(
            inner_dagster_type, "inner_dagster_type", DagsterType
        )
        check.param_invariant(inner_dagster_type.loader, "inner_dagster_type")
        self._schema_type = ConfigNoneable(inner_dagster_type.loader.schema_type)

    @property
    def schema_type(self):
        return self._schema_type

    def construct_from_config_value(self, context, config_value):
        if config_value is None:
            return None
        return self._inner_dagster_type.loader.construct_from_config_value(context, config_value)


def _create_nullable_input_schema(inner_type):
    if not inner_type.loader:
        return None

    return NoneableInputSchema(inner_type)


class OptionalType(DagsterType):
    def __init__(self, inner_type):
        inner_type = resolve_dagster_type(inner_type)

        if inner_type is Nothing:
            raise DagsterInvalidDefinitionError(
                "Type Nothing can not be wrapped in List or Optional"
            )

        key = "Optional." + inner_type.key
        self.inner_type = inner_type
        super(OptionalType, self).__init__(
            key=key,
            name=None,
            kind=DagsterTypeKind.NULLABLE,
            type_check_fn=self.type_check_method,
            loader=_create_nullable_input_schema(inner_type),
        )

    @property
    def display_name(self):
        return self.inner_type.display_name + "?"

    def type_check_method(self, context, value):
        return (
            TypeCheck(success=True) if value is None else self.inner_type.type_check(context, value)
        )

    @property
    def inner_types(self):
        return [self.inner_type] + self.inner_type.inner_types

    @property
    def type_param_keys(self):
        return [self.inner_type.key]

    @property
    def supports_fan_in(self):
        return self.inner_type.supports_fan_in

    def get_inner_type_for_fan_in(self):
        return self.inner_type.get_inner_type_for_fan_in()


class ListInputSchema(DagsterTypeLoader):
    def __init__(self, inner_dagster_type):
        self._inner_dagster_type = check.inst_param(
            inner_dagster_type, "inner_dagster_type", DagsterType
        )
        check.param_invariant(inner_dagster_type.loader, "inner_dagster_type")
        self._schema_type = Array(inner_dagster_type.loader.schema_type)

    @property
    def schema_type(self):
        return self._schema_type

    def construct_from_config_value(self, context, config_value):
        convert_item = partial(self._inner_dagster_type.loader.construct_from_config_value, context)
        return list(map(convert_item, config_value))


def _create_list_input_schema(inner_type):
    if not inner_type.loader:
        return None

    return ListInputSchema(inner_type)


class ListType(DagsterType):
    def __init__(self, inner_type):
        key = "List." + inner_type.key
        self.inner_type = inner_type
        super(ListType, self).__init__(
            key=key,
            name=None,
            kind=DagsterTypeKind.LIST,
            type_check_fn=self.type_check_method,
            loader=_create_list_input_schema(inner_type),
        )

    @property
    def display_name(self):
        return "[" + self.inner_type.display_name + "]"

    def type_check_method(self, context, value):
        value_check = _fail_if_not_of_type(value, list, "list")
        if not value_check.success:
            return value_check

        for item in value:
            item_check = self.inner_type.type_check(context, item)
            if not item_check.success:
                return item_check

        return TypeCheck(success=True)

    @property
    def inner_types(self):
        return [self.inner_type] + self.inner_type.inner_types

    @property
    def type_param_keys(self):
        return [self.inner_type.key]

    @property
    def supports_fan_in(self):
        return True

    def get_inner_type_for_fan_in(self):
        return self.inner_type


class DagsterListApi:
    def __getitem__(self, inner_type):
        check.not_none_param(inner_type, "inner_type")
        return _List(resolve_dagster_type(inner_type))

    def __call__(self, inner_type):
        check.not_none_param(inner_type, "inner_type")
        return _List(inner_type)


List = DagsterListApi()


def _List(inner_type):
    check.inst_param(inner_type, "inner_type", DagsterType)
    if inner_type is Nothing:
        raise DagsterInvalidDefinitionError("Type Nothing can not be wrapped in List or Optional")
    return ListType(inner_type)


class Stringish(DagsterType):
    def __init__(self, key=None, name=None, **kwargs):
        name = check.opt_str_param(name, "name", type(self).__name__)
        key = check.opt_str_param(key, "key", name)
        super(Stringish, self).__init__(
            key=key,
            name=name,
            kind=DagsterTypeKind.SCALAR,
            type_check_fn=self.type_check_method,
            loader=BuiltinSchemas.STRING_INPUT,
            materializer=BuiltinSchemas.STRING_OUTPUT,
            **kwargs,
        )

    def type_check_method(self, _context, value):
        return _fail_if_not_of_type(value, str, "string")


def create_string_type(name, description=None):
    return Stringish(name=name, key=name, description=description)


Any = _Any()
Bool = _Bool()
Float = _Float()
Int = _Int()
String = _String()
Nothing = _Nothing()

_RUNTIME_MAP = {
    BuiltinEnum.ANY: Any,
    BuiltinEnum.BOOL: Bool,
    BuiltinEnum.FLOAT: Float,
    BuiltinEnum.INT: Int,
    BuiltinEnum.STRING: String,
    BuiltinEnum.NOTHING: Nothing,
}

_PYTHON_TYPE_TO_DAGSTER_TYPE_MAPPING_REGISTRY: typing.Dict[type, DagsterType] = {}
"""Python types corresponding to user-defined RunTime types created using @map_to_dagster_type or
as_dagster_type are registered here so that we can remap the Python types to runtime types."""


def make_python_type_usable_as_dagster_type(
    python_type: typing.Type, dagster_type: DagsterType
) -> None:
    """
    Take any existing python type and map it to a dagster type (generally created with
    :py:class:`DagsterType <dagster.DagsterType>`) This can only be called once
    on a given python type.
    """
    check.inst_param(python_type, "python_type", type)
    check.inst_param(dagster_type, "dagster_type", DagsterType)
    registered_dagster_type = _PYTHON_TYPE_TO_DAGSTER_TYPE_MAPPING_REGISTRY.get(python_type)

    if registered_dagster_type is None:
        _PYTHON_TYPE_TO_DAGSTER_TYPE_MAPPING_REGISTRY[python_type] = dagster_type
    elif registered_dagster_type is not dagster_type:
        # This would be just a great place to insert a short URL pointing to the type system
        # documentation into the error message
        # https://github.com/dagster-io/dagster/issues/1831
        if isinstance(registered_dagster_type, TypeHintInferredDagsterType):
            raise DagsterInvalidDefinitionError(
                f"A Dagster type has already been registered for the Python type "
                f'{python_type}. The Dagster type was "auto-registered" - i.e. a solid definition '
                f"used the Python type as an annotation for one of its arguments or for its return "
                f"value before make_python_type_usable_as_dagster_type was called, and we "
                f"generated a Dagster type to correspond to it. To override the auto-generated "
                f"Dagster type, call make_python_type_usable_as_dagster_type before any solid "
                f"definitions refer to the Python type."
            )
        else:
            raise DagsterInvalidDefinitionError(
                f"A Dagster type has already been registered for the Python type "
                f"{python_type}. make_python_type_usable_as_dagster_type can only "
                f"be called once on a python type as it is registering a 1:1 mapping "
                f"between that python type and a dagster type."
            )


DAGSTER_INVALID_TYPE_ERROR_MESSAGE = (
    "Invalid type: dagster_type must be an instance of DagsterType or a Python type: "
    "got {dagster_type}{additional_msg}"
)


class TypeHintInferredDagsterType(DagsterType):
    def __init__(self, python_type: typing.Type):
        qualified_name = f"{python_type.__module__}.{python_type.__name__}"
        self.python_type = python_type
        super(TypeHintInferredDagsterType, self).__init__(
            key=f"_TypeHintInferred[{qualified_name}]",
            description=f"DagsterType created from a type hint for the Python type {qualified_name}",
            type_check_fn=isinstance_type_check_fn(
                python_type, python_type.__name__, qualified_name
            ),
        )

    @property
    def display_name(self) -> str:
        return self.python_type.__name__


def resolve_dagster_type(dagster_type):
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
        "Cannot resolve a config type to a runtime type",
    )

    check.invariant(
        not (isinstance(dagster_type, type) and issubclass(dagster_type, DagsterType)),
        "Do not pass runtime type classes. Got {}".format(dagster_type),
    )

    # First check to see if it part of python's typing library
    if is_typing_type(dagster_type):
        dagster_type = transform_typing_type(dagster_type)

    if isinstance(dagster_type, DagsterType):
        return dagster_type

    # Test for unhashable objects -- this is if, for instance, someone has passed us an instance of
    # a dict where they meant to pass dict or Dict, etc.
    try:
        hash(dagster_type)
    except TypeError:
        raise DagsterInvalidDefinitionError(
            DAGSTER_INVALID_TYPE_ERROR_MESSAGE.format(
                additional_msg=(
                    ", which isn't hashable. Did you pass an instance of a type instead of "
                    "the type?"
                ),
                dagster_type=str(dagster_type),
            )
        )

    if is_supported_runtime_python_builtin(dagster_type):
        return remap_python_builtin_for_runtime(dagster_type)

    if dagster_type is None:
        return Any

    if dagster_type is Dict:
        return PythonDict
    if isinstance(dagster_type, DagsterTupleApi):
        return PythonTuple
    if isinstance(dagster_type, DagsterSetApi):
        return PythonSet
    if isinstance(dagster_type, DagsterListApi):
        return List(Any)
    if BuiltinEnum.contains(dagster_type):
        return DagsterType.from_builtin_enum(dagster_type)

    if isinstance(dagster_type, type):
        return resolve_python_type_to_dagster_type(dagster_type)

    raise DagsterInvalidDefinitionError(
        DAGSTER_INVALID_TYPE_ERROR_MESSAGE.format(
            dagster_type=str(dagster_type), additional_msg="."
        )
    )


def resolve_python_type_to_dagster_type(python_type: typing.Type) -> DagsterType:
    """
    Resolves a Python type to a Dagster type.
    """
    check.inst_param(python_type, "python_type", type)

    if python_type in _PYTHON_TYPE_TO_DAGSTER_TYPE_MAPPING_REGISTRY:
        return _PYTHON_TYPE_TO_DAGSTER_TYPE_MAPPING_REGISTRY[python_type]
    else:
        dagster_type = TypeHintInferredDagsterType(python_type)
        _PYTHON_TYPE_TO_DAGSTER_TYPE_MAPPING_REGISTRY[python_type] = dagster_type
        return dagster_type


ALL_RUNTIME_BUILTINS = list(_RUNTIME_MAP.values())


def construct_dagster_type_dictionary(solid_defs):
    type_dict_by_name = {t.unique_name: t for t in ALL_RUNTIME_BUILTINS}
    type_dict_by_key = {t.key: t for t in ALL_RUNTIME_BUILTINS}
    for solid_def in solid_defs:
        for dagster_type in solid_def.all_dagster_types():
            # We don't do uniqueness check on key because with classes
            # like Array, Noneable, etc, those are ephemeral objects
            # and it is perfectly fine to have many of them.
            type_dict_by_key[dagster_type.key] = dagster_type

            if not dagster_type.has_unique_name:
                continue

            if dagster_type.unique_name not in type_dict_by_name:
                type_dict_by_name[dagster_type.unique_name] = dagster_type
                continue

            if type_dict_by_name[dagster_type.unique_name] is not dagster_type:
                raise DagsterInvalidDefinitionError(
                    (
                        'You have created two dagster types with the same name "{type_name}". '
                        "Dagster types have must have unique names."
                    ).format(type_name=dagster_type.display_name)
                )

    return type_dict_by_key


class DagsterOptionalApi:
    def __getitem__(self, inner_type):
        check.not_none_param(inner_type, "inner_type")
        return OptionalType(inner_type)


Optional = DagsterOptionalApi()
