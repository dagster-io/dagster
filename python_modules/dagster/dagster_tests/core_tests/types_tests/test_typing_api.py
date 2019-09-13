import sys
from typing import List, Optional

import pytest

from dagster.core.types.typing_api import (
    get_optional_inner_type,
    is_closed_python_optional_typehint,
    is_python_list_typehint,
)


def py_3_only(fn):
    if sys.version_info.major < 3:
        return

    return fn


REASON_STRING = 'typing_api only valid for python 3'


@pytest.mark.skipif(sys.version_info.major < 3, reason=REASON_STRING)
def test_is_typing_list_py_3():
    assert is_python_list_typehint(List[int])
    assert is_python_list_typehint(List)
    assert is_python_list_typehint(list)
    assert not is_python_list_typehint(None)
    assert not is_python_list_typehint(int)
    assert not is_python_list_typehint('foobar')


@pytest.mark.skipif(sys.version_info.major < 3, reason=REASON_STRING)
def test_is_typing_optional_py_3():
    assert is_closed_python_optional_typehint(Optional[int])
    assert not is_closed_python_optional_typehint(Optional)
    assert not is_closed_python_optional_typehint(None)
    assert not is_closed_python_optional_typehint(int)
    assert not is_closed_python_optional_typehint(list)
    assert not is_closed_python_optional_typehint('foobar')


@pytest.mark.skipif(sys.version_info.major < 3, reason=REASON_STRING)
def test_get_inner_optional_py_3():
    assert get_optional_inner_type(Optional[int]) is int


PY_2_REASON_STRING = 'Only checking python 2 implementations'


@pytest.mark.skipif(sys.version_info.major >= 3, reason=PY_2_REASON_STRING)
def test_is_typing_list_py_2():
    assert not is_python_list_typehint(List[int])
    assert not is_python_list_typehint(List)
    assert not is_python_list_typehint(list)
    assert not is_python_list_typehint(None)
    assert not is_python_list_typehint(int)
    assert not is_python_list_typehint('foobar')


@pytest.mark.skipif(sys.version_info.major >= 3, reason=PY_2_REASON_STRING)
def test_is_typing_optional_py_2():
    assert not is_closed_python_optional_typehint(Optional[int])
    assert not is_closed_python_optional_typehint(Optional)
    assert not is_closed_python_optional_typehint(None)
    assert not is_closed_python_optional_typehint(int)
    assert not is_closed_python_optional_typehint(list)
    assert not is_closed_python_optional_typehint('foobar')
