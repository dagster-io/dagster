from dagster._cli.workspace.cli_target import get_target_from_toml
from dagster._core.workspace.load_target import ModuleTarget
from dagster._utils import file_relative_path


def test_load_python_module_from_toml():
    target = get_target_from_toml(file_relative_path(__file__, "single_module.toml"))
    assert isinstance(target, ModuleTarget)
    assert target.module_name == "baaz"


def test_load_empty_toml():
    assert get_target_from_toml(file_relative_path(__file__, "empty.toml")) is None


def test_load_toml_with_other_stuff():
    assert get_target_from_toml(file_relative_path(__file__, "other_stuff.toml")) is None
