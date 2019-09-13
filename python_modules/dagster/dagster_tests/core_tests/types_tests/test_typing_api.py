import typing

from dagster.core.types.typing_api import (
    get_optional_inner_type,
    is_closed_python_dict_type,
    is_closed_python_optional_type,
    is_python_list_type,
)


def test_closed_python_dict():
    assert is_closed_python_dict_type(typing.Dict[str, int]) is True

    assert is_closed_python_dict_type(dict) is False
    assert is_closed_python_dict_type(typing.Dict) is False
    assert is_closed_python_dict_type(None) is False
    assert is_closed_python_dict_type(1) is False
    assert is_closed_python_dict_type('foobar') is False
    assert is_closed_python_dict_type(typing.Optional) is False
    assert is_closed_python_dict_type(typing.List) is False


def test_is_typing_list():
    assert is_python_list_type(typing.List[int])
    assert is_python_list_type(typing.List)
    assert is_python_list_type(list)
    assert not is_python_list_type(None)
    assert not is_python_list_type(int)
    assert not is_python_list_type('foobar')


def test_is_typing_optional_py_3():
    assert is_closed_python_optional_type(typing.Optional[int])
    assert not is_closed_python_optional_type(typing.Optional)
    assert not is_closed_python_optional_type(None)
    assert not is_closed_python_optional_type(int)
    assert not is_closed_python_optional_type(list)
    assert not is_closed_python_optional_type('foobar')


def test_get_inner_optional_py_3():
    assert get_optional_inner_type(typing.Optional[int]) is int
