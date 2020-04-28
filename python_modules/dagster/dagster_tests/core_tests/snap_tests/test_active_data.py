from dagster import ModeDefinition, PresetDefinition, RepositoryDefinition, pipeline, solid
from dagster.core.snap import active_repository_data_from_def
from dagster.serdes import serialize_pp


def test_active_data(snapshot):
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

    rep_def = RepositoryDefinition(name='repo', pipeline_defs=[a_pipeline])

    snapshot.assert_match(serialize_pp(active_repository_data_from_def(rep_def)))
