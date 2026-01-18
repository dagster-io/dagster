from unittest.mock import MagicMock

from dagster_cloud_cli.core.graphql_client import DagsterCloudGraphQLClient
from dagster_cloud_cli.gql import graphql_client_from_url, mark_cli_event


def test_graphql_client_from_url_doesnt_raise():
    with graphql_client_from_url(str(None), str(None)):
        pass

    with graphql_client_from_url("bad-url", "bad-token"):
        pass


def test_mark_cli_event_doesnt_raise():
    client = MagicMock(DagsterCloudGraphQLClient, autospec=True)
    client.execute.side_effect = Exception("boom")

    mark_cli_event(
        client=client,
        event_type=MagicMock(),
        duration_seconds=MagicMock(),
        tags=MagicMock(),
    )
