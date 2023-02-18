import json

from dagster import op
from dagster._utils.test import wrap_op_in_graph_and_execute
from dagster_msteams import msteams_resource
from mock import patch


@patch("dagster_msteams.client.TeamsClient.post_message")
def test_msteams_resource(mock_teams_post_message, json_message, teams_client):
    @op(required_resource_keys={"msteams"})
    def msteams_solid(context):
        assert context.resources.msteams
        body = {"ok": True}
        mock_teams_post_message.return_value = {
            "status": 200,
            "body": json.dumps(body),
            "headers": "",
        }
        teams_client.post_message(json_message)
        assert mock_teams_post_message.called

    result = wrap_op_in_graph_and_execute(
        msteams_solid,
        run_config={
            "resources": {
                "msteams": {
                    "config": {
                        "hook_url": "https://some_url_here/",
                        "https_proxy": "some_proxy",
                    }
                }
            }
        },
        resources={"msteams": msteams_resource},
    )
    assert result.success
