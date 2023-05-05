from dagster._core.workspace.load_target import get_origins_from_toml
from dagster._utils import file_relative_path


def test_load_python_module_from_toml():
    origins = get_origins_from_toml(file_relative_path(__file__, "single_module.toml"))
    assert len(origins) == 1
    assert origins[0].loadable_target_origin.module_name == "baaz"


def test_load_empty_toml():
    assert get_origins_from_toml(file_relative_path(__file__, "empty.toml")) == []


def test_load_toml_with_other_stuff():
    assert get_origins_from_toml(file_relative_path(__file__, "other_stuff.toml")) == []
