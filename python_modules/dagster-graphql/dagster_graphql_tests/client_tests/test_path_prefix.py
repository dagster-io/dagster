from unittest.mock import patch

import dagster._check as check
import pytest
from dagster_graphql import DagsterGraphQLClient

from dagster_graphql_tests.client_tests.conftest import python_client_test_suite


@python_client_test_suite
class TestPathPrefix:
    def test_default_url_no_path_prefix(self):
        with patch("dagster_graphql.client.client.Client"):
            client = DagsterGraphQLClient("localhost", port_number=3000)
            assert client._url == "http://localhost:3000/graphql"  # noqa: SLF001

    def test_url_with_path_prefix(self):
        with patch("dagster_graphql.client.client.Client"):
            client = DagsterGraphQLClient("localhost", port_number=3000, path_prefix="/dagster")
            assert client._url == "http://localhost:3000/dagster/graphql"  # noqa: SLF001

    def test_url_with_nested_path_prefix(self):
        with patch("dagster_graphql.client.client.Client"):
            client = DagsterGraphQLClient(
                "localhost", port_number=3000, path_prefix="/my/custom/prefix"
            )
            assert client._url == "http://localhost:3000/my/custom/prefix/graphql"  # noqa: SLF001

    def test_path_prefix_trailing_slash_stripped(self):
        with patch("dagster_graphql.client.client.Client"):
            client = DagsterGraphQLClient("localhost", port_number=3000, path_prefix="/dagster/")
            assert client._url == "http://localhost:3000/dagster/graphql"  # noqa: SLF001

    def test_path_prefix_missing_leading_slash_raises(self):
        with patch("dagster_graphql.client.client.Client"):
            with pytest.raises(check.CheckError, match='path_prefix must start with "/"'):
                DagsterGraphQLClient("localhost", port_number=3000, path_prefix="dagster")

    def test_path_prefix_with_https(self):
        with patch("dagster_graphql.client.client.Client"):
            client = DagsterGraphQLClient(
                "localhost", port_number=3000, use_https=True, path_prefix="/dagster"
            )
            assert client._url == "https://localhost:3000/dagster/graphql"  # noqa: SLF001

    def test_path_prefix_empty_string_default(self):
        with patch("dagster_graphql.client.client.Client"):
            client = DagsterGraphQLClient("localhost", port_number=3000, path_prefix="")
            assert client._url == "http://localhost:3000/graphql"  # noqa: SLF001
