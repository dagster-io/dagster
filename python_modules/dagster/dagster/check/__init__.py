from future.utils import raise_with_traceback
from six import string_types


class CheckError(Exception):
    pass


class ParameterCheckError(CheckError):
    pass


class ElementCheckError(CheckError):
    pass


class NotImplementedCheckError(CheckError):
    pass


def _param_type_mismatch_exception(obj, ttype, param_name):
    return ParameterCheckError(
        'Param "{name}" is not a {type}. Got {obj} with is type {obj_type}.'.format(
            name=param_name, obj=repr(obj), type=ttype.__name__, obj_type=type(obj)
        )
    )


def _type_mismatch_error(obj, ttype, desc):
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
    if not _is_str(desc):
        raise_with_traceback(CheckError('desc argument must be a string'))

    raise_with_traceback(CheckError('Failure condition: {desc}'.format(desc=desc)))


def not_implemented(desc):
    if not _is_str(desc):
        raise_with_traceback(CheckError('desc argument must be a string'))

    raise_with_traceback(NotImplementedCheckError('Not implemented: {desc}'.format(desc=desc)))


def inst(obj, ttype, desc=None):
    if not isinstance(obj, ttype):
        raise_with_traceback(_type_mismatch_error(obj, ttype, desc))
    return obj


def is_callable(obj, desc=None):
    if not callable(obj):
        if desc:
            raise_with_traceback(
                CheckError(
                    'Must be callable. Got {obj}. Description: {desc}'.format(
                        obj=repr(obj),
                        desc=desc,
                    )
                )
            )
        else:
            raise_with_traceback(
                CheckError(
                    'Must be callable. Got {obj}. Description: {desc}'.format(
                        obj=obj,
                        desc=desc,
                    )
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
    if not isinstance(condition, bool):
        raise_with_traceback(CheckError('Invariant condition must be boolean'))

    if not condition:
        if desc:
            raise_with_traceback(
                CheckError('Invariant failed. Description: {desc}'.format(desc=desc))
            )
        else:
            raise_with_traceback(CheckError('Invariant failed.'))

    return True


def param_invariant(condition, param_name, desc=None):
    if not isinstance(condition, bool):
        raise_with_traceback(ParameterCheckError('Invariant condition must be boolean'))

    if not condition:
        raise_with_traceback(_param_invariant_exception(param_name, desc))


def inst_param(obj, param_name, ttype):
    if not isinstance(obj, ttype):
        raise_with_traceback(_param_type_mismatch_exception(obj, ttype, param_name))
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
    if not isinstance(obj, int):
        raise_with_traceback(_param_type_mismatch_exception(obj, int, param_name))
    return obj


def opt_int_param(obj, param_name):
    if obj is not None and not isinstance(obj, int):
        raise_with_traceback(_param_type_mismatch_exception(obj, int, param_name))
    return obj


def _is_str(obj):
    return isinstance(obj, string_types)


def str_param(obj, param_name):
    if not _is_str(obj):
        raise_with_traceback(_param_type_mismatch_exception(obj, str, param_name))
    return obj


def opt_str_param(obj, param_name, default=None):
    if obj is not None and not isinstance(obj, string_types):
        raise_with_traceback(_param_type_mismatch_exception(obj, str, param_name))
    return default if obj is None else obj


def bool_param(obj, param_name):
    if not isinstance(obj, bool):
        raise_with_traceback(_param_type_mismatch_exception(obj, bool, param_name))
    return obj


def opt_bool_param(obj, param_name, default=None):
    if obj is not None and not isinstance(obj, bool):
        raise_with_traceback(_param_type_mismatch_exception(obj, bool, param_name))
    return default if obj is None else obj


def list_param(obj_list, param_name, of_type=None):
    if not isinstance(obj_list, list):
        raise_with_traceback(_param_type_mismatch_exception(obj_list, list, param_name))

    if not of_type:
        return obj_list

    return _check_list_items(obj_list, of_type)


def tuple_param(obj, param_name):
    if not isinstance(obj, tuple):
        raise_with_traceback(_param_type_mismatch_exception(obj, tuple, param_name))
    return obj


def opt_tuple_param(obj, param_name, default=None):
    if obj is not None and not isinstance(obj, tuple):
        raise_with_traceback(_param_type_mismatch_exception(obj, tuple, param_name))
    return default if obj is None else obj


def _check_list_items(obj_list, of_type):
    for obj in obj_list:

        if of_type is str:
            key_type = string_types

        if not isinstance(obj, of_type):
            raise_with_traceback(
                CheckError(
                    'Member of list mismatches type. Expected {of_type}. Got {obj_repr}'.format(
                        of_type=of_type,
                        obj_repr=repr(obj),
                    )
                )
            )
    return obj_list


def opt_list_param(obj_list, param_name, of_type=None):
    if obj_list is not None and not isinstance(obj_list, list):
        raise_with_traceback(_param_type_mismatch_exception(obj_list, list, param_name))
    if not obj_list:
        return []
    if not of_type:
        return obj_list

    return _check_list_items(obj_list, of_type)


def dict_param(obj, param_name, key_type=None, value_type=None):
    if not isinstance(obj, dict):
        raise_with_traceback(_param_type_mismatch_exception(obj, dict, param_name))

    if not (key_type or value_type):
        return obj

    return _check_key_value_types(obj, key_type, value_type)


def type_param(obj, param_name):
    if not isinstance(obj, type):
        raise_with_traceback(_param_type_mismatch_exception(obj, type, param_name))
    return obj


def _check_key_value_types(obj, key_type, value_type):
    if key_type is str:
        key_type = string_types

    if value_type is str:
        value_type = string_types

    for key, value in obj.items():
        if key_type and not isinstance(key, key_type):
            raise_with_traceback(
                CheckError(
                    'Key in dictionary mismatches type. Expected {key_type}. Got {obj_repr}'.format(
                        key_type=repr(key_type),
                        obj_repr=repr(key),
                    )
                )
            )
        if value_type and not isinstance(value, value_type):
            raise_with_traceback(
                CheckError(
                    'Value in dictionary mismatches type. Expected {vtype}. Got {obj_repr}'.format(
                        vtype=repr(value_type),
                        obj_repr=repr(value),
                    )
                )
            )
    return obj


def opt_dict_param(obj, param_name, key_type=None, value_type=None):
    if obj is not None and not isinstance(obj, dict):
        raise_with_traceback(_param_type_mismatch_exception(obj, dict, param_name))

    if not obj:
        return {}

    return _check_key_value_types(obj, key_type, value_type)


def _element_check_error(key, value, ddict, ttype):
    return ElementCheckError(
        'Value {value} from key {key} is not a {ttype}. Dict: {ddict}'.format(
            key=key, value=repr(value), ddict=repr(ddict), ttype=repr(ttype)
        )
    )


def list_elem(ddict, key):
    dict_param(ddict, 'ddict')
    str_param(key, 'key')

    value = ddict[key]
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
    dict_param(ddict, 'ddict')
    str_param(key, 'key')

    if key not in ddict:
        raise_with_traceback(
            CheckError('{key} not present in dictionary {ddict}'.format(key=key, ddict=ddict))
        )

    value = ddict[key]
    if not isinstance(value, dict):
        raise_with_traceback(_element_check_error(key, value, ddict, dict))
    return value


def opt_dict_elem(ddict, key):
    dict_param(ddict, 'ddict')
    str_param(key, 'key')

    value = ddict.get(key)

    if value is None:
        return {}

    if not isinstance(value, dict):
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
    if not _is_str(value):
        raise_with_traceback(_element_check_error(key, value, ddict, str))
    return value


def str_elem(ddict, key):
    dict_param(ddict, 'ddict')
    str_param(key, 'key')

    value = ddict[key]
    if not _is_str(value):
        raise_with_traceback(_element_check_error(key, value, ddict, str))
    return value
