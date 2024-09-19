import typing

from dagster._core.types.dagster_type import List, Optional
from dagster._core.types.python_dict import Dict, create_typed_runtime_dict
from dagster._core.types.python_set import Set
from dagster._core.types.python_tuple import Tuple, create_typed_tuple
from dagster._utils.typing_api import (
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


def transform_typing_type(type_annotation):
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
        return Optional[transform_typing_type(get_optional_inner_type(type_annotation))]
    elif is_closed_python_dict_type(type_annotation):
        key_type, value_type = get_dict_key_value_types(type_annotation)
        return create_typed_runtime_dict(
            transform_typing_type(key_type), transform_typing_type(value_type)
        )
    else:
        return type_annotation
