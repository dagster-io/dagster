import typing

from dagster import check
from dagster.core.errors import DagsterInvalidDefinitionError
from dagster.utils.typing_api import (
    get_dict_key_value_types,
    get_list_inner_type,
    get_optional_inner_type,
    get_set_inner_type,
    get_tuple_type_params,
    is_closed_python_dict_type,
    is_closed_python_list_type,
    is_closed_python_optional_type,
    is_closed_python_set_type,
    is_closed_python_tuple_type,
)

from .builtin_enum import BuiltinEnum


def transform_typing_type(type_annotation):
    from dagster.core.types.runtime.runtime_type import List
    from dagster.core.types.runtime.python_dict import create_typed_runtime_dict
    from dagster.core.types.runtime.python_set import Set
    from dagster.core.types.runtime.python_tuple import Tuple, create_typed_tuple

    if type_annotation is typing.List:
        return List
    elif type_annotation is typing.Set:
        return Set
    elif type_annotation is typing.Tuple:
        return Tuple
    elif type_annotation is typing.Dict:
        return Dict
    elif is_closed_python_list_type(type_annotation):
        return List[transform_typing_type(get_list_inner_type(type_annotation))]
    elif is_closed_python_set_type(type_annotation):
        return Set[transform_typing_type(get_set_inner_type(type_annotation))]
    elif is_closed_python_tuple_type(type_annotation):
        transformed_types = [
            transform_typing_type(tt) for tt in get_tuple_type_params(type_annotation)
        ]
        return create_typed_tuple(*transformed_types)
    elif is_closed_python_optional_type(type_annotation):
        return WrappingNullableType(transform_typing_type(get_optional_inner_type(type_annotation)))
    elif is_closed_python_dict_type(type_annotation):
        key_type, value_type = get_dict_key_value_types(type_annotation)
        return create_typed_runtime_dict(
            transform_typing_type(key_type), transform_typing_type(value_type)
        )
    else:
        return type_annotation


class WrappingType(object):
    def __init__(self, inner_type):
        # Cannot check inner_type because of circular references and no fwd declarations
        if inner_type == BuiltinEnum.NOTHING:
            raise DagsterInvalidDefinitionError(
                'Type Nothing can not be wrapped in List or Optional'
            )

        self.inner_type = inner_type


class WrappingNullableType(WrappingType):
    pass


class DagsterOptionalApi:
    def __getitem__(self, inner_type):
        check.not_none_param(inner_type, 'inner_type')
        return WrappingNullableType(inner_type)


class DagsterDictApi(object):
    def __call__(self, fields):
        from dagster.core.types.config.field_utils import build_config_dict

        return build_config_dict(fields)

    def __getitem__(self, *args):
        from dagster.core.types.runtime.python_dict import create_typed_runtime_dict

        check.param_invariant(len(args[0]) == 2, 'args', 'Must be two parameters')
        return create_typed_runtime_dict(args[0][0], args[0][1])


Optional = DagsterOptionalApi()

Dict = DagsterDictApi()
