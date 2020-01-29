import re

import pytest

from dagster.check import CheckError
from dagster.seven import mock
from dagster.utils.backcompat import canonicalize_backcompat_args


def is_new(old_flag=None, new_flag=None):
    actual_new_flag = canonicalize_backcompat_args(
        new_val=new_flag,
        new_arg='new_flag',
        old_val=old_flag,
        old_arg='old_flag',
        coerce_old_to_new=lambda val: not val,
        additional_warn_txt='Will remove at next release.',
    )

    return actual_new_flag


def test_backcompat_default():
    assert is_new() is None


def test_backcompat_new_flag():
    assert is_new(new_flag=False) is False


def test_backcompat_old_flag():
    with mock.patch('warnings.warn') as warn_mock:
        assert is_new(old_flag=False) is True
        warn_mock.assert_called_once_with(
            '"old_flag" is deprecated, use "new_flag" instead. Will remove at next release.',
            stacklevel=3,
        )


def test_backcompat_both_set():
    with pytest.raises(
        CheckError,
        match=re.escape('Do not use deprecated "old_flag" now that you are using "new_flag".'),
    ):
        is_new(old_flag=False, new_flag=True)
