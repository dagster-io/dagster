import re

import pytest
from dagster.check import CheckError
from dagster.utils.backcompat import (
    EXPERIMENTAL_WARNING_HELP,
    ExperimentalWarning,
    canonicalize_backcompat_args,
    experimental,
    experimental_arg_warning,
    experimental_class_warning,
    experimental_fn_warning,
)
from dagster_tests.general_tests.utils_tests.utils import assert_no_warnings


def is_new(old_flag=None, new_flag=None, include_additional_warn_txt=True):
    actual_new_flag = canonicalize_backcompat_args(
        new_val=new_flag,
        new_arg="new_flag",
        old_val=old_flag,
        old_arg="old_flag",
        breaking_version="0.9.0",
        coerce_old_to_new=lambda val: not val,
        additional_warn_txt="Will remove at next release." if include_additional_warn_txt else None,
    )

    return actual_new_flag


def test_backcompat_default():
    assert is_new() is None


def test_backcompat_new_flag():
    assert is_new(new_flag=False) is False


def test_backcompat_old_flag():
    with pytest.warns(
        UserWarning,
        match=re.escape(
            '"old_flag" is deprecated and will be removed in 0.9.0, use "new_flag" instead. Will '
            "remove at next release."
        ),
    ):
        assert is_new(old_flag=False) is True


def test_backcompat_no_additional_warn_text():
    with pytest.warns(
        UserWarning,
        match=re.escape(
            '"old_flag" is deprecated and will be removed in 0.9.0, use "new_flag" instead.'
        ),
    ):
        assert is_new(old_flag=False, include_additional_warn_txt=False) is True


def test_backcompat_both_set():
    with pytest.raises(
        CheckError,
        match=re.escape('Do not use deprecated "old_flag" now that you are using "new_flag".'),
    ):
        is_new(old_flag=False, new_flag=True)


def test_experimental_fn_warning():
    def my_experimental_function():
        experimental_fn_warning("my_experimental_function")

    with pytest.warns(
        ExperimentalWarning,
        match='"my_experimental_function" is an experimental function. It may break in future'
        " versions, even between dot releases. ",
    ) as warning:
        my_experimental_function()

    assert warning[0].filename.endswith("test_backcompat.py")


def test_experimental_class_warning():
    class MyExperimentalClass:
        def __init__(self):
            experimental_class_warning("MyExperimentalClass")

    with pytest.warns(
        ExperimentalWarning,
        match='"MyExperimentalClass" is an experimental class. It may break in future'
        " versions, even between dot releases. ",
    ) as warning:
        MyExperimentalClass()

    assert warning[0].filename.endswith("test_backcompat.py")


def test_experimental_arg_warning():
    def stable_function(_stable_arg, _experimental_arg):
        experimental_arg_warning("experimental_arg", "stable_function")

    with pytest.warns(
        ExperimentalWarning,
        match='"experimental_arg" is an experimental argument to function "stable_function". '
        "It may break in future versions, even between dot releases. ",
    ) as warning:
        stable_function(1, 2)

    assert warning[0].filename.endswith("test_backcompat.py")


def test_experimental_decorator():
    with assert_no_warnings():

        @experimental
        def my_experimental_function(some_arg):
            assert some_arg == 5
            return 4

    assert my_experimental_function.__name__ == "my_experimental_function"

    with pytest.warns(
        ExperimentalWarning,
        match='"my_experimental_function" is an experimental function. It may break in future'
        " versions, even between dot releases. ",
    ) as warning:
        assert my_experimental_function(5) == 4

    assert warning[0].filename.endswith("test_backcompat.py")
