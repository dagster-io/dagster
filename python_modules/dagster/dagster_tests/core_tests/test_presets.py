from dagster import PresetDefinition
from dagster.utils import script_relative_path

from ..test_repository import define_multi_mode_with_resources_pipeline


def test_preset_yaml_roundtrip():
    pipeline = define_multi_mode_with_resources_pipeline()

    preset_def = pipeline.get_presets()[0]

    with open(
        script_relative_path('../environments/multi_mode_with_resources/add_mode.yaml'), 'r'
    ) as fd:
        assert preset_def.get_environment_yaml(pipeline.name) == fd.read()


def test_empty_preset():
    pipeline = define_multi_mode_with_resources_pipeline()
    empty_preset = PresetDefinition('empty')
    assert empty_preset.get_environment_dict(pipeline.name) == {}
    assert empty_preset.get_environment_yaml(pipeline.name) == '{}\n'
