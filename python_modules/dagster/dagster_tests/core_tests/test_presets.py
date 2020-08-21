from dagster_tests.general_tests.test_repository import define_multi_mode_with_resources_pipeline

from dagster import PresetDefinition
from dagster.utils import file_relative_path


def test_preset_yaml_roundtrip():
    pipeline = define_multi_mode_with_resources_pipeline()

    preset_def = pipeline.get_preset("add")

    with open(
        file_relative_path(__file__, "../environments/multi_mode_with_resources/add_mode.yaml"), "r"
    ) as fd:
        assert preset_def.get_environment_yaml() == fd.read()


def test_empty_preset():
    empty_preset = PresetDefinition("empty")
    assert empty_preset.run_config == None
    assert empty_preset.get_environment_yaml() == "{}\n"
