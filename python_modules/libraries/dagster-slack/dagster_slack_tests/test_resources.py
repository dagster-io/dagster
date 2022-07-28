import json

from dagster_slack import slack_resource
from mock import patch

from dagster import execute_solid
from dagster._legacy import ModeDefinition, solid


@patch("slack_sdk.WebClient.api_call")
def test_slack_resource(mock_api_call):
    @solid(required_resource_keys={"slack"})
    def slack_solid(context):
        assert context.resources.slack
        body = {"ok": True}
        mock_api_call.return_value = {
            "status": 200,
            "body": json.dumps(body),
            "headers": "",
        }

        context.resources.slack.chat_postMessage(channel="#random", text=":wave: hey there!")

        assert mock_api_call.called

    result = execute_solid(
        slack_solid,
        run_config={
            "resources": {"slack": {"config": {"token": "xoxp-1234123412341234-12341234-1234"}}}
        },
        mode_def=ModeDefinition(resource_defs={"slack": slack_resource}),
    )
    assert result.success
