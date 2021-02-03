import pytest
from dagster import Any, Enum, EnumValue, Field, Noneable, Permissive, String
from dagster.check import CheckError, ParameterCheckError
from dagster.config.config_type import ConfigType, ConfigTypeKind
from dagster.config.field import resolve_to_config_type
from dagster.config.field_utils import Selector
from dagster.config.post_process import post_process_config


def test_post_process_config():
    scalar_config_type = resolve_to_config_type(String)
    assert post_process_config(scalar_config_type, "foo").value == "foo"
    assert post_process_config(scalar_config_type, 3).value == 3
    assert post_process_config(scalar_config_type, {}).value == {}
    assert post_process_config(scalar_config_type, None).value is None

    enum_config_type = resolve_to_config_type(
        Enum("an_enum", [EnumValue("foo"), EnumValue("bar", python_value=3)])
    )
    assert post_process_config(enum_config_type, "foo").value == "foo"
    assert post_process_config(enum_config_type, "bar").value == 3
    with pytest.raises(CheckError):
        post_process_config(enum_config_type, "baz")
    with pytest.raises(CheckError):
        post_process_config(enum_config_type, None)
    list_config_type = resolve_to_config_type([str])

    assert post_process_config(list_config_type, ["foo"]).value == ["foo"]
    assert post_process_config(list_config_type, None).value == []
    with pytest.raises(CheckError, match="Null array member not caught"):
        assert post_process_config(list_config_type, [None]).value == [None]

    nullable_list_config_type = resolve_to_config_type([Noneable(str)])
    assert post_process_config(nullable_list_config_type, ["foo"]).value == ["foo"]
    assert post_process_config(nullable_list_config_type, [None]).value == [None]
    assert post_process_config(nullable_list_config_type, None).value == []

    composite_config_type = resolve_to_config_type(
        {
            "foo": String,
            "bar": {"baz": [str]},
            "quux": Field(str, is_required=False, default_value="zip"),
            "quiggle": Field(str, is_required=False),
        }
    )
    with pytest.raises(CheckError, match="Missing required composite member"):
        post_process_config(composite_config_type, {})

    with pytest.raises(CheckError, match="Missing required composite member"):
        post_process_config(composite_config_type, {"bar": {"baz": ["giraffe"]}, "quux": "nimble"})

    with pytest.raises(CheckError, match="Missing required composite member"):
        post_process_config(composite_config_type, {"foo": "zowie", "quux": "nimble"})

    assert post_process_config(
        composite_config_type, {"foo": "zowie", "bar": {"baz": ["giraffe"]}, "quux": "nimble"}
    ).value == {"foo": "zowie", "bar": {"baz": ["giraffe"]}, "quux": "nimble"}

    assert post_process_config(
        composite_config_type, {"foo": "zowie", "bar": {"baz": ["giraffe"]}}
    ).value == {"foo": "zowie", "bar": {"baz": ["giraffe"]}, "quux": "zip"}

    assert post_process_config(
        composite_config_type, {"foo": "zowie", "bar": {"baz": ["giraffe"]}, "quiggle": "squiggle"}
    ).value == {"foo": "zowie", "bar": {"baz": ["giraffe"]}, "quux": "zip", "quiggle": "squiggle"}

    nested_composite_config_type = resolve_to_config_type(
        {
            "fruts": {
                "apple": Field(String),
                "banana": Field(String, is_required=False),
                "potato": Field(String, is_required=False, default_value="pie"),
            }
        }
    )

    with pytest.raises(CheckError, match="Missing required composite member"):
        post_process_config(nested_composite_config_type, {"fruts": None})

    with pytest.raises(CheckError, match="Missing required composite member"):
        post_process_config(
            nested_composite_config_type, {"fruts": {"banana": "good", "potato": "bad"}}
        )

    assert post_process_config(
        nested_composite_config_type, {"fruts": {"apple": "strawberry"}}
    ).value == {"fruts": {"apple": "strawberry", "potato": "pie"}}

    assert post_process_config(
        nested_composite_config_type, {"fruts": {"apple": "a", "banana": "b", "potato": "c"}}
    ).value == {"fruts": {"apple": "a", "banana": "b", "potato": "c"}}

    any_config_type = resolve_to_config_type(Any)

    assert post_process_config(any_config_type, {"foo": "bar"}).value == {"foo": "bar"}

    assert post_process_config(
        ConfigType("gargle", given_name="bargle", kind=ConfigTypeKind.ANY), 3
    )

    selector_config_type = resolve_to_config_type(
        Selector(
            {
                "one": Field(String),
                "another": {"foo": Field(String, default_value="bar", is_required=False)},
                "yet_another": Field(String, default_value="quux", is_required=False),
            }
        )
    )

    with pytest.raises(CheckError):
        post_process_config(selector_config_type, "one")

    with pytest.raises(ParameterCheckError):
        post_process_config(selector_config_type, None)

    with pytest.raises(ParameterCheckError, match="Expected dict with single item"):
        post_process_config(selector_config_type, {})

    with pytest.raises(CheckError):
        post_process_config(selector_config_type, {"one": "foo", "another": "bar"})

    assert post_process_config(selector_config_type, {"one": "foo"}).value == {"one": "foo"}

    assert post_process_config(selector_config_type, {"one": None}).value == {"one": None}

    assert post_process_config(selector_config_type, {"one": {}}).value == {"one": {}}

    assert post_process_config(selector_config_type, {"another": {}}).value == {
        "another": {"foo": "bar"}
    }

    singleton_selector_config_type = resolve_to_config_type(
        Selector({"foo": Field(String, default_value="bar", is_required=False)})
    )

    assert post_process_config(singleton_selector_config_type, None).value == {"foo": "bar"}

    permissive_dict_config_type = resolve_to_config_type(
        Permissive(
            {"foo": Field(String), "bar": Field(String, default_value="baz", is_required=False)}
        )
    )

    with pytest.raises(CheckError, match="Missing required composite member"):
        post_process_config(permissive_dict_config_type, None)

    assert post_process_config(permissive_dict_config_type, {"foo": "wow", "mau": "mau"}).value == {
        "foo": "wow",
        "bar": "baz",
        "mau": "mau",
    }

    noneable_permissive_config_type = resolve_to_config_type(
        {"args": Field(Noneable(Permissive()), is_required=False, default_value=None)}
    )
    assert post_process_config(
        noneable_permissive_config_type, {"args": {"foo": "wow", "mau": "mau"}}
    ).value["args"] == {
        "foo": "wow",
        "mau": "mau",
    }
    assert post_process_config(noneable_permissive_config_type, {"args": {}}).value["args"] == {}
    assert post_process_config(noneable_permissive_config_type, None).value["args"] == None
