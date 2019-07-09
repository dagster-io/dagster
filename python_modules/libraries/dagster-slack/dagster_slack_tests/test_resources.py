import responses

from dagster import execute_pipeline, solid, pipeline, ModeDefinition

from dagster_slack import slack_resource


@responses.activate
def test_slack_resource():
    @solid(required_resource_keys={'slack'})
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

    @pipeline(mode_defs=[ModeDefinition(resource_defs={'slack': slack_resource})])
    def test_pipeline():
        slack_solid()  # pylint: disable=no-value-for-parameter

    result = execute_pipeline(
        test_pipeline,
        {'resources': {'slack': {'config': {'token': 'xoxp-1234123412341234-12341234-1234'}}}},
    )
    assert result.success
