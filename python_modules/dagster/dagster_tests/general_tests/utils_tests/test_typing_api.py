# ruff: noqa: UP006

import typing

from dagster._utils.typing_api import (
    flatten_unions,
    get_mapping_key_value_types,
    get_optional_inner_type,
    get_sequence_inner_type,
    is_closed_python_dict_type,
    is_closed_python_list_type,
    is_closed_python_mapping_type,
    is_closed_python_optional_type,
    is_closed_python_sequence_type,
    is_closed_python_set_type,
    is_closed_python_tuple_type,
    is_typing_type,
)


def test_closed_python_dict():
    assert is_closed_python_dict_type(typing.Dict[str, int]) is True

    # Documenting current behavior -- it seems possible that this is not intended
    assert is_closed_python_dict_type(typing.Dict[str, typing.Tuple]) is True
    assert is_closed_python_dict_type(typing.Dict[str, typing.List]) is True
    assert is_closed_python_dict_type(typing.Dict[str, typing.Dict]) is True
    assert is_closed_python_dict_type(typing.Dict[str, typing.Dict[str, typing.Dict]]) is True
    assert is_closed_python_dict_type(typing.Dict[str, typing.Dict | None]) is True

    assert is_closed_python_dict_type(dict) is False
    assert is_closed_python_dict_type(typing.Dict) is False
    assert is_closed_python_dict_type(None) is False
    assert is_closed_python_dict_type(1) is False
    assert is_closed_python_dict_type("foobar") is False
    assert is_closed_python_dict_type(typing.Optional) is False
    assert is_closed_python_dict_type(typing.List) is False


def test_is_typing_optional_py_3():
    assert is_closed_python_optional_type(typing.Optional[int])  # noqa: UP045
    assert not is_closed_python_optional_type(typing.Optional)
    assert not is_closed_python_optional_type(None)
    assert not is_closed_python_optional_type(int)
    assert not is_closed_python_optional_type(list)
    assert not is_closed_python_optional_type("foobar")


def test_get_inner_optional_py_3():
    assert get_optional_inner_type(typing.Optional[int]) is int  # noqa: UP045


def test_closed_tuple_type():
    assert is_closed_python_tuple_type(typing.Tuple[int, str]) is True

    # Documenting current behavior -- it seems possible that this is not intended
    assert is_closed_python_tuple_type(typing.Tuple[str, typing.Tuple]) is True
    assert is_closed_python_tuple_type(typing.Tuple[str, typing.List]) is True
    assert is_closed_python_tuple_type(typing.Tuple[str, typing.Dict]) is True
    assert is_closed_python_tuple_type(typing.Tuple[str, typing.Dict[str, typing.Dict]]) is True
    assert is_closed_python_tuple_type(typing.Tuple[str, typing.Dict | None]) is True

    assert is_closed_python_tuple_type(tuple) is False
    assert is_closed_python_tuple_type(typing.Tuple) is False
    assert is_closed_python_tuple_type(1) is False
    assert is_closed_python_tuple_type("foobar") is False
    assert is_closed_python_tuple_type(typing.Optional) is False
    assert is_closed_python_tuple_type(typing.List) is False


def test_closed_set_type():
    assert is_closed_python_set_type(typing.Set[int]) is True
    assert is_closed_python_set_type(set) is False
    assert is_closed_python_set_type(typing.Set) is False
    assert is_closed_python_set_type(1) is False
    assert is_closed_python_set_type("foobar") is False
    assert is_closed_python_set_type(typing.Optional) is False
    assert is_closed_python_set_type(typing.List) is False
    assert is_closed_python_set_type(typing.Dict) is False
    assert is_closed_python_set_type(typing.Dict[int, str]) is False
    assert is_closed_python_set_type(typing.Tuple) is False
    assert is_closed_python_set_type(typing.Tuple[int, str]) is False

    # Documenting current behavior -- it seems possible that this is not intended
    assert is_closed_python_set_type(typing.Set[typing.Tuple]) is True
    assert is_closed_python_set_type(typing.Set[typing.List]) is True
    assert is_closed_python_set_type(typing.Set[typing.Dict]) is True
    assert is_closed_python_set_type(typing.Set[typing.Dict[str, typing.Dict]]) is True
    assert is_closed_python_set_type(typing.Set[typing.Dict | None]) is True


def test_closed_list_type():
    assert is_closed_python_list_type(typing.List[int]) is True

    assert is_closed_python_list_type(typing.List) is False
    assert is_closed_python_list_type(list) is False
    assert is_closed_python_list_type(None) is False
    assert is_closed_python_list_type(1) is False
    assert is_closed_python_list_type("foobar") is False
    assert is_closed_python_list_type(typing.Optional) is False
    assert is_closed_python_list_type(typing.Dict) is False
    assert is_closed_python_list_type(typing.Dict[int, str]) is False
    assert is_closed_python_list_type(typing.Tuple) is False
    assert is_closed_python_list_type(typing.Tuple[int, str]) is False


def test_closed_mapping_type():
    assert is_closed_python_mapping_type(typing.Mapping[str, typing.Any]) is True
    assert is_closed_python_mapping_type(typing.Mapping[str, int]) is True

    assert is_closed_python_mapping_type(typing.Mapping) is False
    assert is_closed_python_mapping_type(dict) is False
    assert is_closed_python_mapping_type(typing.Dict[str, int]) is False
    assert is_closed_python_mapping_type(None) is False
    assert is_closed_python_mapping_type(1) is False


def test_closed_sequence_type():
    assert is_closed_python_sequence_type(typing.Sequence[int]) is True
    assert is_closed_python_sequence_type(typing.Sequence[str]) is True

    assert is_closed_python_sequence_type(typing.Sequence) is False
    assert is_closed_python_sequence_type(list) is False
    assert is_closed_python_sequence_type(typing.List[int]) is False
    assert is_closed_python_sequence_type(None) is False
    assert is_closed_python_sequence_type(1) is False


def test_get_mapping_key_value_types():
    assert get_mapping_key_value_types(typing.Mapping[str, typing.Any]) == (str, typing.Any)
    assert get_mapping_key_value_types(typing.Mapping[str, int]) == (str, int)


def test_get_sequence_inner_type():
    assert get_sequence_inner_type(typing.Sequence[int]) is int
    assert get_sequence_inner_type(typing.Sequence[str]) is str


def test_is_typing_type():
    assert is_typing_type("foobar") is False
    assert is_typing_type(1) is False
    assert is_typing_type(dict) is False
    assert is_typing_type(int) is False
    assert is_typing_type(list) is False
    assert is_typing_type(None) is False
    assert is_typing_type(set) is False
    assert is_typing_type(tuple) is False
    assert is_typing_type(typing.Dict) is True
    assert is_typing_type(typing.Dict[int, str]) is True
    assert is_typing_type(typing.Dict[str, typing.Dict[str, typing.Dict]]) is True
    assert is_typing_type(typing.Dict[str, typing.Dict]) is True
    assert is_typing_type(typing.Dict[str, typing.List]) is True
    assert is_typing_type(typing.Dict[str, typing.Dict | None]) is True
    assert is_typing_type(typing.Dict[str, typing.Tuple]) is True
    assert is_typing_type(typing.List) is True
    assert is_typing_type(typing.List[int]) is True
    assert is_typing_type(typing.Optional) is False
    assert is_typing_type(typing.Optional[int]) is True  # noqa: UP045
    assert is_typing_type(typing.Set) is True
    assert is_typing_type(typing.Set[int]) is True
    assert is_typing_type(typing.Set[typing.Dict[str, typing.Dict]]) is True
    assert is_typing_type(typing.Set[typing.Dict]) is True
    assert is_typing_type(typing.Set[typing.List]) is True
    assert is_typing_type(typing.Set[typing.Dict | None]) is True
    assert is_typing_type(typing.Set[typing.Tuple]) is True
    assert is_typing_type(typing.Tuple) is True
    assert is_typing_type(typing.Tuple[int, str]) is True
    assert is_typing_type(typing.Tuple[str, typing.Dict[str, typing.Dict]]) is True
    assert is_typing_type(typing.Tuple[str, typing.Dict]) is True
    assert is_typing_type(typing.Tuple[str, typing.List]) is True
    assert is_typing_type(typing.Tuple[str, typing.Dict | None]) is True
    assert is_typing_type(typing.Tuple[str, typing.Tuple]) is True
    assert is_typing_type(typing.Mapping) is True
    assert is_typing_type(typing.Mapping[str, typing.Any]) is True
    assert is_typing_type(typing.Mapping[str, int]) is True
    assert is_typing_type(typing.Sequence) is True
    assert is_typing_type(typing.Sequence[int]) is True
    assert is_typing_type(typing.Sequence[str]) is True


def test_flatten_unions() -> None:
    assert flatten_unions(str) == {str}
    assert flatten_unions(typing.Union[str, float]) == {str, float}  # noqa: UP007
    assert flatten_unions(typing.Union[str, float, int]) == {str, float, int}  # noqa: UP007
    assert flatten_unions(typing.Optional[str]) == {str, type(None)}  # noqa: UP045
    assert flatten_unions(typing.Optional[str | float]) == {  # noqa: UP045
        str,
        float,
        type(None),
    }
    assert flatten_unions(typing.Union[str | float, int]) == {  # noqa: UP007
        str,
        float,
        int,
    }
    assert flatten_unions(typing.Any) == {typing.Any}  # type: ignore

    # Python 3.10+ pipe syntax (creates types.UnionType instead of typing.Union)
    assert flatten_unions(str | float) == {str, float}
    assert flatten_unions(str | float | int) == {str, float, int}
    assert flatten_unions(str | None) == {str, type(None)}
