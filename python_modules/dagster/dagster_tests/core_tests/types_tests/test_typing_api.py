import sys
import typing

import pytest

from dagster.core.types.typing_api import (
    get_optional_inner_type,
    is_closed_python_dict_type,
    is_closed_python_optional_typehint,
    is_python_list_typehint,
)

REASON_STRING = 'typing_api only valid for python 3'


def test_closed_python_dict():
    assert is_closed_python_dict_type(typing.Dict[str, int]) is True

    assert is_closed_python_dict_type(dict) is False
    assert is_closed_python_dict_type(typing.Dict) is False
    assert is_closed_python_dict_type(None) is False
    assert is_closed_python_dict_type(1) is False
    assert is_closed_python_dict_type('foobar') is False
    assert is_closed_python_dict_type(typing.Optional) is False
    assert is_closed_python_dict_type(typing.List) is False


@pytest.mark.skipif(sys.version_info.major < 3, reason=REASON_STRING)
def test_is_typing_list_py_3():
    assert is_python_list_typehint(typing.List[int])
    assert is_python_list_typehint(typing.List)
    assert is_python_list_typehint(list)
    assert not is_python_list_typehint(None)
    assert not is_python_list_typehint(int)
    assert not is_python_list_typehint('foobar')


@pytest.mark.skipif(sys.version_info.major < 3, reason=REASON_STRING)
def test_is_typing_optional_py_3():
    assert is_closed_python_optional_typehint(typing.Optional[int])
    assert not is_closed_python_optional_typehint(typing.Optional)
    assert not is_closed_python_optional_typehint(None)
    assert not is_closed_python_optional_typehint(int)
    assert not is_closed_python_optional_typehint(list)
    assert not is_closed_python_optional_typehint('foobar')


@pytest.mark.skipif(sys.version_info.major < 3, reason=REASON_STRING)
def test_get_inner_optional_py_3():
    assert get_optional_inner_type(typing.Optional[int]) is int


PY_2_REASON_STRING = 'Only checking python 2 implementations'


@pytest.mark.skipif(sys.version_info.major >= 3, reason=PY_2_REASON_STRING)
def test_is_typing_list_py_2():
    with pytest.raises(NotImplementedError):
        is_python_list_typehint(typing.List[int])


@pytest.mark.skipif(sys.version_info.major >= 3, reason=PY_2_REASON_STRING)
def test_is_typing_optional_py_2():
    with pytest.raises(NotImplementedError):
        is_closed_python_optional_typehint(typing.Optional[int])
