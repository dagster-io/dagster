import collections.abc
import inspect
from collections.abc import Generator, Iterable, Iterator, Mapping, Sequence
from os import PathLike, fspath
from typing import (  # noqa: UP035
    AbstractSet,
    Any,
    Callable,
    NoReturn,
    Optional,
    TypeVar,
    Union,
    overload,
)

from dagster_shared.check.record import is_record

TypeOrTupleOfTypes = Union[type, tuple[type, ...]]
Numeric = Union[int, float]
T = TypeVar("T")
U = TypeVar("U")
V = TypeVar("V")

TTypeOrTupleOfTTypes = Union[type[T], tuple[type[T], ...]]


# This module contains runtime type-checking code used throughout Dagster. It is divided into three
# sections:
#
# - TYPE CHECKS: functions that check the type of a single value
# - OTHER CHECKS: functions that check conditions other than the type of a single value
# - ERRORS/UTILITY: error generation code and other utility functions invoked by the check functions
#
# TYPE CHECKS is divided into subsections for each type (e.g. bool, list). Each subsection contains
# multiple functions that implement the same check logic, but differ in how the target value is
# extracted and how the error message is generated. Call this dimension the "check context". Check
# contexts are:
#
# - Parameter checks (`<type>_param`): Used to type-check the arguments to a function, typically
#   before any business logic executes.
# - Element checks (`<type>_elem`): Used to type-check an element of a dictionary under a specific
#   key.
# - General checks (`[is_]<type>`): Used to type-check a value in an arbitrary context. When the
#   function name would conflict with a python built-in, the prefix `is_` is used to disambiguate--
#   e.g. we have `check.is_list` instead of `check.list`.
#
# Using the right check for the calling context ensures an appropriate error message can be generated.

# ###################################################################################################
# ##### TYPE CHECKS
# ###################################################################################################

# ########################
# ##### BOOL
# ########################


def bool_param(obj: object, param_name: str, additional_message: Optional[str] = None) -> bool:
    if not isinstance(obj, bool):
        raise _param_type_mismatch_exception(obj, bool, param_name, additional_message)
    return obj


@overload
def opt_bool_param(
    obj: object, param_name: str, default: bool, additional_message: Optional[str] = None
) -> bool: ...


@overload
def opt_bool_param(
    obj: object,
    param_name: str,
    default: Optional[bool] = ...,
    additional_message: Optional[str] = None,
) -> Optional[bool]: ...


def opt_bool_param(
    obj: object,
    param_name: str,
    default: Optional[bool] = None,
    additional_message: Optional[str] = None,
) -> Optional[bool]:
    if obj is not None and not isinstance(obj, bool):
        raise _param_type_mismatch_exception(obj, bool, param_name, additional_message)
    return default if obj is None else obj


def bool_elem(ddict: Mapping, key: str, additional_message: Optional[str] = None) -> bool:
    dict_param(ddict, "ddict")
    str_param(key, "key")

    value = ddict[key]
    if not isinstance(value, bool):
        raise _element_check_error(key, value, ddict, bool, additional_message)
    return value


# ########################
# ##### CALLABLE
# ########################

T_Callable = TypeVar("T_Callable", bound=Callable)
U_Callable = TypeVar("U_Callable", bound=Callable)


def callable_param(
    obj: T_Callable, param_name: str, additional_message: Optional[str] = None
) -> T_Callable:
    if not callable(obj):
        raise _param_not_callable_exception(obj, param_name, additional_message)
    return obj


@overload
def opt_callable_param(
    obj: None, param_name: str, default: None = ..., additional_message: Optional[str] = None
) -> None: ...


@overload
def opt_callable_param(
    obj: None, param_name: str, default: T_Callable, additional_message: Optional[str] = None
) -> T_Callable: ...


@overload
def opt_callable_param(
    obj: T_Callable,
    param_name: str,
    default: Optional[U_Callable] = ...,
    additional_message: Optional[str] = None,
) -> T_Callable: ...


def opt_callable_param(
    obj: Optional[Callable],
    param_name: str,
    default: Optional[Callable] = None,
    additional_message: Optional[str] = None,
) -> Optional[Callable]:
    if obj is not None and not callable(obj):
        raise _param_not_callable_exception(obj, param_name, additional_message)
    return default if obj is None else obj


def is_callable(obj: T_Callable, additional_message: Optional[str] = None) -> T_Callable:
    if not callable(obj):
        raise CheckError(
            "Must be callable. Got"
            f" {obj}.{(additional_message and f' Description: {additional_message}.') or ''}"
        )
    return obj


# ########################
# ##### CLASS
# ########################

T_Type = TypeVar("T_Type", bound=type)


def class_param(
    obj: T_Type,
    param_name: str,
    superclass: Optional[type] = None,
    additional_message: Optional[str] = None,
) -> T_Type:
    if not isinstance(obj, type):
        raise _param_class_mismatch_exception(
            obj, param_name, superclass, False, additional_message
        )

    if superclass and not issubclass(obj, superclass):
        raise _param_class_mismatch_exception(
            obj, param_name, superclass, False, additional_message
        )

    return obj


@overload
def opt_class_param(
    obj: object,
    param_name: str,
    default: type,
    superclass: Optional[type] = None,
    additional_message: Optional[str] = None,
) -> type: ...


@overload
def opt_class_param(
    obj: object,
    param_name: str,
    default: None = ...,
    superclass: Optional[type] = None,
    additional_message: Optional[str] = None,
) -> Optional[type]: ...


def opt_class_param(
    obj: object,
    param_name: str,
    default: Optional[type] = None,
    superclass: Optional[type] = None,
    additional_message: Optional[str] = None,
) -> Optional[type]:
    if obj is not None and not isinstance(obj, type):
        raise _param_class_mismatch_exception(obj, param_name, superclass, True, additional_message)

    if obj is None:
        return default

    if superclass and not issubclass(obj, superclass):
        raise _param_class_mismatch_exception(obj, param_name, superclass, True, additional_message)

    return obj


# ########################
# ##### DICT
# ########################


def dict_param(
    obj: object,
    param_name: str,
    key_type: Optional[TypeOrTupleOfTypes] = None,
    value_type: Optional[TypeOrTupleOfTypes] = None,
    additional_message: Optional[str] = None,
) -> dict[Any, Any]:
    """Ensures argument obj is a native Python dictionary, raises an exception if not, and otherwise
    returns obj.
    """
    if not isinstance(obj, dict):
        raise _param_type_mismatch_exception(
            obj, dict, param_name, additional_message=additional_message
        )

    if not (key_type or value_type):
        return obj

    return _check_mapping_entries(obj, key_type, value_type, mapping_type=dict)


def opt_dict_param(
    obj: Optional[dict[T, U]],
    param_name: str,
    key_type: Optional[TypeOrTupleOfTypes] = None,
    value_type: Optional[TypeOrTupleOfTypes] = None,
    additional_message: Optional[str] = None,
) -> dict[T, U]:
    """Ensures argument obj is either a dictionary or None; if the latter, instantiates an empty
    dictionary.
    """
    if obj is not None and not isinstance(obj, dict):
        raise _param_type_mismatch_exception(obj, dict, param_name, additional_message)

    if not obj:
        return {}

    return _check_mapping_entries(obj, key_type, value_type, mapping_type=dict)


@overload
def opt_nullable_dict_param(  # pyright: ignore[reportOverlappingOverload]
    obj: None,
    param_name: str,
    key_type: Optional[TypeOrTupleOfTypes] = ...,
    value_type: Optional[TypeOrTupleOfTypes] = ...,
    additional_message: Optional[str] = None,
) -> None: ...


@overload
def opt_nullable_dict_param(
    obj: object,
    param_name: str,
    key_type: Optional[TypeOrTupleOfTypes] = ...,
    value_type: Optional[TypeOrTupleOfTypes] = ...,
    additional_message: Optional[str] = None,
) -> dict: ...


def opt_nullable_dict_param(
    obj: object,
    param_name: str,
    key_type: Optional[TypeOrTupleOfTypes] = None,
    value_type: Optional[TypeOrTupleOfTypes] = None,
    additional_message: Optional[str] = None,
) -> Optional[dict]:
    """Ensures argument obj is either a dictionary or None."""
    if obj is not None and not isinstance(obj, dict):
        raise _param_type_mismatch_exception(obj, dict, param_name, additional_message)

    if not obj:
        return None if obj is None else {}

    return _check_mapping_entries(obj, key_type, value_type, mapping_type=dict)


def two_dim_dict_param(
    obj: object,
    param_name: str,
    key_type: TypeOrTupleOfTypes = str,
    value_type: Optional[TypeOrTupleOfTypes] = None,
    additional_message: Optional[str] = None,
) -> dict:
    if not isinstance(obj, dict):
        raise _param_type_mismatch_exception(obj, dict, param_name, additional_message)

    return _check_two_dim_mapping_entries(obj, key_type, value_type, mapping_type=dict)


def opt_two_dim_dict_param(
    obj: object,
    param_name: str,
    key_type: TypeOrTupleOfTypes = str,
    value_type: Optional[TypeOrTupleOfTypes] = None,
    additional_message: Optional[str] = None,
) -> dict:
    if obj is not None and not isinstance(obj, dict):
        raise _param_type_mismatch_exception(obj, dict, param_name, additional_message)

    if not obj:
        return {}

    return _check_two_dim_mapping_entries(obj, key_type, value_type, mapping_type=dict)


def dict_elem(
    obj: Mapping,
    key: str,
    key_type: Optional[TypeOrTupleOfTypes] = None,
    value_type: Optional[TypeOrTupleOfTypes] = None,
    additional_message: Optional[str] = None,
) -> dict:
    dict_param(obj, "obj")
    str_param(key, "key")

    if key not in obj:
        raise CheckError(f"{key} not present in dictionary {obj}")

    value = obj[key]
    if not isinstance(value, dict):
        raise _element_check_error(key, value, obj, dict, additional_message)
    else:
        return _check_mapping_entries(value, key_type, value_type, mapping_type=dict)


def opt_dict_elem(
    obj: Mapping[str, Any],
    key: str,
    key_type: Optional[TypeOrTupleOfTypes] = None,
    value_type: Optional[TypeOrTupleOfTypes] = None,
    additional_message: Optional[str] = None,
) -> dict:
    dict_param(obj, "obj")
    str_param(key, "key")

    value = obj.get(key)

    if value is None:
        return {}
    elif not isinstance(value, dict):
        raise _element_check_error(key, value, obj, dict, additional_message)
    else:
        return _check_mapping_entries(value, key_type, value_type, mapping_type=dict)


def opt_nullable_dict_elem(
    obj: Mapping[str, Any],
    key: str,
    key_type: Optional[TypeOrTupleOfTypes] = None,
    value_type: Optional[TypeOrTupleOfTypes] = None,
    additional_message: Optional[str] = None,
) -> Optional[dict]:
    dict_param(obj, "obj")
    str_param(key, "key")

    value = obj.get(key)

    if value is None:
        return None
    elif not isinstance(value, dict):
        raise _element_check_error(key, value, obj, dict, additional_message)
    else:
        return _check_mapping_entries(value, key_type, value_type, mapping_type=dict)


@overload
def is_dict(
    obj: dict[U, V],
    key_type: Optional[TypeOrTupleOfTypes] = ...,
    value_type: Optional[TypeOrTupleOfTypes] = ...,
    additional_message: Optional[str] = ...,
) -> dict[U, V]: ...


@overload
def is_dict(
    obj: object,
    key_type: Optional[TypeOrTupleOfTypes] = ...,
    value_type: Optional[TypeOrTupleOfTypes] = ...,
    additional_message: Optional[str] = ...,
) -> dict[Any, Any]: ...


def is_dict(
    obj: object,
    key_type: Optional[TypeOrTupleOfTypes] = None,
    value_type: Optional[TypeOrTupleOfTypes] = None,
    additional_message: Optional[str] = None,
) -> dict:
    if not isinstance(obj, dict):
        raise _type_mismatch_error(obj, dict, additional_message)

    if not (key_type or value_type):
        return obj

    return _check_mapping_entries(obj, key_type, value_type, mapping_type=dict)


# ########################
# ##### FLOAT
# ########################


def float_param(obj: object, param_name: str, additional_message: Optional[str] = None) -> float:
    if not isinstance(obj, float):
        raise _param_type_mismatch_exception(obj, float, param_name, additional_message)
    return obj


@overload
def opt_float_param(
    obj: object, param_name: str, default: float, additional_message: Optional[str] = None
) -> float: ...


@overload
def opt_float_param(
    obj: object,
    param_name: str,
    default: Optional[float] = ...,
    additional_message: Optional[str] = None,
) -> Optional[float]: ...


def opt_float_param(
    obj: object,
    param_name: str,
    default: Optional[float] = None,
    additional_message: Optional[str] = None,
) -> Optional[float]:
    if obj is not None and not isinstance(obj, float):
        raise _param_type_mismatch_exception(obj, float, param_name, additional_message)
    return default if obj is None else obj


def float_elem(ddict: Mapping, key: str, additional_message: Optional[str] = None) -> float:
    dict_param(ddict, "ddict")
    str_param(key, "key")

    value = ddict[key]
    if not isinstance(value, float):
        raise _element_check_error(key, value, ddict, float, additional_message)
    return value


def opt_float_elem(
    ddict: Mapping, key: str, additional_message: Optional[str] = None
) -> Optional[float]:
    dict_param(ddict, "ddict")
    str_param(key, "key")

    value = ddict.get(key)
    if value is None:
        return None
    if not isinstance(value, float):
        raise _element_check_error(key, value, ddict, float, additional_message)
    return value


# ########################
# ##### GENERATOR
# ########################


def generator_param(
    obj: Generator[T, U, V],
    param_name: str,
) -> Generator[T, U, V]:
    if not inspect.isgenerator(obj):
        raise ParameterCheckError(
            f'Param "{param_name}" is not a generator (return value of function that yields) Got '
            f"{obj} instead"
        )
    return obj


def opt_generator_param(
    obj: object,
    param_name: str,
) -> Optional[Generator]:
    if obj is not None and not inspect.isgenerator(obj):
        raise ParameterCheckError(
            f'Param "{param_name}" is not a generator (return value of function that yields) Got '
            f"{obj} instead"
        )
    return obj


def generator(
    obj: object,
) -> Generator:
    if not inspect.isgenerator(obj):
        raise ParameterCheckError(
            f"Not a generator (return value of function that yields) Got {obj} instead"
        )
    return obj


def opt_generator(
    obj: object,
) -> Optional[Generator]:
    if obj is not None and not inspect.isgenerator(obj):
        raise ParameterCheckError(
            f"Not a generator (return value of function that yields) Got {obj} instead"
        )
    return obj


# ########################
# ##### INT
# ########################


def int_param(obj: object, param_name: str, additional_message: Optional[str] = None) -> int:
    if not isinstance(obj, int):
        raise _param_type_mismatch_exception(obj, int, param_name, additional_message)
    return obj


@overload
def opt_int_param(
    obj: object, param_name: str, default: int, additional_message: Optional[str] = ...
) -> int: ...


@overload
def opt_int_param(
    obj: object,
    param_name: str,
    default: Optional[int] = None,
    additional_message: Optional[str] = None,
) -> Optional[int]: ...


def opt_int_param(
    obj: object,
    param_name: str,
    default: Optional[int] = None,
    additional_message: Optional[str] = None,
) -> Optional[int]:
    if obj is not None and not isinstance(obj, int):
        raise _param_type_mismatch_exception(obj, int, param_name, additional_message)
    return default if obj is None else obj


def int_value_param(
    obj: object, value: int, param_name: str, additional_message: Optional[str] = None
) -> int:
    if not isinstance(obj, int):
        raise _param_type_mismatch_exception(obj, int, param_name, additional_message)
    if obj != value:
        raise _param_invariant_exception(param_name, f"Should be equal to {value}")

    return obj


def int_elem(ddict: Mapping, key: str, additional_message: Optional[str] = None) -> int:
    dict_param(ddict, "ddict")
    str_param(key, "key")

    value = ddict[key]
    if not isinstance(value, int):
        raise _element_check_error(key, value, ddict, int, additional_message)
    return value


def opt_int_elem(
    ddict: Mapping, key: str, additional_message: Optional[str] = None
) -> Optional[int]:
    dict_param(ddict, "ddict")
    str_param(key, "key")

    value = ddict.get(key)
    if value is None:
        return None
    if not isinstance(value, int):
        raise _element_check_error(key, value, ddict, int, additional_message)
    return value


# ########################
# ##### INST
# ########################

# NOTE: inst() and opt_inst() perform narrowing, while inst_param() and opt_inst_param() do not. The
# reason for this is that there is a trade-off between narrowing and passing type information
# through untouched. The only working narrowing implementation will sometimes lose type information.
# This is because not every static type can be expressed as a runtime-checkable type:
#
#     foo = Foo(Bar())  # type is Foo[Bar]
#     inst(foo, Foo[Bar])  # illegal, can't pass parameterized types to inst()
#     inst(foo, Foo)  # type is Foo; because we couldn't pass parameterized type, we lost info
#
# In contrast, we don't lose type information when we pass the type of the checked argument through
# without modification.
#
# Because of this trade-off, it makes sense for inst() to perform narrowing but not inst_param().
# With inst(), we rarely have rich type information at the callsite (if we did we wouldn't be
# calling inst()). With inst_param(), on the other hand, we should always have rich type information
# at the callsite from the type annotation, so we should never need to narrow.


def inst_param(
    obj: T, param_name: str, ttype: TypeOrTupleOfTypes, additional_message: Optional[str] = None
) -> T:
    if not isinstance(obj, ttype):
        raise _param_type_mismatch_exception(
            obj, ttype, param_name, additional_message=additional_message
        )
    return obj


@overload
def opt_inst_param(
    obj: Optional[T],
    param_name: str,
    ttype: TypeOrTupleOfTypes,
    default: None = ...,
    additional_message: Optional[str] = None,
) -> Optional[T]: ...


@overload
def opt_inst_param(
    obj: Optional[T],
    param_name: str,
    ttype: TypeOrTupleOfTypes,
    default: T,
    additional_message: Optional[str] = None,
) -> T: ...


@overload
def opt_inst_param(
    obj: T,
    param_name: str,
    ttype: TypeOrTupleOfTypes,
    default: Optional[T] = ...,
    additional_message: Optional[str] = None,
) -> T: ...


def opt_inst_param(
    obj: Optional[T],
    param_name: str,
    ttype: TypeOrTupleOfTypes,
    default: Optional[T] = None,
    additional_message: Optional[str] = None,
) -> Optional[T]:
    if obj is not None and not isinstance(obj, ttype):
        raise _param_type_mismatch_exception(obj, ttype, param_name, additional_message)
    return default if obj is None else obj


def inst(
    obj: object,
    ttype: Union[type[T], tuple[type[T], ...]],
    additional_message: Optional[str] = None,
) -> T:
    if not isinstance(obj, ttype):
        raise _type_mismatch_error(obj, ttype, additional_message)
    return obj


def opt_inst(
    obj: object,
    ttype: Union[type[T], tuple[type[T], ...]],
    additional_message: Optional[str] = None,
) -> Optional[T]:
    if obj is not None and not isinstance(obj, ttype):
        raise _type_mismatch_error(obj, ttype, additional_message)
    return obj


# ########################
# ##### ITERATOR
# ########################


def iterator_param(
    obj: Iterator[T],
    param_name: str,
    additional_message: Optional[str] = None,
) -> Iterator[T]:
    if not isinstance(obj, Iterator):
        raise _param_type_mismatch_exception(obj, Iterator, param_name, additional_message)
    return obj


# ########################
# ##### LIST
# ########################


def list_param(
    obj: object,
    param_name: str,
    of_type: Optional[TTypeOrTupleOfTTypes[T]] = None,
    additional_message: Optional[str] = None,
) -> list[T]:
    if not isinstance(obj, list):
        raise _param_type_mismatch_exception(obj, list, param_name, additional_message)

    if not of_type:
        return obj

    return _check_iterable_items(obj, of_type, "list")


def opt_list_param(
    obj: object,
    param_name: str,
    of_type: Optional[TTypeOrTupleOfTTypes[T]] = None,
    additional_message: Optional[str] = None,
) -> list[T]:
    """Ensures argument obj is a list or None; in the latter case, instantiates an empty list
    and returns it.

    If the of_type argument is provided, also ensures that list items conform to the type specified
    by of_type.
    """
    if obj is not None and not isinstance(obj, list):
        raise _param_type_mismatch_exception(obj, list, param_name, additional_message)

    if not obj:
        return []
    if not of_type:
        return obj

    return _check_iterable_items(obj, of_type, "list")


@overload
def opt_nullable_list_param(
    obj: None,
    param_name: str,
    of_type: Optional[TTypeOrTupleOfTTypes[T]] = ...,
    additional_message: Optional[str] = None,
) -> None: ...


@overload
def opt_nullable_list_param(
    obj: list[T],
    param_name: str,
    of_type: Optional[TTypeOrTupleOfTTypes[T]] = ...,
    additional_message: Optional[str] = None,
) -> list[T]: ...


def opt_nullable_list_param(
    obj: object,
    param_name: str,
    of_type: Optional[TTypeOrTupleOfTTypes[T]] = None,
    additional_message: Optional[str] = None,
) -> Optional[list[T]]:
    """Ensures argument obj is a list or None. Returns None if input is None.

    If the of_type argument is provided, also ensures that list items conform to the type specified
    by of_type.
    """
    if obj is not None and not isinstance(obj, list):
        raise _param_type_mismatch_exception(obj, list, param_name, additional_message)

    if not obj:
        return None if obj is None else []
    if not of_type:
        return obj

    return _check_iterable_items(obj, of_type, "list")


def two_dim_list_param(
    obj: object,
    param_name: str,
    of_type: Optional[TypeOrTupleOfTypes] = None,
    additional_message: Optional[str] = None,
) -> list[list]:
    obj = list_param(obj, param_name, of_type=list, additional_message=additional_message)
    if not obj:
        raise CheckError("You must pass a list of lists. Received an empty list.")
    for sublist in obj:
        list_param(
            sublist, f"sublist_{param_name}", of_type=of_type, additional_message=additional_message
        )
        if len(sublist) != len(obj[0]):
            raise CheckError("All sublists in obj must have the same length")
    return obj


def list_elem(
    ddict: Mapping,
    key: str,
    of_type: Optional[TypeOrTupleOfTypes] = None,
    additional_message: Optional[str] = None,
) -> list:
    dict_param(ddict, "ddict")
    str_param(key, "key")
    opt_class_param(of_type, "of_type")

    value = ddict.get(key)

    if isinstance(value, list):
        if not of_type:
            return value

        return _check_iterable_items(value, of_type, "list")

    raise _element_check_error(key, value, ddict, list, additional_message)


def opt_list_elem(
    ddict: Mapping,
    key: str,
    of_type: Optional[TypeOrTupleOfTypes] = None,
    additional_message: Optional[str] = None,
) -> list:
    dict_param(ddict, "ddict")
    str_param(key, "key")
    opt_class_param(of_type, "of_type")

    value = ddict.get(key)

    if value is None:
        return []

    if not isinstance(value, list):
        raise _element_check_error(key, value, ddict, list, additional_message)

    if not of_type:
        return value

    return _check_iterable_items(value, of_type, "list")


def is_list(
    obj: object,
    of_type: Optional[TTypeOrTupleOfTTypes[T]] = None,
    additional_message: Optional[str] = None,
) -> list[T]:
    if not isinstance(obj, list):
        raise _type_mismatch_error(obj, list, additional_message)

    if not of_type:
        return obj

    return list(_check_iterable_items(obj, of_type, "list"))


# ########################
# ##### LITERAL
# ########################


def literal_param(
    obj: T, param_name: str, values: Sequence[object], additional_message: Optional[str] = None
) -> T:
    if obj not in values:
        raise _param_value_mismatch_exception(obj, values, param_name, additional_message)
    return obj


def opt_literal_param(
    obj: T, param_name: str, values: Sequence[object], additional_message: Optional[str] = None
) -> T:
    if obj is not None and obj not in values:
        raise _param_value_mismatch_exception(
            obj, values, param_name, additional_message, optional=True
        )
    return obj


# ########################
# ##### MAPPING
# ########################


def mapping_param(
    obj: Mapping[T, U],
    param_name: str,
    key_type: Optional[TypeOrTupleOfTypes] = None,
    value_type: Optional[TypeOrTupleOfTypes] = None,
    additional_message: Optional[str] = None,
) -> Mapping[T, U]:
    ttype = type(obj)
    # isinstance check against abc is costly, so try to handle common cases with cheapest check possible
    if not (ttype is dict or isinstance(obj, collections.abc.Mapping)):
        raise _param_type_mismatch_exception(
            obj, (collections.abc.Mapping,), param_name, additional_message=additional_message
        )

    if not (key_type or value_type):
        return obj

    return _check_mapping_entries(obj, key_type, value_type, mapping_type=collections.abc.Mapping)


def opt_mapping_param(
    obj: Optional[Mapping[T, U]],
    param_name: str,
    key_type: Optional[TypeOrTupleOfTypes] = None,
    value_type: Optional[TypeOrTupleOfTypes] = None,
    additional_message: Optional[str] = None,
) -> Mapping[T, U]:
    if obj is None:
        return dict()
    else:
        return mapping_param(obj, param_name, key_type, value_type, additional_message)


@overload
def opt_nullable_mapping_param(
    obj: None,
    param_name: str,
    key_type: Optional[TypeOrTupleOfTypes] = ...,
    value_type: Optional[TypeOrTupleOfTypes] = ...,
    additional_message: Optional[str] = ...,
) -> None: ...


@overload
def opt_nullable_mapping_param(
    obj: Mapping[T, U],
    param_name: str,
    key_type: Optional[TypeOrTupleOfTypes] = ...,
    value_type: Optional[TypeOrTupleOfTypes] = ...,
    additional_message: Optional[str] = ...,
) -> Mapping[T, U]: ...


def opt_nullable_mapping_param(
    obj: Optional[Mapping[T, U]],
    param_name: str,
    key_type: Optional[TypeOrTupleOfTypes] = None,
    value_type: Optional[TypeOrTupleOfTypes] = None,
    additional_message: Optional[str] = None,
) -> Optional[Mapping[T, U]]:
    if obj is None:
        return None
    else:
        return mapping_param(obj, param_name, key_type, value_type, additional_message)


def two_dim_mapping_param(
    obj: object,
    param_name: str,
    key_type: TypeOrTupleOfTypes = str,
    value_type: Optional[TypeOrTupleOfTypes] = None,
    additional_message: Optional[str] = None,
) -> Mapping:
    if not isinstance(obj, Mapping):
        raise _param_type_mismatch_exception(obj, dict, param_name, additional_message)
    return _check_two_dim_mapping_entries(obj, key_type, value_type)


# ########################
# ##### NOT NONE
# ########################


def not_none_param(
    obj: Optional[T], param_name: str, additional_message: Optional[str] = None
) -> T:
    if obj is None:
        additional_message = " " + additional_message if additional_message else ""
        raise _param_invariant_exception(
            param_name, f"Param {param_name} cannot be none.{additional_message}"
        )
    return obj


def not_none(value: Optional[T], additional_message: Optional[str] = None) -> T:
    if value is None:
        raise CheckError(f"Expected non-None value: {additional_message}")
    return value


# ########################
# ##### NUMERIC
# ########################


def numeric_param(
    obj: object, param_name: str, additional_message: Optional[str] = None
) -> Numeric:
    if not isinstance(obj, (int, float)):
        raise _param_type_mismatch_exception(obj, (int, float), param_name, additional_message)
    return obj


@overload
def opt_numeric_param(
    obj: object, param_name: str, default: Numeric, additional_message: Optional[str] = ...
) -> Numeric: ...


@overload
def opt_numeric_param(
    obj: object,
    param_name: str,
    default: Optional[Numeric] = ...,
    additional_message: Optional[str] = ...,
) -> Optional[Numeric]: ...


def opt_numeric_param(
    obj: object,
    param_name: str,
    default: Optional[Numeric] = None,
    additional_message: Optional[str] = None,
) -> Optional[Numeric]:
    if obj is not None and not isinstance(obj, (int, float)):
        raise _param_type_mismatch_exception(obj, (int, float), param_name, additional_message)
    return default if obj is None else obj


# ########################
# ##### PATH
# ########################


def path_param(
    obj: Union[str, PathLike], param_name: str, additional_message: Optional[str] = None
) -> str:
    if not isinstance(obj, (str, PathLike)):
        raise _param_type_mismatch_exception(obj, (str, PathLike), param_name, additional_message)
    return fspath(obj)


@overload
def opt_path_param(
    obj: None, param_name: str, default: None = ..., additional_message: Optional[str] = ...
) -> None: ...


@overload
def opt_path_param(
    obj: None,
    param_name: str,
    default: Union[str, PathLike],
    additional_message: Optional[str] = ...,
) -> str: ...


@overload
def opt_path_param(
    obj: Union[str, PathLike],
    param_name: str,
    default: Optional[Union[str, PathLike]] = ...,
    additional_message: Optional[str] = ...,
) -> str: ...


def opt_path_param(
    obj: Optional[Union[str, PathLike]],
    param_name: str,
    default: Optional[Union[str, PathLike]] = None,
    additional_message: Optional[str] = None,
) -> Optional[Union[str, PathLike]]:
    if obj is None:
        return str(default) if default is not None else None
    else:
        return path_param(obj, param_name, additional_message)


# ########################
# ##### SEQUENCE
# ########################


def sequence_param(
    obj: Sequence[T],
    param_name: str,
    of_type: Optional[TypeOrTupleOfTypes] = None,
    additional_message: Optional[str] = None,
) -> Sequence[T]:
    """Ensures argument obj is a Sequence.

    Despite technically being a sequences, str and bytes are not allowed as they are
    almost always unintended and cause bugs.

    If the of_type argument is provided, also ensures that sequence items conform to the
    type specified by of_type.
    """
    ttype = type(obj)
    # isinstance check against abc is costly, so try to handle common cases with cheapest check possible
    if not (
        ttype is list
        or ttype is tuple
        # even though str/bytes are technically sequences
        # its likely not desired so error unless allow_str is set
        or (
            isinstance(obj, collections.abc.Sequence)
            and (ttype not in (str, bytes))
            and not is_record(obj)
        )
    ):
        if ttype in (str, bytes):
            msg = f"{ttype.__name__} is a disallowed Sequence type due to its likeliness to cause bugs."
            additional_message = (
                msg if additional_message is None else f"{msg} {additional_message}"
            )

        raise _param_type_mismatch_exception(
            obj,
            collections.abc.Sequence,
            param_name,
            additional_message,
        )

    if not of_type:
        return obj

    return _check_iterable_items(obj, of_type, "sequence")


def opt_sequence_param(
    obj: Optional[Sequence[T]],
    param_name: str,
    of_type: Optional[TypeOrTupleOfTypes] = None,
    additional_message: Optional[str] = None,
) -> Sequence[T]:
    """Ensures argument obj is a Sequence or None, returning an empty list when None.

    Despite technically being a sequences, str and bytes are not allowed as they are
    almost always unintended and cause bugs.

    If the of_type argument is provided, also ensures that sequence items conform to the
    type specified by of_type.
    """
    ttype = type(obj)
    if obj is None:
        return []
    # isinstance check against abc is costly, so try to handle common cases with cheapest check possible
    elif not (
        ttype is list
        or ttype is tuple
        or (
            isinstance(obj, collections.abc.Sequence)
            and ttype not in (bytes, str)
            and not is_record(obj)
        )
    ):
        if ttype in (str, bytes):
            msg = f"{ttype.__name__} is a disallowed Sequence type due to its likeliness to cause bugs."
            additional_message = (
                msg if additional_message is None else f"{msg} {additional_message}"
            )

        raise _param_type_mismatch_exception(
            obj,
            collections.abc.Sequence,
            param_name,
            additional_message,
        )
    elif of_type is not None:
        return _check_iterable_items(obj, of_type, "sequence")
    else:
        return obj


@overload
def opt_nullable_sequence_param(
    obj: None,
    param_name: str,
    of_type: Optional[TypeOrTupleOfTypes] = ...,
    additional_message: Optional[str] = ...,
) -> None: ...


@overload
def opt_nullable_sequence_param(
    obj: Sequence[T],
    param_name: str,
    of_type: Optional[TypeOrTupleOfTypes] = None,
    additional_message: Optional[str] = ...,
) -> Sequence[T]: ...


def opt_nullable_sequence_param(
    obj: Optional[Sequence[T]],
    param_name: str,
    of_type: Optional[TypeOrTupleOfTypes] = None,
    additional_message: Optional[str] = None,
) -> Optional[Sequence[T]]:
    if obj is None:
        return None
    else:
        return opt_sequence_param(obj, param_name, of_type, additional_message)


# ########################
# ##### Iterable
# ########################


def iterable_param(
    obj: Iterable[T],
    param_name: str,
    of_type: Optional[TypeOrTupleOfTypes] = None,
    additional_message: Optional[str] = None,
) -> Iterable[T]:
    ttype = type(obj)
    # isinstance check against abc is costly, so try to handle common cases with cheapest check possible
    if not (
        ttype is list
        or ttype is tuple
        or (
            isinstance(obj, collections.abc.Iterable)
            and ttype not in (str, bytes)
            and not is_record(obj)
        )
    ):
        raise _param_type_mismatch_exception(
            obj, collections.abc.Iterable, param_name, additional_message
        )

    if not of_type:
        return obj

    return _check_iterable_items(obj, of_type, "iterable")


def opt_iterable_param(
    obj: Optional[Iterable[T]],
    param_name: str,
    of_type: Optional[TypeOrTupleOfTypes] = None,
    additional_message: Optional[str] = None,
) -> Iterable[T]:
    if obj is None:
        return []

    return iterable_param(obj, param_name, of_type, additional_message)


def opt_nullable_iterable_param(
    obj: Optional[Iterable[T]],
    param_name: str,
    of_type: Optional[TypeOrTupleOfTypes] = None,
    additional_message: Optional[str] = None,
) -> Optional[Iterable[T]]:
    if obj is None:
        return None

    return iterable_param(obj, param_name, of_type, additional_message)


def is_iterable(
    obj: object,
    of_type: Optional[TTypeOrTupleOfTTypes[T]] = None,
    additional_message: Optional[str] = None,
) -> Iterable[T]:
    # short-circuit for common collections
    # separate if statement to make that explicit
    if not isinstance(obj, (list, tuple)):
        if not isinstance(obj, Iterable):
            raise _type_mismatch_error(obj, list, additional_message)

    return obj if not of_type else _check_iterable_items(obj, of_type, "iterable")


# ########################
# ##### SET
# ########################

T_Set = TypeVar("T_Set", bound=AbstractSet)


def set_param(
    obj: T_Set,
    param_name: str,
    of_type: Optional[TypeOrTupleOfTypes] = None,
    additional_message: Optional[str] = None,
) -> T_Set:
    if not isinstance(obj, (frozenset, set)):
        raise _param_type_mismatch_exception(obj, (frozenset, set), param_name, additional_message)

    if not of_type:
        return obj

    return _check_iterable_items(obj, of_type, "set")


def opt_set_param(
    obj: Optional[T_Set],
    param_name: str,
    of_type: Optional[TypeOrTupleOfTypes] = None,
    additional_message: Optional[str] = None,
) -> T_Set:
    """Ensures argument obj is a set or None; in the latter case, instantiates an empty set
    and returns it.

    If the of_type argument is provided, also ensures that list items conform to the type specified
    by of_type.
    """
    if obj is None:
        return frozenset()  # type: ignore # 2 hot 4 cast
    elif obj is not None and not isinstance(obj, (frozenset, set)):
        raise _param_type_mismatch_exception(obj, (frozenset, set), param_name, additional_message)
    elif not of_type:
        return obj

    return _check_iterable_items(obj, of_type, "set")


@overload
def opt_nullable_set_param(
    obj: None,
    param_name: str,
    of_type: Optional[TypeOrTupleOfTypes] = ...,
    additional_message: Optional[str] = ...,
) -> None: ...


@overload
def opt_nullable_set_param(
    obj: T_Set,
    param_name: str,
    of_type: Optional[TypeOrTupleOfTypes] = ...,
    additional_message: Optional[str] = ...,
) -> T_Set: ...


def opt_nullable_set_param(
    obj: Optional[T_Set],
    param_name: str,
    of_type: Optional[TypeOrTupleOfTypes] = None,
    additional_message: Optional[str] = None,
) -> Optional[T_Set]:
    """Ensures argument obj is a set or None. Returns None if input is None.
    and returns it.

    If the of_type argument is provided, also ensures that list items conform to the type specified
    by of_type.
    """
    if obj is None:
        return None
    elif not isinstance(obj, (frozenset, set)):
        raise _param_type_mismatch_exception(obj, (frozenset, set), param_name, additional_message)
    elif not of_type:
        return obj

    return _check_iterable_items(obj, of_type, "set")


# ########################
# ##### STR
# ########################


def str_param(obj: object, param_name: str, additional_message: Optional[str] = None) -> str:
    if not isinstance(obj, str):
        raise _param_type_mismatch_exception(obj, str, param_name, additional_message)
    return obj


@overload
def opt_str_param(
    obj: object, param_name: str, default: str, additional_message: Optional[str] = ...
) -> str: ...


@overload
def opt_str_param(
    obj: object,
    param_name: str,
    default: Optional[str] = ...,
    additional_message: Optional[str] = ...,
) -> Optional[str]: ...


def opt_str_param(
    obj: object,
    param_name: str,
    default: Optional[str] = None,
    additional_message: Optional[str] = None,
) -> Optional[str]:
    if obj is not None and not isinstance(obj, str):
        raise _param_type_mismatch_exception(obj, str, param_name, additional_message)
    return default if obj is None else obj


def opt_nonempty_str_param(
    obj: object,
    param_name: str,
    default: Optional[str] = None,
    additional_message: Optional[str] = None,
) -> Optional[str]:
    if obj is not None and not isinstance(obj, str):
        raise _param_type_mismatch_exception(obj, str, param_name, additional_message)
    return default if obj is None or obj == "" else obj


def str_elem(ddict: Mapping, key: str, additional_message: Optional[str] = None) -> str:
    dict_param(ddict, "ddict")
    str_param(key, "key")

    value = ddict[key]
    if not isinstance(value, str):
        raise _element_check_error(key, value, ddict, str, additional_message)
    return value


def opt_str_elem(
    ddict: Mapping, key: str, additional_message: Optional[str] = None
) -> Optional[str]:
    dict_param(ddict, "ddict")
    str_param(key, "key")

    value = ddict.get(key)
    if value is None:
        return None
    if not isinstance(value, str):
        raise _element_check_error(key, value, ddict, str, additional_message)
    return value


# ########################
# ##### TUPLE
# ########################


def tuple_param(
    obj: tuple[T, ...],
    param_name: str,
    of_type: Optional[TypeOrTupleOfTypes] = None,
    of_shape: Optional[tuple[TypeOrTupleOfTypes, ...]] = None,
    additional_message: Optional[str] = None,
) -> tuple[T, ...]:
    """Ensure param is a tuple and is of a specified type. `of_type` defines a variadic tuple type--
    `obj` may be of any length, but each element must match the `of_type` argmument. `of_shape`
    defines a fixed-length tuple type-- each element must match the corresponding element in
    `of_shape`. Passing both `of_type` and `of_shape` will raise an error.
    """
    if not isinstance(obj, tuple):
        raise _param_type_mismatch_exception(obj, tuple, param_name, additional_message)

    if of_type is None and of_shape is None:
        return obj

    if of_type and of_shape:
        raise CheckError("Must specify exactly one `of_type` or `of_shape`")

    return _check_tuple_items(obj, of_type, of_shape)


@overload
def opt_tuple_param(
    obj: Optional[tuple[T, ...]],
    param_name: str,
    of_type: Optional[TypeOrTupleOfTypes] = ...,
    of_shape: Optional[tuple[TypeOrTupleOfTypes, ...]] = ...,
    additional_message: Optional[str] = ...,
) -> tuple[T, ...]: ...


@overload
def opt_tuple_param(
    obj: object,
    param_name: str,
    of_type: Optional[TypeOrTupleOfTypes] = ...,
    of_shape: Optional[tuple[TypeOrTupleOfTypes, ...]] = ...,
    additional_message: Optional[str] = ...,
) -> tuple[object, ...]: ...


def opt_tuple_param(
    obj: object,
    param_name: str,
    of_type: Optional[TypeOrTupleOfTypes] = None,
    of_shape: Optional[tuple[TypeOrTupleOfTypes, ...]] = None,
    additional_message: Optional[str] = None,
) -> tuple[Any, ...]:
    """Ensures argument obj is a tuple or None; in the latter case, instantiates an empty tuple
    and returns it.
    """
    if obj is not None and not isinstance(obj, tuple):
        raise _param_type_mismatch_exception(obj, tuple, param_name, additional_message)

    if obj is None:
        return tuple()

    if of_type is None and of_shape is None:
        return obj

    if of_type and of_shape:
        raise CheckError("Must specify exactly one `of_type` or `of_shape`")

    return _check_tuple_items(obj, of_type, of_shape)


@overload
def opt_nullable_tuple_param(
    obj: None,
    param_name: str,
    of_type: Optional[TypeOrTupleOfTypes] = ...,
    of_shape: Optional[tuple[TypeOrTupleOfTypes, ...]] = ...,
    additional_message: Optional[str] = ...,
) -> None: ...


@overload
def opt_nullable_tuple_param(
    obj: tuple[T, ...],
    param_name: str,
    of_type: TypeOrTupleOfTypes = ...,
    of_shape: Optional[tuple[TypeOrTupleOfTypes, ...]] = ...,
    additional_message: Optional[str] = None,
) -> tuple[T, ...]: ...


def opt_nullable_tuple_param(
    obj: Optional[tuple[T, ...]],
    param_name: str,
    of_type: Optional[TypeOrTupleOfTypes] = None,
    of_shape: Optional[tuple[TypeOrTupleOfTypes, ...]] = None,
    additional_message: Optional[str] = None,
) -> Optional[tuple[T, ...]]:
    """Ensure optional param is a tuple and is of a specified type. `default` is returned if `obj`
    is None. `of_type` defines a variadic tuple type-- `obj` may be of any length, but each element
    must match the `of_type` argmument. `of_shape` defines a fixed-length tuple type-- each element
    must match the corresponding element in `of_shape`. Passing both `of_type` and `of_shape` will
    raise an error.
    """
    if obj is not None and not isinstance(obj, tuple):
        raise _param_type_mismatch_exception(obj, tuple, param_name, additional_message)

    if obj is None:
        return None

    if of_type is None and of_shape is None:
        return obj

    if of_type and of_shape:
        raise CheckError("Must specify exactly one `of_type` or `of_shape`")

    return _check_tuple_items(obj, of_type, of_shape)


def is_tuple(
    obj: object,
    of_type: Optional[TypeOrTupleOfTypes] = None,
    of_shape: Optional[tuple[TypeOrTupleOfTypes, ...]] = None,
    additional_message: Optional[str] = None,
) -> tuple:
    """Ensure target is a tuple and is of a specified type. `of_type` defines a variadic tuple
    type-- `obj` may be of any length, but each element must match the `of_type` argmument.
    `of_shape` defines a fixed-length tuple type-- each element must match the corresponding element
    in `of_shape`. Passing both `of_type` and `of_shape` will raise an error.
    """
    if not isinstance(obj, tuple) or is_record(obj):
        raise _type_mismatch_error(obj, tuple, additional_message)

    if of_type is None and of_shape is None:
        return obj

    if of_type and of_shape:
        raise CheckError("Must specify exactly one `of_type` or `of_shape`")

    return _check_tuple_items(obj, of_type, of_shape)


def _check_tuple_items(
    obj_tuple: tuple[T, ...],
    of_type: Optional[TypeOrTupleOfTypes] = None,
    of_shape: Optional[tuple[TypeOrTupleOfTypes, ...]] = None,
) -> tuple[T, ...]:
    if of_shape is not None:
        len_tuple = len(obj_tuple)
        len_type = len(of_shape)
        if not len_tuple == len_type:
            raise CheckError(
                f"Tuple mismatches type: tuple had {len_tuple} members but type had {len_type}"
            )

        for i, obj in enumerate(obj_tuple):
            of_shape_i = of_shape[i]
            if not isinstance(obj, of_shape_i):
                if isinstance(obj, type):
                    additional_message = (
                        " Did you pass a class where you were expecting an instance of the class?"
                    )
                else:
                    additional_message = ""
                raise CheckError(
                    f"Member of tuple mismatches type at index {i}. Expected {of_shape_i}. Got "
                    f"{obj!r} of type {type(obj)}.{additional_message}"
                )

    elif of_type is not None:
        _check_iterable_items(obj_tuple, of_type, "tuple")

    return obj_tuple


def tuple_elem(
    ddict: Mapping,
    key: str,
    of_type: Optional[TypeOrTupleOfTypes] = None,
    additional_message: Optional[str] = None,
) -> tuple:
    dict_param(ddict, "ddict")
    str_param(key, "key")
    opt_class_param(of_type, "of_type")

    value = ddict.get(key)

    if isinstance(value, tuple) and not is_record(value):
        if not of_type:
            return value

        return _check_iterable_items(value, of_type, "tuple")

    raise _element_check_error(key, value, ddict, tuple, additional_message)


def opt_tuple_elem(
    ddict: Mapping,
    key: str,
    of_type: Optional[TypeOrTupleOfTypes] = None,
    additional_message: Optional[str] = None,
) -> tuple:
    dict_param(ddict, "ddict")
    str_param(key, "key")
    opt_class_param(of_type, "of_type")

    value = ddict.get(key)

    if value is None:
        return tuple()

    if isinstance(value, tuple) and not is_record(value):
        if not of_type:
            return value

        return _check_iterable_items(value, of_type, "tuple")

    raise _element_check_error(key, value, ddict, tuple, additional_message)


# ###################################################################################################
# ##### OTHER CHECKS
# ###################################################################################################


def param_invariant(condition: Any, param_name: str, desc: Optional[str] = None):
    if not condition:
        raise _param_invariant_exception(param_name, desc)


def invariant(condition: Any, desc: Optional[str] = None) -> bool:
    if not condition:
        if desc:
            raise CheckError(f"Invariant failed. Description: {desc}")
        else:
            raise CheckError("Invariant failed.")

    return True


def assert_never(value: object) -> NoReturn:
    failed(f"Unhandled value: {value} ({type(value).__name__})")


def failed(desc: str) -> NoReturn:
    if not isinstance(desc, str):
        raise CheckError("desc argument must be a string")

    raise CheckError(f"Failure condition: {desc}")


def not_implemented(desc: str) -> NoReturn:
    if not isinstance(desc, str):
        raise CheckError("desc argument must be a string")

    raise NotImplementedCheckError(f"Not implemented: {desc}")


# ###################################################################################################
# ##### ERRORS / UTILITY
# ###################################################################################################


class CheckError(Exception):
    pass


class ParameterCheckError(CheckError):
    pass


class ElementCheckError(CheckError):
    pass


class NotImplementedCheckError(CheckError):
    pass


def _element_check_error(
    key: object,
    value: object,
    ddict: Mapping,
    ttype: TypeOrTupleOfTypes,
    additional_message: Optional[str] = None,
) -> ElementCheckError:
    additional_message = " " + additional_message if additional_message else ""
    return ElementCheckError(
        f"Value {value!r} from key {key} is not a {ttype!r}. Dict: {ddict!r}.{additional_message}"
    )


def _param_value_mismatch_exception(
    obj: object,
    values: Sequence[object],
    param_name: str,
    additional_message: Optional[str] = None,
    optional: bool = False,
) -> ParameterCheckError:
    allow_none_clause = " or None" if optional else ""
    additional_message = " " + additional_message if additional_message else ""
    return ParameterCheckError(
        f'Param "{param_name}" is not equal to one of {values}{allow_none_clause}. Got'
        f" {obj!r}.{additional_message}"
    )


def _param_type_mismatch_exception(
    obj: object,
    ttype: TypeOrTupleOfTypes,
    param_name: str,
    additional_message: Optional[str] = None,
) -> ParameterCheckError:
    additional_message = " " + additional_message if additional_message else ""
    if isinstance(ttype, tuple):
        type_names = sorted([t.__name__ for t in ttype])
        return ParameterCheckError(
            f'Param "{param_name}" is not one of {type_names}. Got {obj!r} which is type'
            f" {type(obj)}.{additional_message}"
        )
    else:
        return ParameterCheckError(
            f'Param "{param_name}" is not a {ttype.__name__}. Got {obj!r} which is type'
            f" {type(obj)}.{additional_message}"
        )


def _param_class_mismatch_exception(
    obj: object,
    param_name: str,
    superclass: Optional[type],
    optional: bool,
    additional_message: Optional[str] = None,
) -> ParameterCheckError:
    additional_message = " " + additional_message if additional_message else ""
    opt_clause = (optional and "be None or") or ""
    subclass_clause = (superclass and f"that inherits from {superclass.__name__}") or ""
    return ParameterCheckError(
        f'Param "{param_name}" must {opt_clause}be a class{subclass_clause}. Got {obj!r} of'
        f" type {type(obj)}.{additional_message}"
    )


def _type_mismatch_error(
    obj: object, ttype: TypeOrTupleOfTypes, additional_message: Optional[str] = None
) -> CheckError:
    type_message = (
        f"not one of {sorted([t.__name__ for t in ttype])}"
        if isinstance(ttype, tuple)
        else f"not a {ttype.__name__}"
    )
    repr_obj = repr(obj)
    additional_message = " " + additional_message if additional_message else ""
    return CheckError(
        f"Object {repr_obj} is {type_message}. Got {repr_obj} with type"
        f" {type(obj)}.{additional_message}"
    )


def _param_not_callable_exception(
    obj: Any, param_name: str, additional_message: Optional[str] = None
) -> ParameterCheckError:
    additional_message = " " + additional_message if additional_message else ""
    return ParameterCheckError(
        f'Param "{param_name}" is not callable. Got {obj!r} with type {type(obj)}.'
        f"{additional_message}"
    )


def _param_invariant_exception(param_name: str, desc: Optional[str] = None) -> ParameterCheckError:
    return ParameterCheckError(
        f"Invariant violation for parameter {param_name}. Description: {desc}"
    )


T_Iterable = TypeVar("T_Iterable", bound=Iterable)


def _check_iterable_items(
    obj_iter: T_Iterable, of_type: TypeOrTupleOfTypes, collection_name: str = "iterable"
) -> T_Iterable:
    for obj in obj_iter:
        if not isinstance(obj, of_type):
            if isinstance(obj, type):
                additional_message = (
                    " Did you pass a class where you were expecting an instance of the class?"
                )
            else:
                additional_message = ""
            raise CheckError(
                f"Member of {collection_name} mismatches type. Expected {of_type}. Got"
                f" {obj!r} of type {type(obj)}.{additional_message}"
            )

    return obj_iter


W = TypeVar("W", bound=Mapping)
X = TypeVar("X", bound=Mapping)


def _check_mapping_entries(
    obj: W,
    key_type: Optional[TypeOrTupleOfTypes] = None,
    value_type: Optional[TypeOrTupleOfTypes] = None,
    key_check: Callable[..., Any] = isinstance,
    value_check: Callable[..., Any] = isinstance,
    mapping_type: type = collections.abc.Mapping,
) -> W:
    """Enforces that the keys/values conform to the types specified by key_type, value_type."""
    for key, value in obj.items():
        if key_type and not key_check(key, key_type):
            raise CheckError(
                f"Key in {mapping_type.__name__} mismatches type. Expected {key_type!r}. Got"
                f" {key!r}"
            )

        if value_type and not value_check(value, value_type):
            raise CheckError(
                f"Value in {mapping_type.__name__} mismatches expected type for key {key}. Expected"
                f" value of type {value_type!r}. Got value {value} of type {type(value)}."
            )

    return obj


def _check_two_dim_mapping_entries(
    obj: W,
    key_type: Optional[TypeOrTupleOfTypes] = None,
    value_type: Optional[TypeOrTupleOfTypes] = None,
    mapping_type: type = collections.abc.Mapping,
) -> W:
    _check_mapping_entries(
        obj, key_type, mapping_type, mapping_type=mapping_type
    )  # check level one

    for inner_mapping in obj.values():
        _check_mapping_entries(
            inner_mapping, key_type, value_type, mapping_type=mapping_type
        )  # check level two

    return obj
