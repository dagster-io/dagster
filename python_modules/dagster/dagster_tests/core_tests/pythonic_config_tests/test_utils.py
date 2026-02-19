import sys

import pytest
from dagster._utils.typing_api import is_closed_python_optional_type


def test_is_closed_python_optional_type() -> None:
    from typing import Union

    assert is_closed_python_optional_type(str | None)
    assert is_closed_python_optional_type(int | None)

    assert not is_closed_python_optional_type(str)
    assert not is_closed_python_optional_type(int)

    assert is_closed_python_optional_type(Union[str, None])  # noqa: UP007
    assert is_closed_python_optional_type(Union[int, None])  # noqa: UP007

    assert is_closed_python_optional_type(Union[None, str])  # noqa: UP007
    assert is_closed_python_optional_type(Union[None, int])  # noqa: UP007

    assert not is_closed_python_optional_type(Union[str, int])  # noqa: UP007
    assert not is_closed_python_optional_type(Union[str, int, None])  # noqa: UP007


@pytest.mark.skipif(sys.version_info < (3, 10), reason="requires python3.10")
def test_is_closed_python_optional_type_310_types() -> None:
    assert is_closed_python_optional_type(str | None)
    assert is_closed_python_optional_type(int | None)

    assert is_closed_python_optional_type(None | str)
    assert is_closed_python_optional_type(None | int)

    assert not is_closed_python_optional_type(str | int)
    assert not is_closed_python_optional_type(str | int | None)
