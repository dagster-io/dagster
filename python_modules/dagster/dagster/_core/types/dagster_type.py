import typing as t
from abc import abstractmethod
from enum import Enum as PythonEnum
from functools import partial
from typing import (
    AbstractSet as TypingAbstractSet,
)
from typing import (
    AnyStr,
    Mapping,
    Sequence,
    cast,
)
from typing import (
    Iterator as TypingIterator,
)
from typing import (
    Type as TypingType,
)

from dagster_shared.seven import is_subclass
from typing_extensions import get_args, get_origin

import dagster._check as check
from dagster._annotations import public
from dagster._builtins import BuiltinEnum
from dagster._config import (
    Array,
    ConfigType,
)
from dagster._config import (
    Noneable as ConfigNoneable,
)
from dagster._core.definitions.events import DynamicOutput, Output, TypeCheck
from dagster._core.definitions.metadata import (
    MetadataValue,
    RawMetadataValue,
    normalize_metadata,
)
from dagster._core.definitions.resource_requirement import (
    ResourceRequirement,
    TypeResourceRequirement,
)
from dagster._core.definitions.result import MaterializeResult
from dagster._core.definitions.utils import NoValueSentinel
from dagster._core.errors import (
    DagsterInvalidDefinitionError,
    DagsterInvariantViolationError,
)
from dagster._core.types.builtin_config_schemas import BuiltinSchemas
from dagster._core.types.config_schema import DagsterTypeLoader
from dagster._serdes import whitelist_for_serdes

if t.TYPE_CHECKING:
    from dagster._core.definitions.node_definition import NodeDefinition
    from dagster._core.execution.context.system import (
        DagsterTypeLoaderContext,
        TypeCheckContext,
    )

TypeCheckFn = t.Callable[["TypeCheckContext", AnyStr], t.Union[TypeCheck, bool]]


@whitelist_for_serdes
class DagsterTypeKind(PythonEnum):
    ANY = "ANY"
    SCALAR = "SCALAR"
    LIST = "LIST"
    NOTHING = "NOTHING"
    NULLABLE = "NULLABLE"
    REGULAR = "REGULAR"


@public
class DagsterType:
    """Define a type in dagster. These can be used in the inputs and outputs of ops.

    Args:
        type_check_fn (Callable[[TypeCheckContext, Any], [Union[bool, TypeCheck]]]):
            The function that defines the type check. It takes the value flowing
            through the input or output of the op. If it passes, return either
            ``True`` or a :py:class:`~dagster.TypeCheck` with ``success`` set to ``True``. If it fails,
            return either ``False`` or a :py:class:`~dagster.TypeCheck` with ``success`` set to ``False``.
            The first argument must be named ``context`` (or, if unused, ``_``, ``_context``, or ``context_``).
            Use ``required_resource_keys`` for access to resources.
        key (Optional[str]): The unique key to identify types programmatically.
            The key property always has a value. If you omit key to the argument
            to the init function, it instead receives the value of ``name``. If
            neither ``key`` nor ``name`` is provided, a ``CheckError`` is thrown.

            In the case of a generic type such as ``List`` or ``Optional``, this is
            generated programmatically based on the type parameters.

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
        required_resource_keys (Optional[Set[str]]): Resource keys required by the ``type_check_fn``.
        is_builtin (bool): Defaults to False. This is used by tools to display or
            filter built-in types (such as :py:class:`~dagster.String`, :py:class:`~dagster.Int`) to visually distinguish
            them from user-defined types. Meant for internal use.
        kind (DagsterTypeKind): Defaults to None. This is used to determine the kind of runtime type
            for InputDefinition and OutputDefinition type checking.
        typing_type: Defaults to None. A valid python typing type (e.g. Optional[List[int]]) for the
            value contained within the DagsterType. Meant for internal use.
    """

    def __init__(
        self,
        type_check_fn: TypeCheckFn,
        key: t.Optional[str] = None,
        name: t.Optional[str] = None,
        is_builtin: bool = False,
        description: t.Optional[str] = None,
        loader: t.Optional[DagsterTypeLoader] = None,
        required_resource_keys: t.Optional[t.Set[str]] = None,
        kind: DagsterTypeKind = DagsterTypeKind.REGULAR,
        typing_type: t.Any = t.Any,
        metadata: t.Optional[t.Mapping[str, RawMetadataValue]] = None,
    ):
        check.opt_str_param(key, "key")
        check.opt_str_param(name, "name")

        check.invariant(not (name is None and key is None), "Must set key or name")
        if name is None:
            key = check.not_none(
                key,
                "If name is not provided, must provide key.",
            )
            self.key, self._name = key, None
        elif key is None:
            name = check.not_none(
                name,
                "If key is not provided, must provide name.",
            )
            self.key, self._name = name, name
        else:
            check.invariant(key and name)
            self.key, self._name = key, name

        self._description = check.opt_str_param(description, "description")
        self._loader = check.opt_inst_param(loader, "loader", DagsterTypeLoader)

        self._required_resource_keys = check.opt_set_param(
            required_resource_keys,
            "required_resource_keys",
        )

        self._type_check_fn = check.callable_param(type_check_fn, "type_check_fn")
        _validate_type_check_fn(self._type_check_fn, self._name)

        self.is_builtin = check.bool_param(is_builtin, "is_builtin")
        check.invariant(
            self.display_name is not None,
            f"All types must have a valid display name, got None for key {key}",
        )

        self.kind = check.inst_param(kind, "kind", DagsterTypeKind)

        self._typing_type = typing_type

        self._metadata = normalize_metadata(
            check.opt_mapping_param(metadata, "metadata", key_type=str),
        )

    @public
    def type_check(self, context: "TypeCheckContext", value: object) -> TypeCheck:
        """Type check the value against the type.

        Args:
            context (TypeCheckContext): The context of the type check.
            value (Any): The value to check.

        Returns:
            TypeCheck: The result of the type check.
        """
        retval = self._type_check_fn(context, value)

        if not isinstance(retval, (bool, TypeCheck)):
            raise DagsterInvariantViolationError(
                f"You have returned {retval!r} of type {type(retval)} from the type "
                f'check function of type "{self.key}". Return value must be instance '
                "of TypeCheck or a bool."
            )

        return TypeCheck(success=retval) if isinstance(retval, bool) else retval

    def __eq__(self, other):
        return isinstance(other, DagsterType) and self.key == other.key

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return hash(self.key)

    @staticmethod
    def from_builtin_enum(builtin_enum) -> "DagsterType":
        check.invariant(
            BuiltinEnum.contains(builtin_enum), "must be member of BuiltinEnum"
        )
        return _RUNTIME_MAP[builtin_enum]

    @property
    def metadata(self) -> t.Mapping[str, MetadataValue]:
        return self._metadata

    @public
    @property
    def required_resource_keys(self) -> TypingAbstractSet[str]:
        """AbstractSet[str]: Set of resource keys required by the type check function."""
        return self._required_resource_keys

    @public
    @property
    def display_name(self) -> str:
        """Either the name or key (if name is `None`) of the type, overridden in many subclasses."""
        return cast(str, self._name or self.key)

    @public
    @property
    def unique_name(self) -> t.Optional[str]:
        """The unique name of this type. Can be None if the type is not unique, such as container types."""
        # TODO: docstring and body inconsistent-- can this be None or not?
        check.invariant(
            self._name is not None,
            f"unique_name requested but is None for type {self.display_name}",
        )
        return self._name

    @public
    @property
    def has_unique_name(self) -> bool:
        """bool: Whether the type has a unique name."""
        return self._name is not None

    @public
    @property
    def typing_type(self) -> t.Any:
        """Any: The python typing type for this type."""
        return self._typing_type

    @public
    @property
    def loader(self) -> t.Optional[DagsterTypeLoader]:
        """Optional[DagsterTypeLoader]: Loader for this type, if any."""
        return self._loader

    @public
    @property
    def description(self) -> t.Optional[str]:
        """Optional[str]: Description of the type, or None if not provided."""
        return self._description

    @property
    def inner_types(self) -> t.Sequence["DagsterType"]:
        return []

    @property
    def loader_schema_key(self) -> t.Optional[str]:
        return self.loader.schema_type.key if self.loader else None

    @property
    def type_param_keys(self) -> t.Sequence[str]:
        return []

    @property
    def is_nothing(self) -> bool:
        return self.kind == DagsterTypeKind.NOTHING

    @property
    def is_any(self) -> bool:
        return self.kind == DagsterTypeKind.ANY

    @property
    def supports_fan_in(self) -> bool:
        return False

    def get_inner_type_for_fan_in(self) -> "DagsterType":
        check.failed(
            f"DagsterType {self.display_name} does not support fan-in, should have checked supports_fan_in before"
            " calling getter."
        )

    def get_resource_requirements(self) -> TypingIterator[ResourceRequirement]:
        for resource_key in sorted(list(self.required_resource_keys)):
            yield TypeResourceRequirement(
                key=resource_key, type_display_name=self.display_name
            )
        if self.loader:
            yield from self.loader.get_resource_requirements(
                type_display_name=self.display_name
            )


def _validate_type_check_fn(fn: t.Callable, name: t.Optional[str]) -> bool:
    from dagster_shared.seven import get_arg_names

    args = get_arg_names(fn)

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
                f'type_check function on type "{name}" must have first '
                'argument named "context" (or _, _context, context_).'
            )
        return True

    raise DagsterInvalidDefinitionError(
        f'type_check_fn argument on type "{name}" must take 2 arguments, received {len(args)}.'
    )


class BuiltinScalarDagsterType(DagsterType):
    def __init__(
        self, name: str, type_check_fn: TypeCheckFn, typing_type: t.Type, **kwargs
    ):
        super(BuiltinScalarDagsterType, self).__init__(
            key=name,
            name=name,
            kind=DagsterTypeKind.SCALAR,
            type_check_fn=type_check_fn,
            is_builtin=True,
            typing_type=typing_type,
            **kwargs,
        )

    # This is passed to the constructor of subclasses as the argument `type_check_fn`-- that's why
    # it exists together with the `type_check_fn` arg.
    def type_check_fn(self, _context, value) -> TypeCheck:
        return self.type_check_scalar_value(value)

    @abstractmethod
    def type_check_scalar_value(self, _value) -> TypeCheck:
        raise NotImplementedError()


def _typemismatch_error_str(value: object, expected_type_desc: str) -> str:
    return f'Value "{value}" of python type "{type(value).__name__}" must be a {expected_type_desc}.'


def _fail_if_not_of_type(
    value: object, value_type: t.Type[t.Any], value_type_desc: str
) -> TypeCheck:
    if not isinstance(value, value_type):
        return TypeCheck(
            success=False, description=_typemismatch_error_str(value, value_type_desc)
        )

    return TypeCheck(success=True)


class _Int(BuiltinScalarDagsterType):
    def __init__(self):
        super(_Int, self).__init__(
            name="Int",
            loader=BuiltinSchemas.INT_INPUT,
            type_check_fn=self.type_check_fn,
            typing_type=int,
        )

    def type_check_scalar_value(self, value) -> TypeCheck:
        return _fail_if_not_of_type(value, int, "int")


class _String(BuiltinScalarDagsterType):
    def __init__(self):
        super(_String, self).__init__(
            name="String",
            loader=BuiltinSchemas.STRING_INPUT,
            type_check_fn=self.type_check_fn,
            typing_type=str,
        )

    def type_check_scalar_value(self, value: object) -> TypeCheck:
        return _fail_if_not_of_type(value, str, "string")


class _Float(BuiltinScalarDagsterType):
    def __init__(self):
        super(_Float, self).__init__(
            name="Float",
            loader=BuiltinSchemas.FLOAT_INPUT,
            type_check_fn=self.type_check_fn,
            typing_type=float,
        )

    def type_check_scalar_value(self, value: object) -> TypeCheck:
        return _fail_if_not_of_type(value, float, "float")


class _Bool(BuiltinScalarDagsterType):
    def __init__(self):
        super(_Bool, self).__init__(
            name="Bool",
            loader=BuiltinSchemas.BOOL_INPUT,
            type_check_fn=self.type_check_fn,
            typing_type=bool,
        )

    def type_check_scalar_value(self, value: object) -> TypeCheck:
        return _fail_if_not_of_type(value, bool, "bool")


class Anyish(DagsterType):
    def __init__(
        self,
        key: t.Optional[str],
        name: t.Optional[str],
        loader: t.Optional[DagsterTypeLoader] = None,
        is_builtin: bool = False,
        description: t.Optional[str] = None,
    ):
        super(Anyish, self).__init__(
            key=key,
            name=name,
            kind=DagsterTypeKind.ANY,
            loader=loader,
            is_builtin=is_builtin,
            type_check_fn=self.type_check_method,
            description=description,
            typing_type=t.Any,
        )

    def type_check_method(
        self, _context: "TypeCheckContext", _value: object
    ) -> TypeCheck:
        return TypeCheck(success=True)

    @property
    def supports_fan_in(self) -> bool:
        return True

    def get_inner_type_for_fan_in(self) -> DagsterType:
        # Anyish all the way down
        return self


class _Any(Anyish):
    def __init__(self):
        super(_Any, self).__init__(
            key="Any",
            name="Any",
            loader=BuiltinSchemas.ANY_INPUT,
            is_builtin=True,
        )


def create_any_type(
    name: str,
    loader: t.Optional[DagsterTypeLoader] = None,
    description: t.Optional[str] = None,
) -> Anyish:
    return Anyish(
        key=name,
        name=name,
        description=description,
        loader=loader,
    )


class _Nothing(DagsterType):
    def __init__(self):
        super(_Nothing, self).__init__(
            key="Nothing",
            name="Nothing",
            kind=DagsterTypeKind.NOTHING,
            loader=None,
            type_check_fn=self.type_check_method,
            is_builtin=True,
            typing_type=type(None),
        )

    def type_check_method(
        self, _context: "TypeCheckContext", value: object
    ) -> TypeCheck:
        if value is not None and value != NoValueSentinel:
            return TypeCheck(
                success=False,
                description=f"Value must be None or unset, got a {type(value)}",
            )

        return TypeCheck(success=True)

    @property
    def supports_fan_in(self) -> bool:
        return True

    def get_inner_type_for_fan_in(self) -> DagsterType:
        return self


def isinstance_type_check_fn(
    expected_python_type: t.Union[t.Type, t.Tuple[t.Type, ...]],
    dagster_type_name: str,
    expected_python_type_str: str,
) -> TypeCheckFn:
    def type_check(_context: "TypeCheckContext", value: object) -> TypeCheck:
        if not isinstance(value, expected_python_type):
            return TypeCheck(
                success=False,
                description=(
                    f"Value of type {type(value)} failed type check for Dagster type"
                    f" {dagster_type_name}, expected value to be of Python type"
                    f" {expected_python_type_str}."
                ),
            )

        return TypeCheck(success=True)

    return type_check


@public
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
    """

    def __init__(
        self,
        python_type: t.Union[t.Type, t.Tuple[t.Type, ...]],
        key: t.Optional[str] = None,
        name: t.Optional[str] = None,
        **kwargs,
    ):
        if isinstance(python_type, tuple):
            self.python_type = check.tuple_param(
                python_type, "python_type", of_shape=tuple(type for item in python_type)
            )
            self.type_str = "Union[{}]".format(
                ", ".join(python_type.__name__ for python_type in python_type)
            )
            typing_type = t.Union[python_type]  # type: ignore

        else:
            self.python_type = check.class_param(python_type, "python_type")
            self.type_str = cast(str, python_type.__name__)
            typing_type = self.python_type
        name = check.opt_str_param(name, "name", self.type_str)
        key = check.opt_str_param(key, "key", name)
        super(PythonObjectDagsterType, self).__init__(
            key=key,
            name=name,
            type_check_fn=isinstance_type_check_fn(python_type, name, self.type_str),
            typing_type=typing_type,
            **kwargs,
        )


class NoneableInputSchema(DagsterTypeLoader):
    def __init__(self, inner_dagster_type: DagsterType):
        self._inner_dagster_type = check.inst_param(
            inner_dagster_type, "inner_dagster_type", DagsterType
        )
        self._inner_loader = check.not_none_param(
            inner_dagster_type.loader, "inner_dagster_type"
        )
        self._schema_type = ConfigNoneable(self._inner_loader.schema_type)

    @property
    def schema_type(self) -> ConfigType:
        return self._schema_type

    def construct_from_config_value(
        self, context: "DagsterTypeLoaderContext", config_value: object
    ) -> object:
        if config_value is None:
            return None
        return self._inner_loader.construct_from_config_value(context, config_value)


def _create_nullable_input_schema(
    inner_type: DagsterType,
) -> t.Optional[DagsterTypeLoader]:
    if not inner_type.loader:
        return None

    return NoneableInputSchema(inner_type)


class OptionalType(DagsterType):
    def __init__(self, inner_type: DagsterType):
        inner_type = resolve_dagster_type(inner_type)

        if inner_type is Nothing:
            raise DagsterInvalidDefinitionError(
                "Type Nothing can not be wrapped in List or Optional"
            )

        key = "Optional." + cast(str, inner_type.key)
        self.inner_type = inner_type
        super(OptionalType, self).__init__(
            key=key,
            name=None,
            kind=DagsterTypeKind.NULLABLE,
            type_check_fn=self.type_check_method,
            loader=_create_nullable_input_schema(inner_type),
            # This throws a type error with Py
            typing_type=t.Optional[inner_type.typing_type],
        )

    @property
    def display_name(self) -> str:
        return self.inner_type.display_name + "?"

    def type_check_method(self, context, value):
        return (
            TypeCheck(success=True)
            if value is None
            else self.inner_type.type_check(context, value)
        )

    @property
    def inner_types(self):
        return [self.inner_type] + self.inner_type.inner_types  # pyright: ignore[reportOperatorIssue]

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
        convert_item = partial(
            self._inner_dagster_type.loader.construct_from_config_value, context
        )
        return list(map(convert_item, config_value))


def _create_list_input_schema(inner_type):
    if not inner_type.loader:
        return None

    return ListInputSchema(inner_type)


class ListType(DagsterType):
    def __init__(self, inner_type: DagsterType):
        key = "List." + inner_type.key
        self.inner_type = inner_type
        super(ListType, self).__init__(
            key=key,
            name=None,
            kind=DagsterTypeKind.LIST,
            type_check_fn=self.type_check_method,
            loader=_create_list_input_schema(inner_type),
            typing_type=t.List[inner_type.typing_type],
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
        return [self.inner_type] + self.inner_type.inner_types  # pyright: ignore[reportOperatorIssue]

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


List: DagsterListApi = DagsterListApi()


def _List(inner_type):
    check.inst_param(inner_type, "inner_type", DagsterType)
    if inner_type is Nothing:
        raise DagsterInvalidDefinitionError(
            "Type Nothing can not be wrapped in List or Optional"
        )
    return ListType(inner_type)


class Stringish(DagsterType):
    def __init__(
        self, key: t.Optional[str] = None, name: t.Optional[str] = None, **kwargs
    ):
        name = check.opt_str_param(name, "name", type(self).__name__)
        key = check.opt_str_param(key, "key", name)
        super(Stringish, self).__init__(
            key=key,
            name=name,
            kind=DagsterTypeKind.SCALAR,
            type_check_fn=self.type_check_method,
            loader=BuiltinSchemas.STRING_INPUT,
            typing_type=str,
            **kwargs,
        )

    def type_check_method(
        self, _context: "TypeCheckContext", value: object
    ) -> TypeCheck:
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

_PYTHON_TYPE_TO_DAGSTER_TYPE_MAPPING_REGISTRY: t.Dict[type, DagsterType] = {}
"""Python types corresponding to user-defined RunTime types created using @map_to_dagster_type or
as_dagster_type are registered here so that we can remap the Python types to runtime types."""


@public
def make_python_type_usable_as_dagster_type(
    python_type: TypingType[t.Any], dagster_type: DagsterType
) -> None:
    """Take any existing python type and map it to a dagster type (generally created with
    :py:class:`DagsterType <dagster.DagsterType>`) This can only be called once
    on a given python type.
    """
    check.inst_param(python_type, "python_type", type)
    check.inst_param(dagster_type, "dagster_type", DagsterType)
    registered_dagster_type = _PYTHON_TYPE_TO_DAGSTER_TYPE_MAPPING_REGISTRY.get(
        python_type
    )

    if registered_dagster_type is None:
        _PYTHON_TYPE_TO_DAGSTER_TYPE_MAPPING_REGISTRY[python_type] = dagster_type
    elif registered_dagster_type is not dagster_type:
        # This would be just a great place to insert a short URL pointing to the type system
        # documentation into the error message
        # https://github.com/dagster-io/dagster/issues/1831
        if isinstance(registered_dagster_type, TypeHintInferredDagsterType):
            raise DagsterInvalidDefinitionError(
                "A Dagster type has already been registered for the Python type "
                f'{python_type}. The Dagster type was "auto-registered" - i.e. a solid definition '
                "used the Python type as an annotation for one of its arguments or for its return "
                "value before make_python_type_usable_as_dagster_type was called, and we "
                "generated a Dagster type to correspond to it. To override the auto-generated "
                "Dagster type, call make_python_type_usable_as_dagster_type before any solid "
                "definitions refer to the Python type."
            )
        else:
            raise DagsterInvalidDefinitionError(
                "A Dagster type has already been registered for the Python type "
                f"{python_type}. make_python_type_usable_as_dagster_type can only "
                "be called once on a python type as it is registering a 1:1 mapping "
                "between that python type and a dagster type."
            )


DAGSTER_INVALID_TYPE_ERROR_MESSAGE = (
    "Invalid type: dagster_type must be an instance of DagsterType or a Python type: "
    "got {dagster_type}{additional_msg}"
)


class TypeHintInferredDagsterType(DagsterType):
    def __init__(self, python_type: t.Type):
        qualified_name = f"{python_type.__module__}.{python_type.__name__}"
        self.python_type = python_type
        super(TypeHintInferredDagsterType, self).__init__(
            key=f"_TypeHintInferred[{qualified_name}]",
            description=(
                f"DagsterType created from a type hint for the Python type {qualified_name}"
            ),
            type_check_fn=isinstance_type_check_fn(
                python_type, python_type.__name__, qualified_name
            ),
            typing_type=python_type,
        )

    @property
    def display_name(self) -> str:
        return self.python_type.__name__


def resolve_dagster_type(dagster_type: object) -> DagsterType:
    # circular dep
    from dagster._core.definitions.result import MaterializeResult, ObserveResult
    from dagster._core.types.primitive_mapping import (
        is_supported_runtime_python_builtin,
        remap_python_builtin_for_runtime,
    )
    from dagster._core.types.python_dict import (
        Dict as DDict,
    )
    from dagster._core.types.python_dict import (
        PythonDict,
    )
    from dagster._core.types.python_set import DagsterSetApi, PythonSet
    from dagster._core.types.python_tuple import DagsterTupleApi, PythonTuple
    from dagster._core.types.transform_typing import transform_typing_type
    from dagster._utils.typing_api import is_typing_type

    check.invariant(
        not (isinstance(dagster_type, type) and is_subclass(dagster_type, ConfigType)),
        "Cannot resolve a config type to a runtime type",
    )

    check.invariant(
        not (isinstance(dagster_type, type) and is_subclass(dagster_type, DagsterType)),
        f"Do not pass runtime type classes. Got {dagster_type}",
    )

    # First, check to see if we're using Dagster's generic output type to do the type catching.
    if is_generic_output_annotation(
        dagster_type
    ) or is_generic_materialize_result_annotation(dagster_type):
        type_args = get_args(dagster_type)
        # If no inner type was provided, forward Any type.
        dagster_type = type_args[0] if len(type_args) == 1 else Any
    elif is_dynamic_output_annotation(dagster_type):
        dynamic_out_annotation = get_args(dagster_type)[0]
        type_args = get_args(dynamic_out_annotation)
        dagster_type = type_args[0] if len(type_args) == 1 else Any
    elif dagster_type == MaterializeResult:
        dagster_type = Any
    elif dagster_type == ObserveResult:
        # ObserveResult does not include a value
        dagster_type = Nothing

    # Then, check to see if it is part of python's typing library
    if is_typing_type(dagster_type):
        dagster_type = transform_typing_type(dagster_type)
    if isinstance(dagster_type, DagsterType):
        return dagster_type

    # Test for unhashable objects -- this is if, for instance, someone has passed us an instance of
    # a dict where they meant to pass dict or Dict, etc.
    try:
        hash(dagster_type)
    except TypeError as e:
        raise DagsterInvalidDefinitionError(
            DAGSTER_INVALID_TYPE_ERROR_MESSAGE.format(
                additional_msg=(
                    ", which isn't hashable. Did you pass an instance of a type instead of "
                    "the type?"
                ),
                dagster_type=str(dagster_type),
            )
        ) from e

    if BuiltinEnum.contains(dagster_type):
        return DagsterType.from_builtin_enum(dagster_type)

    if is_supported_runtime_python_builtin(dagster_type):
        return remap_python_builtin_for_runtime(dagster_type)

    if dagster_type is None:
        return Any

    if dagster_type is DDict:
        return PythonDict
    if isinstance(dagster_type, DagsterTupleApi):
        return PythonTuple
    if isinstance(dagster_type, DagsterSetApi):
        return PythonSet
    if isinstance(dagster_type, DagsterListApi):
        return List(Any)

    if isinstance(dagster_type, type):
        return resolve_python_type_to_dagster_type(dagster_type)

    raise DagsterInvalidDefinitionError(
        DAGSTER_INVALID_TYPE_ERROR_MESSAGE.format(
            dagster_type=str(dagster_type), additional_msg="."
        )
    )


def is_dynamic_output_annotation(dagster_type: object) -> bool:
    check.invariant(
        not (isinstance(dagster_type, type) and is_subclass(dagster_type, ConfigType)),
        "Cannot resolve a config type to a runtime type",
    )

    check.invariant(
        not (isinstance(dagster_type, type) and is_subclass(dagster_type, ConfigType)),
        f"Do not pass runtime type classes. Got {dagster_type}",
    )

    if dagster_type == DynamicOutput or get_origin(dagster_type) == DynamicOutput:
        raise DagsterInvariantViolationError(
            "Op annotated with return type DynamicOutput. DynamicOutputs can only be returned in"
            " the context of a List. If only one output is needed, use the Output API."
        )

    if get_origin(dagster_type) == list and len(get_args(dagster_type)) == 1:  # noqa: E721
        list_inner_type = get_args(dagster_type)[0]
        return (
            list_inner_type == DynamicOutput
            or get_origin(list_inner_type) == DynamicOutput
        )
    return False


def is_generic_output_annotation(dagster_type: object) -> bool:
    return dagster_type == Output or get_origin(dagster_type) == Output


def is_generic_materialize_result_annotation(dagster_type: object) -> bool:
    return (
        dagster_type == MaterializeResult
        or get_origin(dagster_type) == MaterializeResult
    )


def resolve_python_type_to_dagster_type(python_type: t.Type) -> DagsterType:
    """Resolves a Python type to a Dagster type."""
    check.inst_param(python_type, "python_type", type)

    if python_type in _PYTHON_TYPE_TO_DAGSTER_TYPE_MAPPING_REGISTRY:
        return _PYTHON_TYPE_TO_DAGSTER_TYPE_MAPPING_REGISTRY[python_type]
    else:
        dagster_type = TypeHintInferredDagsterType(python_type)
        _PYTHON_TYPE_TO_DAGSTER_TYPE_MAPPING_REGISTRY[python_type] = dagster_type
        return dagster_type


ALL_RUNTIME_BUILTINS = list(_RUNTIME_MAP.values())


def construct_dagster_type_dictionary(
    node_defs: Sequence["NodeDefinition"],
) -> Mapping[str, DagsterType]:
    from dagster._core.definitions.graph_definition import GraphDefinition

    type_dict_by_name = {t.unique_name: t for t in ALL_RUNTIME_BUILTINS}
    type_dict_by_key = {t.key: t for t in ALL_RUNTIME_BUILTINS}

    def process_node_def(node_def: "NodeDefinition"):
        input_output_types = list(node_def.all_input_output_types())
        for dagster_type in input_output_types:
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
                        f'You have created two dagster types with the same name "{dagster_type.display_name}". '
                        "Dagster types have must have unique names."
                    )
                )

        if isinstance(node_def, GraphDefinition):
            for child_node_def in node_def.node_defs:
                process_node_def(child_node_def)

    for node_def in node_defs:
        process_node_def(node_def)

    return type_dict_by_key


class DagsterOptionalApi:
    def __getitem__(self, inner_type: t.Union[t.Type, DagsterType]) -> OptionalType:
        inner_type = resolve_dagster_type(
            check.not_none_param(inner_type, "inner_type")
        )
        return OptionalType(inner_type)


Optional: DagsterOptionalApi = DagsterOptionalApi()
