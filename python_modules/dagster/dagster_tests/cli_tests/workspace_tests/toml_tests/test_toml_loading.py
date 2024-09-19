from dagster._core.workspace.load_target import get_origins_from_toml, is_valid_modules_list
from dagster._utils import file_relative_path
from pytest import raises


def test_load_python_module_from_toml():
    origins = get_origins_from_toml(file_relative_path(__file__, "single_module.toml"))
    assert len(origins) == 1
    assert origins[0].loadable_target_origin.module_name == "baaz"
    assert origins[0].location_name == "baaz"

    origins = get_origins_from_toml(
        file_relative_path(__file__, "single_module_with_code_location_name.toml")
    )
    assert len(origins) == 1
    assert origins[0].loadable_target_origin.module_name == "baaz"
    assert origins[0].location_name == "bar"


def test_load_empty_toml():
    assert get_origins_from_toml(file_relative_path(__file__, "empty.toml")) == []


def test_load_toml_with_other_stuff():
    assert get_origins_from_toml(file_relative_path(__file__, "other_stuff.toml")) == []


def test_load_multiple_modules_from_toml():
    origins = get_origins_from_toml(file_relative_path(__file__, "multiple_modules.toml"))
    assert len(origins) == 2

    module_names = {origin.loadable_target_origin.module_name for origin in origins}
    expected_module_names = {"foo", "bar"}

    assert module_names == expected_module_names
    for origin in origins:
        assert origin.location_name in expected_module_names


def test_load_mixed_modules_and_module_name_from_toml():
    with raises(
        ValueError,
        match="Only one of 'module_name' or 'modules' should be specified, not both.",
    ):
        get_origins_from_toml(file_relative_path(__file__, "mixed_modules_and_module_name.toml"))


def test_load_invalid_empty_modules_from_toml():
    with raises(ValueError, match="'modules' list should not be empty if specified."):
        get_origins_from_toml(file_relative_path(__file__, "invalid_empty_modules.toml"))


def test_is_valid_modules_list_from_toml():
    # Only matchess first error of many, rest is covered below
    with raises(ValueError, match="Dictionary at index 0 does not contain the key 'type'."):
        get_origins_from_toml(file_relative_path(__file__, "invalid_modules_dict.toml"))


def test_is_valid_modules_list_not_a_list():
    with raises(ValueError, match="Modules should be a list."):
        is_valid_modules_list("not a list")


def test_is_valid_modules_list_item_not_dict():
    modules = ["not a dictionary"]
    with raises(ValueError, match="Item at index 0 is not a dictionary."):
        is_valid_modules_list(modules)


def test_is_valid_modules_list_missing_type():
    modules = [{"name": "foo"}]
    with raises(ValueError, match="Dictionary at index 0 does not contain the key 'type'."):
        is_valid_modules_list(modules)


def test_is_valid_modules_list_type_not_string():
    modules = [{"type": 123, "name": "foo"}]
    with raises(ValueError, match="The 'type' value in dictionary at index 0 is not a string."):
        is_valid_modules_list(modules)


def test_is_valid_modules_list_missing_name():
    modules = [{"type": "module"}]
    with raises(ValueError, match="Dictionary at index 0 does not contain the key 'name'."):
        is_valid_modules_list(modules)


def test_is_valid_modules_list_name_not_string():
    modules = [{"type": "module", "name": 123}]
    with raises(ValueError, match="The 'name' value in dictionary at index 0 is not a string."):
        is_valid_modules_list(modules)
