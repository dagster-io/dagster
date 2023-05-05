import json

from dagster import op
from dagster._utils.test import wrap_op_in_graph_and_execute
from dagster_slack import SlackResource, slack_resource
from mock import patch


@patch("slack_sdk.WebClient.api_call")
def test_legacy_slack_resource(mock_api_call):
    @op(required_resource_keys={"slack"})
    def slack_op(context):
        assert context.resources.slack
        body = {"ok": True}
        mock_api_call.return_value = {
            "status": 200,
            "body": json.dumps(body),
            "headers": "",
        }

        context.resources.slack.chat_postMessage(channel="#random", text=":wave: hey there!")

        assert mock_api_call.called

    result = wrap_op_in_graph_and_execute(
        slack_op,
        run_config={
            "resources": {"slack": {"config": {"token": "xoxp-1234123412341234-12341234-1234"}}}
        },
        resources={"slack": slack_resource},
    )
    assert result.success


@patch("slack_sdk.WebClient.api_call")
def test_slack_resource(mock_api_call):
    @op
    def slack_op(slack: SlackResource):
        assert slack
        body = {"ok": True}
        mock_api_call.return_value = {
            "status": 200,
            "body": json.dumps(body),
            "headers": "",
        }

        slack.get_client().chat_postMessage(channel="#random", text=":wave: hey there!")

        assert mock_api_call.called

    result = wrap_op_in_graph_and_execute(
        slack_op,
        resources={"slack": SlackResource(token="xoxp-1234123412341234-12341234-1234")},
    )
    assert result.success
