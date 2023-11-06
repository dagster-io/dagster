import sys

import pytest
from dagster._config.pythonic_config.type_check_utils import is_optional


def test_is_optional() -> None:
    from typing import Optional, Union

    assert is_optional(Optional[str])
    assert is_optional(Optional[int])

    assert not is_optional(str)
    assert not is_optional(int)

    assert is_optional(Union[str, None])
    assert is_optional(Union[int, None])

    assert is_optional(Union[None, str])
    assert is_optional(Union[None, int])

    assert not is_optional(Union[str, int])
    assert not is_optional(Union[str, int, None])


@pytest.mark.skipif(sys.version_info < (3, 10), reason="requires python3.10")
def test_is_optional_310_types() -> None:
    assert is_optional(str | None)  # type: ignore
    assert is_optional(int | None)  # type: ignore

    assert is_optional(None | str)  # type: ignore
    assert is_optional(None | int)  # type: ignore

    assert not is_optional(str | int)  # type: ignore
    assert not is_optional(str | int | None)  # type: ignore
