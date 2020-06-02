from dagster import ModeDefinition, PresetDefinition, pipeline, repository, solid
from dagster.core.host_representation import (
    external_pipeline_data_from_def,
    external_repository_data_from_def,
)
from dagster.serdes import serialize_pp


@solid
def a_solid(_):
    pass


@pipeline(
    mode_defs=[ModeDefinition('default'), ModeDefinition('mode_one')],
    preset_defs=[
        PresetDefinition(name='plain_preset'),
        PresetDefinition(
            name='kitchen_sink_preset',
            environment_dict={'foo': 'bar'},
            solid_subset=['a_solid'],
            mode='mode_one',
        ),
    ],
)
def a_pipeline():
    a_solid()


def test_external_repository_data(snapshot):
    @repository
    def repo():
        return [a_pipeline]

    snapshot.assert_match(serialize_pp(external_repository_data_from_def(repo)))


def test_external_pipeline_data(snapshot):
    snapshot.assert_match(serialize_pp(external_pipeline_data_from_def(a_pipeline)))
