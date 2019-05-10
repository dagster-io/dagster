from dagster.utils import script_relative_path
from .setup import execute_dagster_graphql, define_context


def execute_preset_query(pipeline_name):
    pipeline_query = '''
        query PresetsQuery($pipelineName: String!) {
            presetsForPipeline(pipelineName: $pipelineName) {
                __typename
                name
                solidSubset
                environment
            }
        }
    '''

    # This is fairly horrific
    # See https://github.com/dagster-io/dagster/issues/1345
    return execute_dagster_graphql(
        define_context(
            repo_config={
                'pipelines': {
                    'pandas_hello_world_with_presets': {
                        'presets': {
                            'test': {
                                'environment_files': [
                                    script_relative_path(
                                        '../environments/pandas_hello_world_test.yml'
                                    )
                                ]
                            },
                            'prod': {
                                'environment_files': [
                                    script_relative_path(
                                        '../environments/pandas_hello_world_prod.yml'
                                    )
                                ]
                            },
                        }
                    }
                }
            }
        ),
        pipeline_query,
        variables={'pipelineName': pipeline_name},
    )


def test_basic_preset_query_no_presets():
    result = execute_preset_query('pandas_hello_world')
    assert result.data == {'presetsForPipeline': []}


def test_basic_preset_query_with_presets(snapshot):
    result = execute_preset_query('pandas_hello_world_with_presets')

    assert [preset_data['name'] for preset_data in result.data['presetsForPipeline']] == [
        'prod',
        'test',
    ]

    snapshot.assert_match(result.data)
