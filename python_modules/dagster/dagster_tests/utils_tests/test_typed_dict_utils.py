from typing import Optional, TypedDict

from dagster._utils.typed_dict import init_optional_typeddict


class MyNestedTypedDict(TypedDict):
    nested: Optional[str]


class MyTypedDict(TypedDict):
    nested: MyNestedTypedDict
    optional_field: Optional[str]


def test_init_optional_typeddict():
    assert init_optional_typeddict(MyTypedDict) == {
        "nested": {"nested": None},
        "optional_field": None,
    }
