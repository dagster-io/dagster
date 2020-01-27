from dagster_graphql.client.execute import execute_remote_pipeline_run


def test_execute_remote_pipeline_run(mocker):
    mocker.patch(
        'dagster_graphql.client.execute.execute_query_against_remote',
        return_value={'data': {'startPipelineExecution': {}}},
    )

    result = execute_remote_pipeline_run(
        "http://localhost:3000", "my_pipeline", environment_dict={}
    )

    assert result
    assert result['data']
    assert 'startPipelineExecution' in result['data']
