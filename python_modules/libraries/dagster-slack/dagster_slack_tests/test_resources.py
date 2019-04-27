import responses

from dagster import execute_pipeline, solid, PipelineContextDefinition, PipelineDefinition

from dagster_slack import slack_resource


@responses.activate
def test_slack_resource():
    @solid
    def slack_solid(context):
        assert context.resources.slack
        with responses.RequestsMock() as rsps:
            rsps.add(
                rsps.POST,
                'https://slack.com/api/chat.postMessage',
                status=200,
                json={
                    'ok': True,
                    'channel': 'SOME_CHANNEL',
                    'ts': '1555993892.000300',
                    'headers': {'Content-Type': 'application/json; charset=utf-8'},
                },
            )
            context.resources.slack.chat.post_message()

    pipeline = PipelineDefinition(
        name='test_slack_resource',
        solids=[slack_solid],
        context_definitions={
            'default': PipelineContextDefinition(resources={'slack': slack_resource})
        },
    )

    result = execute_pipeline(
        pipeline,
        {
            'context': {
                'default': {
                    'resources': {
                        'slack': {'config': {'token': 'xoxp-1234123412341234-12341234-1234'}}
                    }
                }
            }
        },
    )
    assert result.success
