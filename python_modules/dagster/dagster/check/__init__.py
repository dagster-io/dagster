import inspect
import sys
from typing import (
    AbstractSet,
    Any,
    Callable,
    Dict,
    Generator,
    List,
    NoReturn,
    Optional,
    Set,
    Tuple,
    Union,
)

Type = Union[type, Tuple[type, ...]]
Numeric = Union[int, float]


class CheckError(Exception):
    pass


class ParameterCheckError(CheckError):
    pass


class ElementCheckError(CheckError):
    pass


class NotImplementedCheckError(CheckError):
    pass


def _param_type_mismatch_exception(
    obj: Any, ttype: Type, param_name: str, additional_message: str = None
) -> ParameterCheckError:
    if isinstance(ttype, tuple):
        type_names = sorted([t.__name__ for t in ttype])
        return ParameterCheckError(
            'Param "{name}" is not one of {type_names}. Got {obj} which is type {obj_type}.'
            "{additional_message}".format(
                name=param_name,
                obj=repr(obj),
                type_names=type_names,
                obj_type=type(obj),
                additional_message=" " + additional_message if additional_message else "",
            )
        )
    else:
        return ParameterCheckError(
            'Param "{name}" is not a {type}. Got {obj} which is type {obj_type}.'
            "{additional_message}".format(
                name=param_name,
                obj=repr(obj),
                type=ttype.__name__,
                obj_type=type(obj),
                additional_message=" " + additional_message if additional_message else "",
            )
        )


def _not_type_param_subclass_mismatch_exception(obj: Any, param_name: str) -> ParameterCheckError:
    return ParameterCheckError(
        'Param "{name}" was supposed to be a type. Got {obj} of type {obj_type}'.format(
            name=param_name, obj=repr(obj), obj_type=type(obj)
        )
    )


def _param_subclass_mismatch_exception(
    obj: Any, superclass: Type, param_name: str
) -> ParameterCheckError:
    return ParameterCheckError(
        'Param "{name}" is a type but not a subclass of {superclass}. Got {obj} instead'.format(
            name=param_name, superclass=superclass, obj=obj
        )
    )


def _type_mismatch_error(obj: Any, ttype: Type, desc: str = None) -> CheckError:
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


def _not_callable_exception(obj: Any, param_name: str) -> ParameterCheckError:
    return ParameterCheckError(
        'Param "{name}" is not callable. Got {obj} with type {obj_type}.'.format(
            name=param_name, obj=repr(obj), obj_type=type(obj)
        )
    )


def _param_invariant_exception(param_name: str, desc: str = None) -> ParameterCheckError:
    return ParameterCheckError(
        "Invariant violation for parameter {param_name}. Description: {desc}".format(
            param_name=param_name, desc=desc
        )
    )


def failed(desc: str) -> NoReturn:  # type: ignore[misc]
    if not isinstance(desc, str):
        raise CheckError("desc argument must be a string")

    raise CheckError("Failure condition: {desc}".format(desc=desc))


def not_implemented(desc: str):
    if not isinstance(desc, str):
        raise CheckError("desc argument must be a string")

    raise NotImplementedCheckError(f"Not implemented: {desc}")


def inst(obj: Any, ttype: Type, desc: str = None) -> Any:
    if not isinstance(obj, ttype):
        raise _type_mismatch_error(obj, ttype, desc)
    return obj


def opt_inst(obj: Any, ttype: Type, desc: str = None, default: Any = None) -> Any:
    if obj is not None and not isinstance(obj, ttype):
        raise _type_mismatch_error(obj, ttype, desc)
    return default if obj is None else obj


def subclass(obj: Any, superclass: Type, desc: str = None) -> Any:
    if not issubclass(obj, superclass):
        raise _type_mismatch_error(obj, superclass, desc)

    return obj


def is_callable(obj: Any, desc: str = None) -> Callable:
    if not callable(obj):
        if desc:
            raise CheckError(
                "Must be callable. Got {obj}. Description: {desc}".format(obj=repr(obj), desc=desc)
            )
        else:
            raise CheckError(
                "Must be callable. Got {obj}. Description: {desc}".format(obj=obj, desc=desc)
            )
    return obj


def not_none_param(obj: Any, param_name: str) -> Any:
    if obj is None:
        raise _param_invariant_exception(param_name, f"Param {param_name} cannot be none")
    return obj


def invariant(condition: Any, desc: str = None) -> bool:
    if not condition:
        if desc:
            raise CheckError(f"Invariant failed. Description: {desc}")
        else:
            raise CheckError("Invariant failed.")

    return True


def param_invariant(condition: Any, param_name: str, desc: str = None):
    if not condition:
        raise _param_invariant_exception(param_name, desc)


def inst_param(obj: Any, param_name: str, ttype: Type, additional_message: str = None) -> Any:
    if not isinstance(obj, ttype):
        raise _param_type_mismatch_exception(
            obj, ttype, param_name, additional_message=additional_message
        )
    return obj


def opt_inst_param(obj: Any, param_name: str, ttype: Type, default: Any = None) -> Any:
    if obj is not None and not isinstance(obj, ttype):
        raise _param_type_mismatch_exception(obj, ttype, param_name)
    return default if obj is None else obj


def callable_param(obj: Any, param_name: str) -> Callable:
    if not callable(obj):
        raise _not_callable_exception(obj, param_name)
    return obj


def opt_callable_param(obj: Any, param_name: str, default: Callable = None) -> Optional[Callable]:
    if obj is not None and not callable(obj):
        raise _not_callable_exception(obj, param_name)
    return default if obj is None else obj


def int_param(obj: Any, param_name: str) -> int:
    if not isinstance(obj, int):
        raise _param_type_mismatch_exception(obj, int, param_name)
    return obj


def int_value_param(obj: Any, value: int, param_name: str) -> int:
    if not isinstance(obj, int):
        raise _param_type_mismatch_exception(obj, int, param_name)
    if obj != value:
        raise _param_invariant_exception(param_name, f"Should be equal to {value}")

    return obj


def opt_int_param(obj: Any, param_name: str, default: int = None) -> Optional[int]:
    if obj is not None and not isinstance(obj, int):
        raise _param_type_mismatch_exception(obj, int, param_name)
    return default if obj is None else obj


def float_param(obj: Any, param_name: str) -> float:
    if not isinstance(obj, float):
        raise _param_type_mismatch_exception(obj, float, param_name)
    return obj


def opt_numeric_param(obj: Any, param_name: str, default: Numeric = None) -> Optional[Numeric]:
    if obj is not None and not isinstance(obj, (int, float)):
        raise _param_type_mismatch_exception(obj, (int, float), param_name)
    return default if obj is None else obj


def numeric_param(obj: Any, param_name: str) -> Numeric:
    if not isinstance(obj, (int, float)):
        raise _param_type_mismatch_exception(obj, (int, float), param_name)
    return obj


def opt_float_param(obj: Any, param_name: str, default: float = None) -> Optional[float]:
    if obj is not None and not isinstance(obj, float):
        raise _param_type_mismatch_exception(obj, float, param_name)
    return default if obj is None else obj


def str_param(obj: Any, param_name: str) -> str:
    if not isinstance(obj, str):
        raise _param_type_mismatch_exception(obj, str, param_name)
    return obj


def opt_str_param(obj: Any, param_name: str, default: str = None) -> Optional[str]:
    if obj is not None and not isinstance(obj, str):
        raise _param_type_mismatch_exception(obj, str, param_name)
    return default if obj is None else obj


def opt_nonempty_str_param(obj: Any, param_name: str, default: str = None) -> Optional[str]:
    if obj is not None and not isinstance(obj, str):
        raise _param_type_mismatch_exception(obj, str, param_name)
    return default if obj is None or obj == "" else obj


def bool_param(obj: Any, param_name: str) -> bool:
    if not isinstance(obj, bool):
        raise _param_type_mismatch_exception(obj, bool, param_name)
    return obj


def opt_bool_param(obj: Any, param_name: str, default: bool = None) -> Optional[bool]:
    if obj is not None and not isinstance(obj, bool):
        raise _param_type_mismatch_exception(obj, bool, param_name)
    return default if obj is None else obj


def is_list(obj_list: Any, of_type: Type = None, desc: str = None) -> List:
    if not isinstance(obj_list, list):
        raise _type_mismatch_error(obj_list, list, desc)

    if not of_type:
        return obj_list

    return _check_list_items(obj_list, of_type)


def is_tuple(obj_tuple: Any, of_type: Type = None, desc: str = None) -> Tuple:
    if not isinstance(obj_tuple, tuple):
        raise _type_mismatch_error(obj_tuple, tuple, desc)

    if not of_type:
        return obj_tuple

    return _check_tuple_items(obj_tuple, of_type)


def list_param(obj_list: Any, param_name: str, of_type: Type = None) -> List:
    from dagster.utils import frozenlist

    if not isinstance(obj_list, (frozenlist, list)):
        raise _param_type_mismatch_exception(obj_list, (frozenlist, list), param_name)

    if not of_type:
        return obj_list

    return _check_list_items(obj_list, of_type)


def set_param(obj_set: Any, param_name: str, of_type: Type = None) -> AbstractSet:
    if not isinstance(obj_set, (frozenset, set)):
        raise _param_type_mismatch_exception(obj_set, (frozenset, set), param_name)

    if not of_type:
        return obj_set

    return _check_set_items(obj_set, of_type)


def tuple_param(obj: Any, param_name: str, of_type: Type = None) -> Tuple:
    if not isinstance(obj, tuple):
        raise _param_type_mismatch_exception(obj, tuple, param_name)

    if of_type is None:
        return obj

    return _check_tuple_items(obj, of_type)


def matrix_param(matrix: Any, param_name: str, of_type: Type = None) -> List[List]:
    matrix = list_param(matrix, param_name, of_type=list)
    if not matrix:
        raise CheckError("You must pass a list of lists. Received an empty list.")
    for sublist in matrix:
        sublist = list_param(sublist, "sublist_{}".format(param_name), of_type=of_type)
        if len(sublist) != len(matrix[0]):
            raise CheckError("All sublists in matrix must have the same length")
    return matrix


def opt_tuple_param(
    obj: Any, param_name: str, default: Tuple = None, of_type: Type = None
) -> Optional[Tuple]:
    if obj is not None and not isinstance(obj, tuple):
        raise _param_type_mismatch_exception(obj, tuple, param_name)

    if obj is None:
        return default

    if of_type is None:
        return obj

    return _check_tuple_items(obj, of_type)


def _check_list_items(obj_list: Any, of_type: Type) -> List:
    for obj in obj_list:
        if not isinstance(obj, of_type):
            if isinstance(obj, type):
                additional_message = (
                    " Did you pass a class where you were expecting an instance of the class?"
                )
            else:
                additional_message = ""
            raise CheckError(
                "Member of list mismatches type. Expected {of_type}. Got {obj_repr} of type "
                "{obj_type}.{additional_message}".format(
                    of_type=of_type,
                    obj_repr=repr(obj),
                    obj_type=type(obj),
                    additional_message=additional_message,
                )
            )

    return obj_list


def _check_set_items(obj_set: Any, of_type: Type) -> Set:
    for obj in obj_set:

        if not isinstance(obj, of_type):
            if isinstance(obj, type):
                additional_message = (
                    " Did you pass a class where you were expecting an instance of the class?"
                )
            else:
                additional_message = ""
            raise CheckError(
                "Member of set mismatches type. Expected {of_type}. Got {obj_repr} of type "
                "{obj_type}.{additional_message}".format(
                    of_type=of_type,
                    obj_repr=repr(obj),
                    obj_type=type(obj),
                    additional_message=additional_message,
                )
            )

    return obj_set


def _check_tuple_items(obj_tuple: Any, of_type: Union[Tuple, Type]) -> Tuple:
    if isinstance(of_type, tuple):
        len_tuple = len(obj_tuple)
        len_type = len(of_type)
        if not len_tuple == len_type:
            raise CheckError(
                "Tuple mismatches type: tuple had {len_tuple} members but type had "
                "{len_type}".format(len_tuple=len_tuple, len_type=len_type)
            )

        for (i, obj) in enumerate(obj_tuple):
            of_type_i = of_type[i]
            if not isinstance(obj, of_type_i):
                if isinstance(obj, type):
                    additional_message = (
                        " Did you pass a class where you were expecting an instance of the class?"
                    )
                else:
                    additional_message = ""
                raise CheckError(
                    "Member of tuple mismatches type at index {index}. Expected {of_type}. Got "
                    "{obj_repr} of type {obj_type}.{additional_message}".format(
                        index=i,
                        of_type=of_type_i,
                        obj_repr=repr(obj),
                        obj_type=type(obj),
                        additional_message=additional_message,
                    )
                )

    else:
        for (i, obj) in enumerate(obj_tuple):
            if not isinstance(obj, of_type):
                if isinstance(obj, type):
                    additional_message = (
                        " Did you pass a class where you were expecting an instance of the class?"
                    )
                else:
                    additional_message = ""
                raise CheckError(
                    "Member of tuple mismatches type at index {index}. Expected {of_type}. Got "
                    "{obj_repr} of type {obj_type}.{additional_message}".format(
                        index=i,
                        of_type=of_type,
                        obj_repr=repr(obj),
                        obj_type=type(obj),
                        additional_message=additional_message,
                    )
                )

    return obj_tuple


def opt_list_param(obj_list: Any, param_name: str, of_type: Type = None) -> List:
    """Ensures argument obj_list is a list or None; in the latter case, instantiates an empty list
    and returns it.

    If the of_type argument is provided, also ensures that list items conform to the type specified
    by of_type.
    """
    from dagster.utils import frozenlist

    if obj_list is not None and not isinstance(obj_list, (frozenlist, list)):
        raise _param_type_mismatch_exception(obj_list, (frozenlist, list), param_name)

    if not obj_list:
        return []
    if not of_type:
        return obj_list

    return _check_list_items(obj_list, of_type)


def opt_set_param(obj_set: Any, param_name: str, of_type: Type = None) -> AbstractSet:
    """Ensures argument obj_set is a set or None; in the latter case, instantiates an empty set
    and returns it.

    If the of_type argument is provided, also ensures that list items conform to the type specified
    by of_type.
    """
    if obj_set is not None and not isinstance(obj_set, (frozenset, set)):
        raise _param_type_mismatch_exception(obj_set, (frozenset, set), param_name)
    if not obj_set:
        return set()
    if not of_type:
        return obj_set

    return _check_set_items(obj_set, of_type)


def opt_nullable_list_param(obj_list: Any, param_name: str, of_type: Type = None) -> Optional[List]:
    """Ensures argument obj_list is a list or None. Returns None if input is None.

    If the of_type argument is provided, also ensures that list items conform to the type specified
    by of_type.
    """
    from dagster.utils import frozenlist

    if obj_list is not None and not isinstance(obj_list, (frozenlist, list)):
        raise _param_type_mismatch_exception(obj_list, (frozenlist, list), param_name)

    if not obj_list:
        return None if obj_list is None else []
    if not of_type:
        return obj_list

    return _check_list_items(obj_list, of_type)


def _check_key_value_types(
    obj: Any,
    key_type: Type = None,
    value_type: Type = None,
    key_check: Callable = isinstance,
    value_check: Callable = isinstance,
) -> Dict:
    """Ensures argument obj is a dictionary, and enforces that the keys/values conform to the types
    specified by key_type, value_type.
    """
    if not isinstance(obj, dict):
        raise _type_mismatch_error(obj, dict)

    for key, value in obj.items():
        if key_type and not key_check(key, key_type):
            raise CheckError(
                "Key in dictionary mismatches type. Expected {key_type}. Got {obj_repr}".format(
                    key_type=repr(key_type), obj_repr=repr(key)
                )
            )

        if value_type and not value_check(value, value_type):
            raise CheckError(
                "Value in dictionary mismatches expected type for key {key}. Expected value "
                "of type {vtype}. Got value {value} of type {obj_type}.".format(
                    vtype=repr(value_type), obj_type=type(value), key=key, value=value
                )
            )

    return obj


def dict_param(
    obj: Any,
    param_name: str,
    key_type: Type = None,
    value_type: Type = None,
    additional_message: str = None,
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

    return _check_key_value_types(obj, key_type, value_type)


def opt_dict_param(
    obj: Any,
    param_name: str,
    key_type: Type = None,
    value_type: Type = None,
    value_class: Type = None,
) -> Dict:
    """Ensures argument obj is either a dictionary or None; if the latter, instantiates an empty
    dictionary.
    """
    from dagster.utils import frozendict

    if obj is not None and not isinstance(obj, (frozendict, dict)):
        raise _param_type_mismatch_exception(obj, (frozendict, dict), param_name)

    if not obj:
        return {}

    if value_class:
        return _check_key_value_types(obj, key_type, value_type=value_class, value_check=issubclass)
    return _check_key_value_types(obj, key_type, value_type)


def opt_nullable_dict_param(
    obj: Any,
    param_name: str,
    key_type: Type = None,
    value_type: Type = None,
    value_class: Type = None,
) -> Optional[Dict]:
    """Ensures argument obj is either a dictionary or None;"""
    from dagster.utils import frozendict

    if obj is not None and not isinstance(obj, (frozendict, dict)):
        raise _param_type_mismatch_exception(obj, (frozendict, dict), param_name)

    if not obj:
        return None if obj is None else {}

    if value_class:
        return _check_key_value_types(obj, key_type, value_type=value_class, value_check=issubclass)
    return _check_key_value_types(obj, key_type, value_type)


def _check_two_dim_key_value_types(
    obj: Any, key_type: Type = None, _param_name: str = None, value_type: Type = None
) -> Dict:
    _check_key_value_types(obj, key_type, dict)  # check level one

    for level_two_dict in obj.values():
        _check_key_value_types(level_two_dict, key_type, value_type)  # check level two

    return obj


def two_dim_dict_param(
    obj: Any, param_name: str, key_type: Type = str, value_type: Type = None
) -> Dict:
    if not isinstance(obj, dict):
        raise _param_type_mismatch_exception(obj, dict, param_name)

    return _check_two_dim_key_value_types(obj, key_type, param_name, value_type)


def opt_two_dim_dict_param(
    obj: Any, param_name: str, key_type: Type = str, value_type: Type = None
) -> Dict:
    if obj is not None and not isinstance(obj, dict):
        raise _param_type_mismatch_exception(obj, dict, param_name)

    if not obj:
        return {}

    return _check_two_dim_key_value_types(obj, key_type, param_name, value_type)


def type_param(obj: Any, param_name: str) -> type:
    if not isinstance(obj, type):
        raise _not_type_param_subclass_mismatch_exception(obj, param_name)
    return obj


def opt_type_param(obj: Any, param_name: str, default: type = None) -> Optional[type]:
    if obj is not None and not isinstance(obj, type):
        raise _not_type_param_subclass_mismatch_exception(obj, param_name)
    return obj if obj is not None else default


def subclass_param(obj: Any, param_name: str, superclass: type) -> type:
    type_param(obj, param_name)
    if not issubclass(obj, superclass):
        raise _param_subclass_mismatch_exception(obj, superclass, param_name)

    return obj


def opt_subclass_param(obj: Any, param_name: str, superclass: type) -> Optional[type]:
    opt_type_param(obj, param_name)
    if obj is not None and not issubclass(obj, superclass):
        raise _param_subclass_mismatch_exception(obj, superclass, param_name)

    return obj


def _element_check_error(key: Any, value: Any, ddict: Dict, ttype: Type) -> ElementCheckError:
    return ElementCheckError(
        "Value {value} from key {key} is not a {ttype}. Dict: {ddict}".format(
            key=key, value=repr(value), ddict=repr(ddict), ttype=repr(ttype)
        )
    )


def generator(obj: Any) -> Generator:
    if not inspect.isgenerator(obj):
        raise ParameterCheckError(
            f"Not a generator (return value of function that yields) Got {obj} instead"
        )
    return obj


def opt_generator(obj: Any) -> Optional[Generator]:
    if obj is not None and not inspect.isgenerator(obj):
        raise ParameterCheckError(
            f"Not a generator (return value of function that yields) Got {obj} instead"
        )
    return obj


def generator_param(obj: Any, param_name: str) -> Generator:
    if not inspect.isgenerator(obj):
        raise ParameterCheckError(
            f'Param "{param_name}" is not a generator (return value of function that yields) Got '
            f"{obj} instead"
        )
    return obj


def opt_generator_param(obj: Any, param_name: str) -> Optional[Generator]:
    if obj is not None and not inspect.isgenerator(obj):
        raise ParameterCheckError(
            f'Param "{param_name}" is not a generator (return value of function that yields) Got '
            f"{obj} instead"
        )
    return obj


def list_elem(ddict: Dict, key: str, of_type: Type = None) -> List:  # type: ignore[return]
    dict_param(ddict, "ddict")
    str_param(key, "key")
    opt_type_param(of_type, "of_type")

    value = ddict.get(key)

    if isinstance(value, list):
        if not of_type:
            return value

        return _check_list_items(value, of_type)

    raise _element_check_error(key, value, ddict, list)


def opt_list_elem(ddict: Dict, key: str, of_type: Type = None) -> List:
    dict_param(ddict, "ddict")
    str_param(key, "key")
    opt_type_param(of_type, "of_type")

    value = ddict.get(key)

    if value is None:
        return []

    if not isinstance(value, list):
        raise _element_check_error(key, value, ddict, list)

    if not of_type:
        return value

    return _check_list_items(value, of_type)


def dict_elem(ddict: Dict, key: str) -> Dict:
    from dagster.utils import frozendict

    dict_param(ddict, "ddict")
    str_param(key, "key")

    if key not in ddict:
        raise CheckError(f"{key} not present in dictionary {ddict}")

    value = ddict[key]
    if not isinstance(value, (frozendict, dict)):
        raise _element_check_error(key, value, ddict, (frozendict, dict))
    return value


def opt_dict_elem(ddict: Dict, key: str) -> Dict:
    from dagster.utils import frozendict

    dict_param(ddict, "ddict")
    str_param(key, "key")

    value = ddict.get(key)

    if value is None:
        return {}

    if not isinstance(value, (frozendict, dict)):
        raise _element_check_error(key, value, ddict, list)

    return value


def bool_elem(ddict: Dict, key: str) -> bool:
    dict_param(ddict, "ddict")
    str_param(key, "key")

    value = ddict[key]
    if not isinstance(value, bool):
        raise _element_check_error(key, value, ddict, bool)
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


def float_elem(ddict: Dict, key: str) -> float:
    dict_param(ddict, "ddict")
    str_param(key, "key")

    value = ddict[key]
    if not isinstance(value, float):
        raise _element_check_error(key, value, ddict, float)
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


def int_elem(ddict: Dict, key: str) -> int:
    dict_param(ddict, "ddict")
    str_param(key, "key")

    value = ddict[key]
    if not isinstance(value, int):
        raise _element_check_error(key, value, ddict, int)
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


def str_elem(ddict: Dict, key: str) -> str:
    dict_param(ddict, "ddict")
    str_param(key, "key")

    value = ddict[key]
    if not isinstance(value, str):
        raise _element_check_error(key, value, ddict, str)
    return value


def class_param(obj: Any, param_name: str) -> Union[ParameterCheckError, type]:
    if not inspect.isclass(obj):
        return ParameterCheckError(
            f'Param "{param_name}" is not a class. Got {repr(obj)} which is type {type(obj)}.'
        )
    return obj
