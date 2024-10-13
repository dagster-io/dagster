import sys

import pytest
from dagster._utils.typing_api import is_closed_python_optional_type


def test_is_closed_python_optional_type() -> None:
    from typing import Optional, Union

    assert is_closed_python_optional_type(Optional[str])
    assert is_closed_python_optional_type(Optional[int])

    assert not is_closed_python_optional_type(str)
    assert not is_closed_python_optional_type(int)

    assert is_closed_python_optional_type(Union[str, None])
    assert is_closed_python_optional_type(Union[int, None])

    assert is_closed_python_optional_type(Union[None, str])
    assert is_closed_python_optional_type(Union[None, int])

    assert not is_closed_python_optional_type(Union[str, int])
    assert not is_closed_python_optional_type(Union[str, int, None])


@pytest.mark.skipif(sys.version_info < (3, 10), reason="requires python3.10")
def test_is_closed_python_optional_type_310_types() -> None:
    assert is_closed_python_optional_type(str | None)  # type: ignore
    assert is_closed_python_optional_type(int | None)  # type: ignore

    assert is_closed_python_optional_type(None | str)  # type: ignore
    assert is_closed_python_optional_type(None | int)  # type: ignore

    assert not is_closed_python_optional_type(str | int)  # type: ignore
    assert not is_closed_python_optional_type(str | int | None)  # type: ignore
