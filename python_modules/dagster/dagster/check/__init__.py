import inspect
import sys

from future.utils import raise_with_traceback
from six import integer_types, string_types

if sys.version_info[0] >= 3:
    type_types = type
else:
    # These shenanigans are to support old-style classes in py27
    import new  # pylint: disable=import-error

    type_types = (type, new.classobj)  # pylint: disable=undefined-variable


class CheckError(Exception):
    pass


class ParameterCheckError(CheckError):
    pass


class ElementCheckError(CheckError):
    pass


class NotImplementedCheckError(CheckError):
    pass


def _param_type_mismatch_exception(obj, ttype, param_name, additional_message=None):
    if isinstance(ttype, tuple):
        type_names = sorted([t.__name__ for t in ttype])
        return ParameterCheckError(
            'Param "{name}" is not one of {type_names}. Got {obj} which is type {obj_type}.'
            '{additional_message}'.format(
                name=param_name,
                obj=repr(obj),
                type_names=type_names,
                obj_type=type(obj),
                additional_message=' ' + additional_message if additional_message else '',
            )
        )
    else:
        return ParameterCheckError(
            'Param "{name}" is not a {type}. Got {obj} which is type {obj_type}.'
            '{additional_message}'.format(
                name=param_name,
                obj=repr(obj),
                type=ttype.__name__,
                obj_type=type(obj),
                additional_message=' ' + additional_message if additional_message else '',
            )
        )


def _not_type_param_subclass_mismatch_exception(obj, param_name):
    return ParameterCheckError(
        'Param "{name}" was supposed to be a type. Got {obj} instead of type {obj_type}'.format(
            name=param_name, obj=repr(obj), obj_type=type(obj)
        )
    )


def _param_subclass_mismatch_exception(obj, superclass, param_name):
    return ParameterCheckError(
        'Param "{name}" is a type but not a subclass of {superclass}. Got {obj} instead'.format(
            name=param_name, superclass=superclass, obj=obj
        )
    )


def _type_mismatch_error(obj, ttype, desc=None):
    if desc:
        return CheckError(
            'Object {obj} is not a {type}. Got {obj} with type {obj_type}. Desc: {desc}'.format(
                obj=repr(obj), type=ttype.__name__, obj_type=type(obj), desc=desc
            )
        )
    else:
        return CheckError(
            'Object {obj} is not a {type}. Got {obj} with type {obj_type}.'.format(
                obj=repr(obj), type=ttype.__name__, obj_type=type(obj)
            )
        )


def _not_callable_exception(obj, param_name):
    return ParameterCheckError(
        'Param "{name}" is not callable. Got {obj} with type {obj_type}.'.format(
            name=param_name, obj=repr(obj), obj_type=type(obj)
        )
    )


def _param_invariant_exception(param_name, desc):
    return ParameterCheckError(
        'Invariant violation for parameter {param_name}. Description: {desc}'.format(
            param_name=param_name, desc=desc
        )
    )


def failed(desc):
    if not is_str(desc):
        raise_with_traceback(CheckError('desc argument must be a string'))

    raise_with_traceback(CheckError('Failure condition: {desc}'.format(desc=desc)))


def not_implemented(desc):
    if not is_str(desc):
        raise_with_traceback(CheckError('desc argument must be a string'))

    raise_with_traceback(NotImplementedCheckError('Not implemented: {desc}'.format(desc=desc)))


def inst(obj, ttype, desc=None):
    if not isinstance(obj, ttype):
        raise_with_traceback(_type_mismatch_error(obj, ttype, desc))
    return obj


def subclass(obj, superclass, desc=None):
    if not issubclass(obj, superclass):
        raise_with_traceback(_type_mismatch_error(obj, superclass, desc))

    return obj


def is_callable(obj, desc=None):
    if not callable(obj):
        if desc:
            raise_with_traceback(
                CheckError(
                    'Must be callable. Got {obj}. Description: {desc}'.format(
                        obj=repr(obj), desc=desc
                    )
                )
            )
        else:
            raise_with_traceback(
                CheckError(
                    'Must be callable. Got {obj}. Description: {desc}'.format(obj=obj, desc=desc)
                )
            )

    return obj


def not_none_param(obj, param_name):
    if obj is None:
        raise_with_traceback(
            _param_invariant_exception(
                param_name, 'Param {param_name} cannot be none'.format(param_name=param_name)
            )
        )
    return obj


def invariant(condition, desc=None):
    if not condition:
        if desc:
            raise_with_traceback(
                CheckError('Invariant failed. Description: {desc}'.format(desc=desc))
            )
        else:
            raise_with_traceback(CheckError('Invariant failed.'))

    return True


def param_invariant(condition, param_name, desc=None):
    if not condition:
        raise_with_traceback(_param_invariant_exception(param_name, desc))


def inst_param(obj, param_name, ttype, additional_message=None):
    if not isinstance(obj, ttype):
        raise_with_traceback(
            _param_type_mismatch_exception(
                obj, ttype, param_name, additional_message=additional_message
            )
        )
    return obj


def opt_inst_param(obj, param_name, ttype, default=None):
    if obj is not None and not isinstance(obj, ttype):
        raise_with_traceback(_param_type_mismatch_exception(obj, ttype, param_name))
    return default if obj is None else obj


def callable_param(obj, param_name):
    if not callable(obj):
        raise_with_traceback(_not_callable_exception(obj, param_name))
    return obj


def opt_callable_param(obj, param_name, default=None):
    if obj is not None and not callable(obj):
        raise_with_traceback(_not_callable_exception(obj, param_name))
    return default if obj is None else obj


def int_param(obj, param_name):
    if not isinstance(obj, integer_types):
        raise_with_traceback(_param_type_mismatch_exception(obj, int, param_name))
    return obj


def int_value_param(obj, value, param_name):
    if not isinstance(obj, integer_types):
        raise_with_traceback(_param_type_mismatch_exception(obj, int, param_name))
    if obj != value:
        raise_with_traceback(
            _param_invariant_exception(param_name, "Should be equal to {value}".format(value=value))
        )
    return obj


def opt_int_param(obj, param_name):
    if obj is not None and not isinstance(obj, integer_types):
        raise_with_traceback(_param_type_mismatch_exception(obj, int, param_name))
    return obj


def float_param(obj, param_name):
    if not isinstance(obj, float):
        raise_with_traceback(_param_type_mismatch_exception(obj, float, param_name))
    return obj


def opt_numeric_param(obj, param_name):
    if obj is not None and not isinstance(obj, (int, float)):
        raise_with_traceback(_param_type_mismatch_exception(obj, (int, float), param_name))
    return obj


def numeric_param(obj, param_name):
    if not isinstance(obj, (int, float)):
        raise_with_traceback(_param_type_mismatch_exception(obj, (int, float), param_name))
    return obj


def opt_float_param(obj, param_name):
    if obj is not None and not isinstance(obj, float):
        raise_with_traceback(_param_type_mismatch_exception(obj, float, param_name))
    return obj


def is_str(obj):
    return isinstance(obj, string_types)


def str_param(obj, param_name):
    if not is_str(obj):
        raise_with_traceback(_param_type_mismatch_exception(obj, str, param_name))
    return obj


def opt_str_param(obj, param_name, default=None):
    if obj is not None and not isinstance(obj, string_types):
        raise_with_traceback(_param_type_mismatch_exception(obj, str, param_name))
    return default if obj is None else obj


def opt_nonempty_str_param(obj, param_name, default=None):
    if obj is not None and not isinstance(obj, string_types):
        raise_with_traceback(_param_type_mismatch_exception(obj, str, param_name))
    return default if obj is None or obj == '' else obj


def bool_param(obj, param_name):
    if not isinstance(obj, bool):
        raise_with_traceback(_param_type_mismatch_exception(obj, bool, param_name))
    return obj


def opt_bool_param(obj, param_name, default=None):
    if obj is not None and not isinstance(obj, bool):
        raise_with_traceback(_param_type_mismatch_exception(obj, bool, param_name))
    return default if obj is None else obj


def is_list(obj_list, of_type=None, desc=None):
    if not isinstance(obj_list, list):
        raise_with_traceback(_type_mismatch_error(obj_list, list, desc))

    if not of_type:
        return obj_list

    return _check_list_items(obj_list, of_type)


def list_param(obj_list, param_name, of_type=None):
    from dagster.utils import frozenlist

    if not isinstance(obj_list, (frozenlist, list)):
        raise_with_traceback(
            _param_type_mismatch_exception(obj_list, (frozenlist, list), param_name)
        )

    if not of_type:
        return obj_list

    return _check_list_items(obj_list, of_type)


def set_param(obj_set, param_name, of_type=None):
    if not isinstance(obj_set, (frozenset, set)):
        raise_with_traceback(_param_type_mismatch_exception(obj_set, (frozenset, set), param_name))

    if not of_type:
        return obj_set

    return _check_set_items(obj_set, of_type)


def tuple_param(obj, param_name):
    if not isinstance(obj, tuple):
        raise_with_traceback(_param_type_mismatch_exception(obj, tuple, param_name))
    return obj


def matrix_param(matrix, param_name, of_type=None):
    matrix = list_param(matrix, param_name, of_type=list)
    if not matrix:
        raise_with_traceback(CheckError('You must pass a list of lists. Received an empty list.'))
    for sublist in matrix:
        sublist = list_param(sublist, 'sublist_{}'.format(param_name), of_type=of_type)
        if len(sublist) != len(matrix[0]):
            raise_with_traceback(CheckError('All sublists in matrix must have the same length'))
    return matrix


def opt_tuple_param(obj, param_name, default=None):
    if obj is not None and not isinstance(obj, tuple):
        raise_with_traceback(_param_type_mismatch_exception(obj, tuple, param_name))
    return default if obj is None else obj


def _check_list_items(obj_list, of_type):
    if of_type is str:
        of_type = string_types

    for obj in obj_list:

        if not isinstance(obj, of_type):
            if isinstance(obj, type):
                additional_message = (
                    ' Did you pass a class where you were expecting an instance of the class?'
                )
            else:
                additional_message = ''
            raise_with_traceback(
                CheckError(
                    'Member of list mismatches type. Expected {of_type}. Got {obj_repr} of type '
                    '{obj_type}.{additional_message}'.format(
                        of_type=of_type,
                        obj_repr=repr(obj),
                        obj_type=type(obj),
                        additional_message=additional_message,
                    )
                )
            )
    return obj_list


def _check_set_items(obj_set, of_type):
    if of_type is str:
        of_type = string_types

    for obj in obj_set:

        if not isinstance(obj, of_type):
            if isinstance(obj, type):
                additional_message = (
                    ' Did you pass a class where you were expecting an instance of the class?'
                )
            else:
                additional_message = ''
            raise_with_traceback(
                CheckError(
                    'Member of set mismatches type. Expected {of_type}. Got {obj_repr} of type '
                    '{obj_type}.{additional_message}'.format(
                        of_type=of_type,
                        obj_repr=repr(obj),
                        obj_type=type(obj),
                        additional_message=additional_message,
                    )
                )
            )
    return obj_set


def opt_list_param(obj_list, param_name, of_type=None):
    '''Ensures argument obj_list is a list or None; in the latter case, instantiates an empty list
    and returns it.

    If the of_type argument is provided, also ensures that list items conform to the type specified
    by of_type.
    '''
    from dagster.utils import frozenlist

    if obj_list is not None and not isinstance(obj_list, (frozenlist, list)):
        raise_with_traceback(
            _param_type_mismatch_exception(obj_list, (frozenlist, list), param_name)
        )
    if not obj_list:
        return []
    if not of_type:
        return obj_list

    return _check_list_items(obj_list, of_type)


def opt_set_param(obj_set, param_name, of_type=None):
    '''Ensures argument obj_set is a set or None; in the latter case, instantiates an empty set
    and returns it.

    If the of_type argument is provided, also ensures that list items conform to the type specified
    by of_type.
    '''
    if obj_set is not None and not isinstance(obj_set, (frozenset, set)):
        raise_with_traceback(_param_type_mismatch_exception(obj_set, (frozenset, set), param_name))
    if not obj_set:
        return set()
    if not of_type:
        return obj_set

    return _check_set_items(obj_set, of_type)


def opt_nullable_list_param(obj_list, param_name, of_type=None):
    '''Ensures argument obj_list is a list or None. Returns None if input is None.

    If the of_type argument is provided, also ensures that list items conform to the type specified
    by of_type.
    '''
    from dagster.utils import frozenlist

    if obj_list is not None and not isinstance(obj_list, (frozenlist, list)):
        raise_with_traceback(
            _param_type_mismatch_exception(obj_list, (frozenlist, list), param_name)
        )
    if not obj_list:
        return None if obj_list is None else []
    if not of_type:
        return obj_list

    return _check_list_items(obj_list, of_type)


def _check_key_value_types(obj, key_type, value_type, key_check=isinstance, value_check=isinstance):
    '''Ensures argument obj is a dictionary, and enforces that the keys/values conform to the types
    specified by key_type, value_type.
    '''
    if not isinstance(obj, dict):
        raise_with_traceback(_type_mismatch_error(obj, dict))

    if key_type is str:
        key_type = string_types

    if value_type is str:
        value_type = string_types

    for key, value in obj.items():
        if key_type and not key_check(key, key_type):
            raise_with_traceback(
                CheckError(
                    'Key in dictionary mismatches type. Expected {key_type}. Got {obj_repr}'.format(
                        key_type=repr(key_type), obj_repr=repr(key)
                    )
                )
            )
        if value_type and not value_check(value, value_type):
            raise_with_traceback(
                CheckError(
                    'Value in dictionary mismatches expected type for key {key}. Expected value '
                    'of type {vtype}. Got value {value} of type {obj_type}.'.format(
                        vtype=repr(value_type), obj_type=type(value), key=key, value=value
                    )
                )
            )
    return obj


def dict_param(obj, param_name, key_type=None, value_type=None):
    '''Ensures argument obj is a native Python dictionary, raises an exception if not, and otherwise
    returns obj.
    '''
    from dagster.utils import frozendict

    if not isinstance(obj, (frozendict, dict)):
        raise_with_traceback(_param_type_mismatch_exception(obj, (frozendict, dict), param_name))

    if not (key_type or value_type):
        return obj

    return _check_key_value_types(obj, key_type, value_type)


def opt_dict_param(obj, param_name, key_type=None, value_type=None, value_class=None):
    '''Ensures argument obj is either a dictionary or None; if the latter, instantiates an empty
    dictionary.
    '''
    from dagster.utils import frozendict

    if obj is not None and not isinstance(obj, (frozendict, dict)):
        raise_with_traceback(_param_type_mismatch_exception(obj, (frozendict, dict), param_name))

    if not obj:
        return {}

    if value_class:
        return _check_key_value_types(obj, key_type, value_type=value_class, value_check=issubclass)
    return _check_key_value_types(obj, key_type, value_type)


def opt_nullable_dict_param(obj, param_name, key_type=None, value_type=None, value_class=None):
    '''Ensures argument obj is either a dictionary or None;
    '''
    from dagster.utils import frozendict

    if obj is not None and not isinstance(obj, (frozendict, dict)):
        raise_with_traceback(_param_type_mismatch_exception(obj, (frozendict, dict), param_name))

    if not obj:
        return None if obj is None else {}

    if value_class:
        return _check_key_value_types(obj, key_type, value_type=value_class, value_check=issubclass)
    return _check_key_value_types(obj, key_type, value_type)


def _check_two_dim_key_value_types(obj, key_type, _param_name, value_type):
    _check_key_value_types(obj, key_type, dict)  # check level one

    for level_two_dict in obj.values():
        _check_key_value_types(level_two_dict, key_type, value_type)  # check level two

    return obj


def two_dim_dict_param(obj, param_name, key_type=string_types, value_type=None):
    if not isinstance(obj, dict):
        raise_with_traceback(_param_type_mismatch_exception(obj, dict, param_name))

    return _check_two_dim_key_value_types(obj, key_type, param_name, value_type)


def opt_two_dim_dict_param(obj, param_name, key_type=string_types, value_type=None):
    if obj is not None and not isinstance(obj, dict):
        raise_with_traceback(_param_type_mismatch_exception(obj, dict, param_name))

    if not obj:
        return {}

    return _check_two_dim_key_value_types(obj, key_type, param_name, value_type)


def type_param(obj, param_name):
    if not isinstance(obj, type_types):
        raise_with_traceback(_not_type_param_subclass_mismatch_exception(obj, param_name))
    return obj


def opt_type_param(obj, param_name, default=None):
    if obj is not None and not isinstance(obj, type):
        raise_with_traceback(_not_type_param_subclass_mismatch_exception(obj, param_name))
    return obj if obj is not None else default


def subclass_param(obj, param_name, superclass):
    type_param(obj, param_name)
    if not issubclass(obj, superclass):
        raise_with_traceback(_param_subclass_mismatch_exception(obj, superclass, param_name))

    return obj


def opt_subclass_param(obj, param_name, superclass):
    opt_type_param(obj, param_name)
    if obj is not None and not issubclass(obj, superclass):
        raise_with_traceback(_param_subclass_mismatch_exception(obj, superclass, param_name))

    return obj


def _element_check_error(key, value, ddict, ttype):
    return ElementCheckError(
        'Value {value} from key {key} is not a {ttype}. Dict: {ddict}'.format(
            key=key, value=repr(value), ddict=repr(ddict), ttype=repr(ttype)
        )
    )


def generator(obj):
    if not inspect.isgenerator(obj):
        raise ParameterCheckError(
            'Not a generator (return value of function that yields) Got {obj} instead'.format(
                obj=obj
            )
        )
    return obj


def opt_generator(obj):
    if obj is not None and not inspect.isgenerator(obj):
        raise ParameterCheckError(
            'Not a generator (return value of function that yields) Got {obj} instead'.format(
                obj=obj
            )
        )
    return obj


def generator_param(obj, param_name):
    if not inspect.isgenerator(obj):
        raise ParameterCheckError(
            (
                'Param "{name}" is not a generator (return value of function that yields) Got '
                '{obj} instead'
            ).format(name=param_name, obj=obj)
        )
    return obj


def opt_generator_param(obj, param_name):
    if obj is not None and not inspect.isgenerator(obj):
        raise ParameterCheckError(
            (
                'Param "{name}" is not a generator (return value of function that yields) Got '
                '{obj} instead'
            ).format(name=param_name, obj=obj)
        )
    return obj


def list_elem(ddict, key):
    dict_param(ddict, 'ddict')
    str_param(key, 'key')

    value = ddict.get(key)
    if not isinstance(value, list):
        raise_with_traceback(_element_check_error(key, value, ddict, list))
    return value


def opt_list_elem(ddict, key):
    dict_param(ddict, 'ddict')
    str_param(key, 'key')

    value = ddict.get(key)

    if value is None:
        return []

    if not isinstance(value, list):
        raise_with_traceback(_element_check_error(key, value, ddict, list))
    return value


def dict_elem(ddict, key):
    from dagster.utils import frozendict

    dict_param(ddict, 'ddict')
    str_param(key, 'key')

    if key not in ddict:
        raise_with_traceback(
            CheckError('{key} not present in dictionary {ddict}'.format(key=key, ddict=ddict))
        )

    value = ddict[key]
    if not isinstance(value, (frozendict, dict)):
        raise_with_traceback(_element_check_error(key, value, ddict, (frozendict, dict)))
    return value


def opt_dict_elem(ddict, key):
    from dagster.utils import frozendict

    dict_param(ddict, 'ddict')
    str_param(key, 'key')

    value = ddict.get(key)

    if value is None:
        return {}

    if not isinstance(value, (frozendict, dict)):
        raise_with_traceback(_element_check_error(key, value, ddict, list))

    return value


def bool_elem(ddict, key):
    dict_param(ddict, 'ddict')
    str_param(key, 'key')

    value = ddict[key]
    if not isinstance(value, bool):
        raise_with_traceback(_element_check_error(key, value, ddict, bool))
    return value


def opt_str_elem(ddict, key):
    dict_param(ddict, 'ddict')
    str_param(key, 'key')

    value = ddict.get(key)
    if value is None:
        return None
    if not is_str(value):
        raise_with_traceback(_element_check_error(key, value, ddict, str))
    return value


def str_elem(ddict, key):
    dict_param(ddict, 'ddict')
    str_param(key, 'key')

    value = ddict[key]
    if not is_str(value):
        raise_with_traceback(_element_check_error(key, value, ddict, str))
    return value
