import re
import warnings

import pytest
from dagster._annotations import experimental
from dagster._check import CheckError
from dagster._utils.warnings import (
    normalize_renamed_param,
    suppress_dagster_warnings,
)


def is_new(old_flag=None, new_flag=None):
    actual_new_flag = normalize_renamed_param(
        new_val=new_flag,
        new_arg="new_flag",
        old_val=old_flag,
        old_arg="old_flag",
        coerce_old_to_new=lambda val: not val,
    )

    return actual_new_flag


def test_renamed_param_default():
    assert is_new() is None


def test_renamed_param_new_name():
    assert is_new(new_flag=False) is False


def test_renamed_param_old_name():
    assert is_new(old_flag=False) is True


def test_renamed_param_both_names():
    with pytest.raises(
        CheckError,
        match=re.escape('Do not use deprecated "old_flag" now that you are using "new_flag".'),
    ):
        is_new(old_flag=False, new_flag=True)


def test_suppress_dagster_warnings() -> None:
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")

        @experimental
        def my_experimental_function(my_arg) -> None:
            pass

        assert len(w) == 0
        my_experimental_function("foo")
        assert len(w) == 1

    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")

        @experimental
        def my_experimental_function(my_arg) -> None:
            pass

        @suppress_dagster_warnings
        def my_quiet_wrapper(my_arg) -> None:
            my_experimental_function(my_arg)

        assert len(w) == 0
        my_quiet_wrapper("foo")
        assert len(w) == 0


def test_suppress_dagster_warnings_on_class() -> None:
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")

        @experimental
        class MyExperimental:
            def __init__(self, _string_in: str) -> None:
                pass

        assert len(w) == 0
        MyExperimental("foo")
        assert len(w) == 1

    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")

        @experimental
        class MyExperimentalTwo:
            def __init__(self, _string_in: str) -> None:
                pass

        class MyExperimentalWrapped(MyExperimentalTwo):
            @suppress_dagster_warnings
            def __init__(self, string_in: str) -> None:
                super().__init__(string_in)

        assert len(w) == 0
        MyExperimentalWrapped("foo")
        assert len(w) == 0
