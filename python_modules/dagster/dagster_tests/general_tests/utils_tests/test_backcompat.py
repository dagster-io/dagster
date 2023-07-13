import re
import warnings

import pytest
from dagster._annotations import experimental
from dagster._check import CheckError
from dagster._utils.backcompat import (
    ExperimentalWarning,
    canonicalize_backcompat_args,
    experimental_arg_warning,
    quiet_experimental_warnings,
)


def is_new(old_flag=None, new_flag=None, include_additional_warn_txt=True):
    actual_new_flag = canonicalize_backcompat_args(
        new_val=new_flag,
        new_arg="new_flag",
        old_val=old_flag,
        old_arg="old_flag",
        breaking_version="0.9.0",
        coerce_old_to_new=lambda val: not val,
        additional_warn_text="Will remove at next release."
        if include_additional_warn_txt
        else None,
    )

    return actual_new_flag


def test_backcompat_default():
    assert is_new() is None


def test_backcompat_new_flag():
    assert is_new(new_flag=False) is False


def test_backcompat_old_flag():
    with pytest.warns(
        DeprecationWarning,
        match=re.escape(
            '"old_flag" is deprecated and will be removed in 0.9.0. Use "new_flag" instead. Will '
            "remove at next release."
        ),
    ):
        assert is_new(old_flag=False) is True


def test_backcompat_no_additional_warn_text():
    with pytest.warns(
        DeprecationWarning,
        match=re.escape(
            '"old_flag" is deprecated and will be removed in 0.9.0. Use "new_flag" instead.'
        ),
    ):
        assert is_new(old_flag=False, include_additional_warn_txt=False) is True


def test_backcompat_both_set():
    with pytest.raises(
        CheckError,
        match=re.escape('Do not use deprecated "old_flag" now that you are using "new_flag".'),
    ):
        is_new(old_flag=False, new_flag=True)


def test_experimental_arg_warning():
    def stable_function(_stable_arg, _experimental_arg):
        experimental_arg_warning("experimental_arg", "stable_function")

    with pytest.warns(
        ExperimentalWarning,
        match=(
            '"experimental_arg" is an experimental argument to function "stable_function". '
            "It may break in future versions, even between dot releases. "
        ),
    ) as warning:
        stable_function(1, 2)

    assert warning[0].filename.endswith("test_backcompat.py")


def test_quiet_experimental_warnings() -> None:
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

        @quiet_experimental_warnings
        def my_quiet_wrapper(my_arg) -> None:
            my_experimental_function(my_arg)

        assert len(w) == 0
        my_quiet_wrapper("foo")
        assert len(w) == 0


def test_quiet_experimental_warnings_on_class() -> None:
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
            @quiet_experimental_warnings
            def __init__(self, string_in: str) -> None:
                super().__init__(string_in)

        assert len(w) == 0
        MyExperimentalWrapped("foo")
        assert len(w) == 0
