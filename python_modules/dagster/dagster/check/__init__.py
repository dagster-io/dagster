import collections.abc
import inspect
from os import PathLike, fspath
from typing import (
    AbstractSet,
    Any,
    Callable,
    Dict,
    Generator,
    Iterable,
    List,
    Mapping,
    NoReturn,
    Optional,
    Sequence,
    Set,
    Tuple,
    Type,
    TypeVar,
    Union,
    overload,
)

TypeOrTupleOfTypes = Union[type, Tuple[type, ...]]
Numeric = Union[int, float]
T = TypeVar("T")
U = TypeVar("U")

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


def bool_param(obj: object, param_name: str) -> bool:
    if not isinstance(obj, bool):
        raise _param_type_mismatch_exception(obj, bool, param_name)
    return obj


@overload
def opt_bool_param(obj: object, param_name: str, default: bool) -> bool:
    ...


@overload
def opt_bool_param(obj: object, param_name: str) -> Optional[bool]:
    ...


def opt_bool_param(obj: object, param_name: str, default: Optional[bool] = None) -> Optional[bool]:
    if obj is not None and not isinstance(obj, bool):
        raise _param_type_mismatch_exception(obj, bool, param_name)
    return default if obj is None else obj


def bool_elem(ddict: Dict, key: str) -> bool:
    dict_param(ddict, "ddict")
    str_param(key, "key")

    value = ddict[key]
    if not isinstance(value, bool):
        raise _element_check_error(key, value, ddict, bool)
    return value


# ########################
# ##### CALLABLE
# ########################


def callable_param(obj: object, param_name: str) -> Callable:
    if not callable(obj):
        raise _param_not_callable_exception(obj, param_name)
    return obj


@overload
def opt_callable_param(obj: object, param_name: str, default: Callable) -> Callable:
    ...


@overload
def opt_callable_param(obj: object, param_name: str) -> Optional[Callable]:
    ...


def opt_callable_param(
    obj: object, param_name: str, default: Optional[Callable] = None
) -> Optional[Callable]:
    if obj is not None and not callable(obj):
        raise _param_not_callable_exception(obj, param_name)
    return default if obj is None else obj


def is_callable(obj: object, desc: Optional[str] = None) -> Callable:
    if not callable(obj):
        raise CheckError(f"Must be callable. Got {obj}.{desc and f' Description: {desc}.' or ''}")
    return obj


# ########################
# ##### CLASS
# ########################


def class_param(obj: object, param_name: str, superclass: Optional[type] = None) -> type:
    if not isinstance(obj, type):
        raise _param_class_mismatch_exception(obj, param_name, superclass, optional=False)

    if superclass and not issubclass(obj, superclass):
        raise _param_class_mismatch_exception(obj, param_name, superclass, optional=False)

    return obj


@overload
def opt_class_param(
    obj: object, param_name: str, default: type, superclass: Optional[type] = None
) -> type:
    ...


@overload
def opt_class_param(
    obj: object, param_name: str, default: None = ..., superclass: Optional[type] = None
) -> Optional[type]:
    ...


def opt_class_param(
    obj: object, param_name: str, default: Optional[type] = None, superclass: Optional[type] = None
) -> Optional[type]:
    if obj is not None and not isinstance(obj, type):
        raise _param_class_mismatch_exception(obj, param_name, superclass, True)

    if obj is None:
        return default

    if superclass and not issubclass(obj, superclass):
        raise _param_class_mismatch_exception(obj, param_name, superclass, True)

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
) -> Dict:
    """Ensures argument obj is a native Python dictionary, raises an exception if not, and otherwise
    returns obj.
    """
    from dagster.utils import frozendict

    if not isinstance(obj, (frozendict, dict)):
        raise _param_type_mismatch_exception(
            obj, (frozendict, dict), param_name, additional_message=additional_message
        )

    if not (key_type or value_type):
        return obj

    return _check_mapping_entries(obj, key_type, value_type, mapping_type=dict)


def opt_dict_param(
    obj: object,
    param_name: str,
    key_type: Optional[TypeOrTupleOfTypes] = None,
    value_type: Optional[TypeOrTupleOfTypes] = None,
) -> Dict:
    """Ensures argument obj is either a dictionary or None; if the latter, instantiates an empty
    dictionary.
    """
    from dagster.utils import frozendict

    if obj is not None and not isinstance(obj, (frozendict, dict)):
        raise _param_type_mismatch_exception(obj, (frozendict, dict), param_name)

    if not obj:
        return {}

    return _check_mapping_entries(obj, key_type, value_type, mapping_type=dict)


# pyright understands this overload but not mypy
@overload
def opt_nullable_dict_param(  # type: ignore
    obj: None,
    param_name: str,
    key_type: Optional[TypeOrTupleOfTypes] = ...,
    value_type: Optional[TypeOrTupleOfTypes] = ...,
) -> None:
    ...


@overload
def opt_nullable_dict_param(
    obj: object,
    param_name: str,
    key_type: Optional[TypeOrTupleOfTypes] = ...,
    value_type: Optional[TypeOrTupleOfTypes] = ...,
) -> Dict:
    ...


def opt_nullable_dict_param(
    obj: object,
    param_name: str,
    key_type: Optional[TypeOrTupleOfTypes] = None,
    value_type: Optional[TypeOrTupleOfTypes] = None,
) -> Optional[Dict]:
    """Ensures argument obj is either a dictionary or None."""
    from dagster.utils import frozendict

    if obj is not None and not isinstance(obj, (frozendict, dict)):
        raise _param_type_mismatch_exception(obj, (frozendict, dict), param_name)

    if not obj:
        return None if obj is None else {}

    return _check_mapping_entries(obj, key_type, value_type, mapping_type=dict)


def two_dim_dict_param(
    obj: object,
    param_name: str,
    key_type: TypeOrTupleOfTypes = str,
    value_type: Optional[TypeOrTupleOfTypes] = None,
) -> Dict:
    if not isinstance(obj, dict):
        raise _param_type_mismatch_exception(obj, dict, param_name)

    return _check_two_dim_mapping_entries(obj, key_type, value_type, mapping_type=dict)


def opt_two_dim_dict_param(
    obj: object,
    param_name: str,
    key_type: TypeOrTupleOfTypes = str,
    value_type: Optional[TypeOrTupleOfTypes] = None,
) -> Dict:
    if obj is not None and not isinstance(obj, dict):
        raise _param_type_mismatch_exception(obj, dict, param_name)

    if not obj:
        return {}

    return _check_two_dim_mapping_entries(obj, key_type, value_type, mapping_type=dict)


def dict_elem(
    obj: Dict,
    key: str,
    key_type: Optional[TypeOrTupleOfTypes] = None,
    value_type: Optional[TypeOrTupleOfTypes] = None,
) -> Dict:
    from dagster.utils import frozendict

    dict_param(obj, "obj")
    str_param(key, "key")

    if key not in obj:
        raise CheckError(f"{key} not present in dictionary {obj}")

    value = obj[key]
    if not isinstance(value, (frozendict, dict)):
        raise _element_check_error(key, value, obj, (frozendict, dict))
    else:
        return _check_mapping_entries(value, key_type, value_type, mapping_type=dict)


def opt_dict_elem(
    obj: Dict[str, Any],
    key: str,
    key_type: Optional[TypeOrTupleOfTypes] = None,
    value_type: Optional[TypeOrTupleOfTypes] = None,
) -> Dict:
    from dagster.utils import frozendict

    dict_param(obj, "obj")
    str_param(key, "key")

    value = obj.get(key)

    if value is None:
        return {}
    elif not isinstance(value, (frozendict, dict)):
        raise _element_check_error(key, value, obj, dict)
    else:
        return _check_mapping_entries(value, key_type, value_type, mapping_type=dict)


def is_dict(
    obj: Dict[T, U],
    key_type: Optional[TypeOrTupleOfTypes] = None,
    value_type: Optional[TypeOrTupleOfTypes] = None,
    desc: Optional[str] = None,
) -> Dict[T, U]:
    from dagster.utils import frozendict

    if not isinstance(obj, (frozendict, dict)):
        raise _type_mismatch_error(obj, (frozendict, dict), desc)

    if not (key_type or value_type):
        return obj

    return _check_mapping_entries(obj, key_type, value_type, mapping_type=dict)


# ########################
# ##### FLOAT
# ########################


def float_param(obj: object, param_name: str) -> float:
    if not isinstance(obj, float):
        raise _param_type_mismatch_exception(obj, float, param_name)
    return obj


@overload
def opt_float_param(obj: object, param_name: str, default: float) -> float:
    ...


@overload
def opt_float_param(obj: object, param_name: str) -> Optional[float]:
    ...


def opt_float_param(
    obj: object, param_name: str, default: Optional[float] = None
) -> Optional[float]:
    if obj is not None and not isinstance(obj, float):
        raise _param_type_mismatch_exception(obj, float, param_name)
    return default if obj is None else obj


def float_elem(ddict: Dict, key: str) -> float:
    dict_param(ddict, "ddict")
    str_param(key, "key")

    value = ddict[key]
    if not isinstance(value, float):
        raise _element_check_error(key, value, ddict, float)
    return value


def opt_float_elem(ddict: Dict, key: str) -> Optional[float]:
    dict_param(ddict, "ddict")
    str_param(key, "key")

    value = ddict.get(key)
    if value is None:
        return None
    if not isinstance(value, float):
        raise _element_check_error(key, value, ddict, float)
    return value


# ########################
# ##### GENERATOR
# ########################


def generator_param(obj: object, param_name: str) -> Generator:
    if not inspect.isgenerator(obj):
        raise ParameterCheckError(
            f'Param "{param_name}" is not a generator (return value of function that yields) Got '
            f"{obj} instead"
        )
    return obj


def opt_generator_param(obj: object, param_name: str) -> Optional[Generator]:
    if obj is not None and not inspect.isgenerator(obj):
        raise ParameterCheckError(
            f'Param "{param_name}" is not a generator (return value of function that yields) Got '
            f"{obj} instead"
        )
    return obj


def generator(obj: object) -> Generator:
    if not inspect.isgenerator(obj):
        raise ParameterCheckError(
            f"Not a generator (return value of function that yields) Got {obj} instead"
        )
    return obj


def opt_generator(obj: object) -> Optional[Generator]:
    if obj is not None and not inspect.isgenerator(obj):
        raise ParameterCheckError(
            f"Not a generator (return value of function that yields) Got {obj} instead"
        )
    return obj


# ########################
# ##### INT
# ########################


def int_param(obj: object, param_name: str) -> int:
    if not isinstance(obj, int):
        raise _param_type_mismatch_exception(obj, int, param_name)
    return obj


@overload
def opt_int_param(obj: object, param_name: str, default: int) -> int:
    ...


@overload
def opt_int_param(obj: object, param_name: str) -> Optional[int]:
    ...


def opt_int_param(obj: object, param_name: str, default: Optional[int] = None) -> Optional[int]:
    if obj is not None and not isinstance(obj, int):
        raise _param_type_mismatch_exception(obj, int, param_name)
    return default if obj is None else obj


def int_value_param(obj: object, value: int, param_name: str) -> int:
    if not isinstance(obj, int):
        raise _param_type_mismatch_exception(obj, int, param_name)
    if obj != value:
        raise _param_invariant_exception(param_name, f"Should be equal to {value}")

    return obj


def int_elem(ddict: Dict, key: str) -> int:
    dict_param(ddict, "ddict")
    str_param(key, "key")

    value = ddict[key]
    if not isinstance(value, int):
        raise _element_check_error(key, value, ddict, int)
    return value


def opt_int_elem(ddict: Dict, key: str) -> Optional[int]:
    dict_param(ddict, "ddict")
    str_param(key, "key")

    value = ddict.get(key)
    if value is None:
        return None
    if not isinstance(value, int):
        raise _element_check_error(key, value, ddict, int)
    return value


# ########################
# ##### INST
# ########################

# mypy note: Attempting to use the passed type (Type[T] -> T) to infer the output type has
# issues with abstract classes, so here we count on the incoming object to be typed before
# this runtime validation check.


def inst_param(
    obj: T, param_name: str, ttype: TypeOrTupleOfTypes, additional_message: Optional[str] = None
) -> T:
    if not isinstance(obj, ttype):
        raise _param_type_mismatch_exception(
            obj, ttype, param_name, additional_message=additional_message
        )
    return obj


@overload
def opt_inst_param(obj: Optional[T], param_name: str, ttype: TypeOrTupleOfTypes, default: T) -> T:
    ...


@overload
def opt_inst_param(obj: T, param_name: str, ttype: TypeOrTupleOfTypes) -> T:
    ...


def opt_inst_param(
    obj: T, param_name: str, ttype: TypeOrTupleOfTypes, default: Optional[T] = None
) -> Optional[T]:
    if obj is not None and not isinstance(obj, ttype):
        raise _param_type_mismatch_exception(obj, ttype, param_name)
    return default if obj is None else obj


def inst(obj: T, ttype: TypeOrTupleOfTypes, desc: Optional[str] = None) -> T:
    if not isinstance(obj, ttype):
        raise _type_mismatch_error(obj, ttype, desc)
    return obj


def opt_inst(
    obj: T, ttype: TypeOrTupleOfTypes, desc: Optional[str] = None, default: Optional[T] = None
) -> Optional[T]:
    if obj is not None and not isinstance(obj, ttype):
        raise _type_mismatch_error(obj, ttype, desc)
    return default if obj is None else obj


# ########################
# ##### LIST
# ########################


def list_param(obj: object, param_name: str, of_type: Optional[TypeOrTupleOfTypes] = None) -> List:
    from dagster.utils import frozenlist

    if not isinstance(obj, (frozenlist, list)):
        raise _param_type_mismatch_exception(obj, (frozenlist, list), param_name)

    if not of_type:
        return obj

    return _check_iterable_items(obj, of_type, "list")


def opt_list_param(
    obj: object, param_name: str, of_type: Optional[TypeOrTupleOfTypes] = None
) -> List:
    """Ensures argument obj is a list or None; in the latter case, instantiates an empty list
    and returns it.

    If the of_type argument is provided, also ensures that list items conform to the type specified
    by of_type.
    """
    from dagster.utils import frozenlist

    if obj is not None and not isinstance(obj, (frozenlist, list)):
        raise _param_type_mismatch_exception(obj, (frozenlist, list), param_name)

    if not obj:
        return []
    if not of_type:
        return obj

    return _check_iterable_items(obj, of_type, "list")


# pyright understands this overload but not mypy
@overload
def opt_nullable_list_param(  # type: ignore
    obj: None,
    param_name: str,
    of_type: Optional[TypeOrTupleOfTypes] = ...,
) -> None:
    ...


@overload
def opt_nullable_list_param(
    obj: List[T],
    param_name: str,
    of_type: Optional[TypeOrTupleOfTypes] = ...,
) -> List[T]:
    ...


def opt_nullable_list_param(
    obj: object, param_name: str, of_type: Optional[TypeOrTupleOfTypes] = None
) -> Optional[List]:
    """Ensures argument obj is a list or None. Returns None if input is None.

    If the of_type argument is provided, also ensures that list items conform to the type specified
    by of_type.
    """
    from dagster.utils import frozenlist

    if obj is not None and not isinstance(obj, (frozenlist, list)):
        raise _param_type_mismatch_exception(obj, (frozenlist, list), param_name)

    if not obj:
        return None if obj is None else []
    if not of_type:
        return obj

    return _check_iterable_items(obj, of_type, "list")


def two_dim_list_param(
    obj: object, param_name: str, of_type: Optional[TypeOrTupleOfTypes] = None
) -> List[List]:
    obj = list_param(obj, param_name, of_type=list)
    if not obj:
        raise CheckError("You must pass a list of lists. Received an empty list.")
    for sublist in obj:
        sublist = list_param(sublist, f"sublist_{param_name}", of_type=of_type)
        if len(sublist) != len(obj[0]):
            raise CheckError("All sublists in obj must have the same length")
    return obj


def list_elem(ddict: Dict, key: str, of_type: Optional[TypeOrTupleOfTypes] = None) -> List:
    dict_param(ddict, "ddict")
    str_param(key, "key")
    opt_class_param(of_type, "of_type")

    value = ddict.get(key)

    if isinstance(value, list):
        if not of_type:
            return value

        return _check_iterable_items(value, of_type, "list")

    raise _element_check_error(key, value, ddict, list)


def opt_list_elem(ddict: Dict, key: str, of_type: Optional[TypeOrTupleOfTypes] = None) -> List:
    dict_param(ddict, "ddict")
    str_param(key, "key")
    opt_class_param(of_type, "of_type")

    value = ddict.get(key)

    if value is None:
        return []

    if not isinstance(value, list):
        raise _element_check_error(key, value, ddict, list)

    if not of_type:
        return value

    return _check_iterable_items(value, of_type, "list")


def is_list(
    obj: object, of_type: Optional[TypeOrTupleOfTypes] = None, desc: Optional[str] = None
) -> List:
    if not isinstance(obj, list):
        raise _type_mismatch_error(obj, list, desc)

    if not of_type:
        return obj

    return _check_iterable_items(obj, of_type, "list")


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
    if not isinstance(obj, collections.abc.Mapping):
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


# pyright understands this overload but not mypy
@overload
def opt_nullable_mapping_param(  # type: ignore
    obj: None,
    param_name: str,
    key_type: Optional[TypeOrTupleOfTypes] = ...,
    value_type: Optional[TypeOrTupleOfTypes] = ...,
    additional_message: Optional[str] = ...,
) -> None:
    ...


@overload
def opt_nullable_mapping_param(
    obj: Mapping[T, U],
    param_name: str,
    key_type: Optional[TypeOrTupleOfTypes] = ...,
    value_type: Optional[TypeOrTupleOfTypes] = ...,
    additional_message: Optional[str] = ...,
) -> Mapping[T, U]:
    ...


def opt_nullable_mapping_param(
    obj: Optional[Mapping[T, U]],
    param_name: str,
    key_type: Optional[TypeOrTupleOfTypes] = None,
    value_type: Optional[TypeOrTupleOfTypes] = None,
    additional_message: Optional[str] = None,
) -> Optional[Mapping[T, U]]:
    if obj is None:
        return dict()
    else:
        return mapping_param(obj, param_name, key_type, value_type, additional_message)


# ########################
# ##### NOT NONE
# ########################


def not_none_param(obj: Optional[T], param_name: str) -> T:
    if obj is None:
        raise _param_invariant_exception(param_name, f"Param {param_name} cannot be none")
    return obj


def not_none(value: Optional[T], desc: Optional[str] = None) -> T:
    if value is None:
        raise ValueError(f"Expected non-None value: {desc}")
    return value


# ########################
# ##### NUMERIC
# ########################


def numeric_param(obj: object, param_name: str) -> Numeric:
    if not isinstance(obj, (int, float)):
        raise _param_type_mismatch_exception(obj, (int, float), param_name)
    return obj


@overload
def opt_numeric_param(obj: object, param_name: str, default: Numeric) -> Numeric:
    ...


@overload
def opt_numeric_param(obj: object, param_name: str) -> Optional[Numeric]:
    ...


def opt_numeric_param(
    obj: object, param_name: str, default: Optional[Numeric] = None
) -> Optional[Numeric]:
    if obj is not None and not isinstance(obj, (int, float)):
        raise _param_type_mismatch_exception(obj, (int, float), param_name)
    return default if obj is None else obj


# ########################
# ##### PATH
# ########################


def path_param(obj: Union[str, PathLike], param_name: str) -> str:
    if not isinstance(obj, (str, PathLike)):
        raise _param_type_mismatch_exception(obj, (str, PathLike), param_name)
    return fspath(obj)


@overload
def opt_path_param(obj: None, param_name: str, default: None = ...) -> None:
    ...


@overload
def opt_path_param(obj: None, param_name: str, default: Union[str, PathLike]) -> str:
    ...


@overload
def opt_path_param(
    obj: Union[str, PathLike], param_name: str, default: Optional[Union[str, PathLike]] = ...
) -> str:
    ...


def opt_path_param(
    obj: Optional[Union[str, PathLike]],
    param_name: str,
    default: Optional[Union[str, PathLike]] = None,
) -> Optional[Union[str, PathLike]]:
    if obj is None:
        return str(default) if default is not None else None
    else:
        return path_param(obj, param_name)


# ########################
# ##### SEQUENCE
# ########################


def sequence_param(
    obj: Sequence[T], param_name: str, of_type: Optional[TypeOrTupleOfTypes] = None
) -> Sequence[T]:
    if not isinstance(obj, collections.abc.Sequence):
        raise _param_type_mismatch_exception(obj, (collections.abc.Sequence,), param_name)

    if not of_type:
        return obj

    return _check_iterable_items(obj, of_type, "sequence")


def opt_sequence_param(
    obj: Optional[Sequence[T]], param_name: str, of_type: Optional[TypeOrTupleOfTypes] = None
) -> Sequence[T]:
    if obj is None:
        return []
    elif not isinstance(obj, collections.abc.Sequence):
        raise _param_type_mismatch_exception(obj, (collections.abc.Sequence,), param_name)
    elif of_type is not None:
        return _check_iterable_items(obj, of_type, "sequence")
    else:
        return obj


@overload
def opt_nullable_sequence_param(
    obj: None, param_name: str, of_type: Optional[TypeOrTupleOfTypes] = ...
) -> None:
    ...


@overload
def opt_nullable_sequence_param(
    obj: Sequence[T], param_name: str, of_type: Optional[TypeOrTupleOfTypes] = None
) -> Sequence[T]:
    ...


def opt_nullable_sequence_param(
    obj: Optional[Sequence[T]], param_name: str, of_type: Optional[TypeOrTupleOfTypes] = None
) -> Optional[Sequence[T]]:
    if obj is None:
        return None
    else:
        return opt_sequence_param(obj, param_name, of_type)


# ########################
# ##### SET
# ########################


def set_param(
    obj: AbstractSet[T], param_name: str, of_type: Optional[TypeOrTupleOfTypes] = None
) -> AbstractSet[T]:
    if not isinstance(obj, (frozenset, set)):
        raise _param_type_mismatch_exception(obj, (frozenset, set), param_name)

    if not of_type:
        return obj

    return _check_iterable_items(obj, of_type, "set")


def opt_set_param(
    obj: Optional[AbstractSet[T]], param_name: str, of_type: Optional[TypeOrTupleOfTypes] = None
) -> AbstractSet[T]:
    """Ensures argument obj is a set or None; in the latter case, instantiates an empty set
    and returns it.

    If the of_type argument is provided, also ensures that list items conform to the type specified
    by of_type.
    """
    if obj is None:
        return set()
    elif obj is not None and not isinstance(obj, (frozenset, set)):
        raise _param_type_mismatch_exception(obj, (frozenset, set), param_name)
    elif not of_type:
        return obj

    return _check_iterable_items(obj, of_type, "set")


@overload
def opt_nullable_set_param(
    obj: None, param_name: str, of_type: Optional[TypeOrTupleOfTypes] = ...
) -> None:
    ...


@overload
def opt_nullable_set_param(
    obj: AbstractSet[T], param_name: str, of_type: Optional[TypeOrTupleOfTypes] = ...
) -> AbstractSet[T]:
    ...


def opt_nullable_set_param(
    obj: Optional[AbstractSet[T]], param_name: str, of_type: Optional[TypeOrTupleOfTypes] = None
) -> Optional[AbstractSet[T]]:
    """Ensures argument obj is a set or None. Returns None if input is None.
    and returns it.

    If the of_type argument is provided, also ensures that list items conform to the type specified
    by of_type.
    """
    if obj is None:
        return None
    elif not isinstance(obj, (frozenset, set)):
        raise _param_type_mismatch_exception(obj, (frozenset, set), param_name)
    elif not of_type:
        return obj

    return _check_iterable_items(obj, of_type, "set")


# ########################
# ##### STR
# ########################


def str_param(obj: object, param_name: str) -> str:
    if not isinstance(obj, str):
        raise _param_type_mismatch_exception(obj, str, param_name)
    return obj


@overload
def opt_str_param(obj: object, param_name: str, default: str) -> str:
    ...


@overload
def opt_str_param(obj: object, param_name: str) -> Optional[str]:
    ...


def opt_str_param(obj: object, param_name: str, default: Optional[str] = None) -> Optional[str]:
    if obj is not None and not isinstance(obj, str):
        raise _param_type_mismatch_exception(obj, str, param_name)
    return default if obj is None else obj


def opt_nonempty_str_param(
    obj: object, param_name: str, default: Optional[str] = None
) -> Optional[str]:
    if obj is not None and not isinstance(obj, str):
        raise _param_type_mismatch_exception(obj, str, param_name)
    return default if obj is None or obj == "" else obj


def str_elem(ddict: Dict, key: str) -> str:
    dict_param(ddict, "ddict")
    str_param(key, "key")

    value = ddict[key]
    if not isinstance(value, str):
        raise _element_check_error(key, value, ddict, str)
    return value


def opt_str_elem(ddict: Dict, key: str) -> Optional[str]:
    dict_param(ddict, "ddict")
    str_param(key, "key")

    value = ddict.get(key)
    if value is None:
        return None
    if not isinstance(value, str):
        raise _element_check_error(key, value, ddict, str)
    return value


# ########################
# ##### TUPLE
# ########################


def tuple_param(
    obj: object,
    param_name: str,
    of_type: Optional[TypeOrTupleOfTypes] = None,
    of_shape: Optional[Tuple[TypeOrTupleOfTypes, ...]] = None,
) -> Tuple:
    """Ensure param is a tuple and is of a specified type. `of_type` defines a variadic tuple type--
    `obj` may be of any length, but each element must match the `of_type` argmument. `of_shape`
    defines a fixed-length tuple type-- each element must match the corresponding element in
    `of_shape`. Passing both `of_type` and `of_shape` will raise an error.
    """
    if not isinstance(obj, tuple):
        raise _param_type_mismatch_exception(obj, tuple, param_name)

    if of_type is None and of_shape is None:
        return obj

    if of_type and of_shape:
        raise CheckError("Must specify exactly one `of_type` or `of_shape`")

    return _check_tuple_items(obj, of_type, of_shape)


@overload
def opt_tuple_param(
    obj: object,
    param_name: str,
    default: Tuple,
    of_type: Optional[TypeOrTupleOfTypes] = None,
    of_shape: Optional[Tuple[TypeOrTupleOfTypes, ...]] = None,
) -> Tuple:
    ...


@overload
def opt_tuple_param(
    obj: object,
    param_name: str,
    default: None = ...,
    of_type: TypeOrTupleOfTypes = ...,
    of_shape: Optional[Tuple[TypeOrTupleOfTypes, ...]] = ...,
) -> Optional[Tuple]:
    ...


def opt_tuple_param(
    obj: object,
    param_name: str,
    default: Optional[Tuple] = None,
    of_type: Optional[TypeOrTupleOfTypes] = None,
    of_shape: Optional[Tuple[TypeOrTupleOfTypes, ...]] = None,
) -> Optional[Tuple]:
    """Ensure optional param is a tuple and is of a specified type. `default` is returned if `obj`
    is None. `of_type` defines a variadic tuple type-- `obj` may be of any length, but each element
    must match the `of_type` argmument. `of_shape` defines a fixed-length tuple type-- each element
    must match the corresponding element in `of_shape`. Passing both `of_type` and `of_shape` will
    raise an error.
    """
    if obj is not None and not isinstance(obj, tuple):
        raise _param_type_mismatch_exception(obj, tuple, param_name)

    if obj is None:
        return default

    if of_type is None and of_shape is None:
        return obj

    if of_type and of_shape:
        raise CheckError("Must specify exactly one `of_type` or `of_shape`")

    return _check_tuple_items(obj, of_type, of_shape)


def is_tuple(
    obj: object,
    of_type: Optional[TypeOrTupleOfTypes] = None,
    of_shape: Optional[Tuple[TypeOrTupleOfTypes, ...]] = None,
    desc: Optional[str] = None,
) -> Tuple:
    """Ensure target is a tuple and is of a specified type. `of_type` defines a variadic tuple
    type-- `obj` may be of any length, but each element must match the `of_type` argmument.
    `of_shape` defines a fixed-length tuple type-- each element must match the corresponding element
    in `of_shape`. Passing both `of_type` and `of_shape` will raise an error.
    """
    if not isinstance(obj, tuple):
        raise _type_mismatch_error(obj, tuple, desc)

    if of_type is None and of_shape is None:
        return obj

    if of_type and of_shape:
        raise CheckError("Must specify exactly one `of_type` or `of_shape`")

    return _check_tuple_items(obj, of_type, of_shape)


def _check_tuple_items(
    obj_tuple: Tuple,
    of_type: Optional[TypeOrTupleOfTypes] = None,
    of_shape: Optional[Tuple[TypeOrTupleOfTypes, ...]] = None,
) -> Tuple:
    if of_shape is not None:
        len_tuple = len(obj_tuple)
        len_type = len(of_shape)
        if not len_tuple == len_type:
            raise CheckError(
                f"Tuple mismatches type: tuple had {len_tuple} members but type had " f"{len_type}"
            )

        for (i, obj) in enumerate(obj_tuple):
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
                    f"{repr(obj)} of type {type(obj)}.{additional_message}"
                )

    elif of_type is not None:
        _check_iterable_items(obj_tuple, of_type, "tuple")

    return obj_tuple


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


def assert_never(value: NoReturn) -> NoReturn:
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
    key: object, value: object, ddict: Dict, ttype: TypeOrTupleOfTypes
) -> ElementCheckError:
    return ElementCheckError(
        f"Value {repr(value)} from key {key} is not a {repr(ttype)}. Dict: {repr(ddict)}"
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
            f'Param "{param_name}" is not one of {type_names}. Got {repr(obj)} which is type {type(obj)}.'
            f"{additional_message}"
        )
    else:
        return ParameterCheckError(
            f'Param "{param_name}" is not a {ttype.__name__}. Got {repr(obj)} which is type {type(obj)}.'
            f"{additional_message}"
        )


def _param_class_mismatch_exception(
    obj: object,
    param_name: str,
    superclass: Optional[type],
    optional: bool,
) -> ParameterCheckError:
    opt_clause = optional and "be None or" or ""
    subclass_clause = superclass and f"that inherits from {superclass.__name__}" or ""
    return ParameterCheckError(
        f'Param "{param_name}" must {opt_clause}be a class{subclass_clause}. Got {repr(obj)} of type {type(obj)}.'
    )


def _type_mismatch_error(
    obj: object, ttype: TypeOrTupleOfTypes, desc: Optional[str] = None
) -> CheckError:
    type_message = (
        f"not one of {sorted([t.__name__ for t in ttype])}"
        if isinstance(ttype, tuple)
        else f"not a {ttype.__name__}"
    )
    repr_obj = repr(obj)
    desc_str = f" Desc: {desc}" if desc else ""
    return CheckError(
        f"Object {repr_obj} is {type_message}. Got {repr_obj} with type {type(obj)}.{desc_str}"
    )


def _param_not_callable_exception(obj: Any, param_name: str) -> ParameterCheckError:
    return ParameterCheckError(
        f'Param "{param_name}" is not callable. Got {repr(obj)} with type {type(obj)}.'
    )


def _param_invariant_exception(param_name: str, desc: Optional[str] = None) -> ParameterCheckError:
    return ParameterCheckError(
        f"Invariant violation for parameter {param_name}. Description: {desc}"
    )


V = TypeVar("V", bound=Iterable)


def _check_iterable_items(
    obj_iter: V, of_type: TypeOrTupleOfTypes, collection_name: str = "iterable"
) -> V:
    for obj in obj_iter:

        if not isinstance(obj, of_type):
            if isinstance(obj, type):
                additional_message = (
                    " Did you pass a class where you were expecting an instance of the class?"
                )
            else:
                additional_message = ""
            raise CheckError(
                f"Member of {collection_name} mismatches type. Expected {of_type}. Got {repr(obj)} of type "
                f"{type(obj)}.{additional_message}"
            )

    return obj_iter


W = TypeVar("W", bound=Mapping)
X = TypeVar("X", bound=Mapping)


def _check_mapping_entries(
    obj: W,
    key_type: Optional[TypeOrTupleOfTypes] = None,
    value_type: Optional[TypeOrTupleOfTypes] = None,
    key_check: Callable = isinstance,
    value_check: Callable = isinstance,
    mapping_type: Type = collections.abc.Mapping,
) -> W:
    """Enforces that the keys/values conform to the types specified by key_type, value_type."""
    for key, value in obj.items():
        if key_type and not key_check(key, key_type):
            raise CheckError(
                f"Key in {mapping_type.__name__} mismatches type. Expected {repr(key_type)}. Got {repr(key)}"
            )

        if value_type and not value_check(value, value_type):
            raise CheckError(
                f"Value in {mapping_type.__name__} mismatches expected type for key {key}. Expected value "
                f"of type {repr(value_type)}. Got value {value} of type {type(value)}."
            )

    return obj


def _check_two_dim_mapping_entries(
    obj: W,
    key_type: Optional[TypeOrTupleOfTypes] = None,
    value_type: Optional[TypeOrTupleOfTypes] = None,
    mapping_type: Type = collections.abc.Mapping,
) -> W:
    _check_mapping_entries(
        obj, key_type, mapping_type, mapping_type=mapping_type
    )  # check level one

    for inner_mapping in obj.values():
        _check_mapping_entries(
            inner_mapping, key_type, value_type, mapping_type=mapping_type
        )  # check level two

    return obj
