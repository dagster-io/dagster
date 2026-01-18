from contextlib import contextmanager
from typing import Optional

import pytest


@contextmanager
def optional_pytest_raise(
    error_expected: bool, exception_cls: type[Exception], exception_message: Optional[str] = None
):
    if error_expected:
        kwargs = {}
        if exception_message:
            kwargs["match"] = exception_message
        with pytest.raises(exception_cls, **kwargs):
            yield
    else:
        yield
