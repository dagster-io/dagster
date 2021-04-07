from collections import namedtuple
from unittest.mock import patch

import pytest
from dagster_graphql import DagsterGraphQLClient

MockClient = namedtuple("MockClient", ("python_client", "mock_gql_client"))


@pytest.fixture(scope="function", name="mock_client")
def create_mock_client():
    with patch("dagster_graphql.client.client.Client") as _:
        client = DagsterGraphQLClient("localhost")
        yield MockClient(
            python_client=client, mock_gql_client=client._client  # pylint: disable=W0212
        )


python_client_test_suite = pytest.mark.python_client_test_suite
