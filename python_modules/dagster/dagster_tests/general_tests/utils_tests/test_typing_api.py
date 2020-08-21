import typing

from dagster.utils.typing_api import (
    get_optional_inner_type,
    is_closed_python_dict_type,
    is_closed_python_list_type,
    is_closed_python_optional_type,
    is_closed_python_set_type,
    is_closed_python_tuple_type,
)


def test_closed_python_dict():
    assert is_closed_python_dict_type(typing.Dict[str, int]) is True

    assert is_closed_python_dict_type(dict) is False
    assert is_closed_python_dict_type(typing.Dict) is False
    assert is_closed_python_dict_type(None) is False
    assert is_closed_python_dict_type(1) is False
    assert is_closed_python_dict_type("foobar") is False
    assert is_closed_python_dict_type(typing.Optional) is False
    assert is_closed_python_dict_type(typing.List) is False


def test_is_typing_optional_py_3():
    assert is_closed_python_optional_type(typing.Optional[int])
    assert not is_closed_python_optional_type(typing.Optional)
    assert not is_closed_python_optional_type(None)
    assert not is_closed_python_optional_type(int)
    assert not is_closed_python_optional_type(list)
    assert not is_closed_python_optional_type("foobar")


def test_get_inner_optional_py_3():
    assert get_optional_inner_type(typing.Optional[int]) is int


def test_closed_tuple_type():
    assert is_closed_python_tuple_type(typing.Tuple[int, str]) is True

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
