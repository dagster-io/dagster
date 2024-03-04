from typing import Any, Dict, Optional, TypedDict

import pytest
from dagster import _check as check
from typing_extensions import NotRequired


class MyNestedTypedDict(TypedDict):
    nested: Optional[str]


class MyTypedDict(TypedDict):
    nested: MyNestedTypedDict
    optional_field: Optional[str]
    dict_field: Dict[str, Any]
    not_required_field: NotRequired[str]


def test_init_optional_typeddict():
    assert check.init_optional_typeddict(MyTypedDict) == {
        "nested": {"nested": None},
        "optional_field": None,
        "dict_field": {},
    }


def test_validate_typeddict():
    valid_dict = {
        "nested": {"nested": None},
        "optional_field": None,
        "dict_field": {},
    }
    assert check.validate_typeddict(MyTypedDict, valid_dict) == valid_dict
    valid_with_not_required_field = {
        "nested": {"nested": None},
        "optional_field": None,
        "dict_field": {},
        "not_required_field": "value",
    }
    assert (
        check.validate_typeddict(MyTypedDict, valid_with_not_required_field)
        == valid_with_not_required_field
    )
    invalid_missing_required_field = {
        "nested": {"nested": None},
        "dict_field": {},
    }
    with pytest.raises(Exception, match="Missing required field optional_field in MyTypedDict"):
        check.validate_typeddict(MyTypedDict, invalid_missing_required_field)

    invalid_wrong_type = {
        "nested": {"nested": None},
        "optional_field": 123,
        "dict_field": {},
    }
    with pytest.raises(Exception, match="Field optional_field must be either None or of type str"):
        check.validate_typeddict(MyTypedDict, invalid_wrong_type)
