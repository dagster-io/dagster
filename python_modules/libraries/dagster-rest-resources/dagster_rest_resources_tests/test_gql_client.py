import json
from unittest.mock import Mock, create_autospec

import httpx
import pytest
from dagster_rest_resources.__generated__.get_organization_settings import (
    GetOrganizationSettingsOrganizationSettings,
)
from dagster_rest_resources.gql_client import DagsterPlusGraphQLClient, DebugGraphQLClient
from dagster_rest_resources.schemas.exception import (
    DagsterPlusGraphqlError,
    DagsterPlusUnauthorizedError,
)


def _make_mock_response(data: dict) -> Mock:
    response = create_autospec(httpx.Response, spec_set=True, instance=True)
    response.is_success = True
    response.json.return_value = {"data": data}
    return response


class TestDagsterPlusGraphQLClientInit:
    def test_sets_url_suffix(self):
        client = DagsterPlusGraphQLClient(
            url="https://test.dagster.plus",
            api_token=None,
            organization=None,
            deployment=None,
        )

        assert client.url == "https://test.dagster.plus/graphql"

    def test_handles_url_trailing_slash(self):
        client = DagsterPlusGraphQLClient(
            url="https://test.dagster.plus/",
            api_token=None,
            organization=None,
            deployment=None,
        )

        assert client.url == "https://test.dagster.plus/graphql"

    def test_includes_provider_headers(self):
        client = DagsterPlusGraphQLClient(
            url="https://test.dagster.plus",
            api_token="test-token",
            organization="test-org",
            deployment="test-deployment",
        )

        assert client.headers == {
            "Dagster-Cloud-Api-Token": "test-token",
            "Dagster-Cloud-Organization": "test-org",
            "Dagster-Cloud-Deployment": "test-deployment",
        }

    def test_omits_none_header_values(self):
        client = DagsterPlusGraphQLClient(
            url="https://example.dagster.plus",
            api_token=None,
            organization=None,
            deployment=None,
        )

        assert client.headers == {}


def _make_dagster_plus_client() -> DagsterPlusGraphQLClient:
    return DagsterPlusGraphQLClient(
        url="https://test.dagster.plus",
        api_token="test-token",
        organization="test-org",
        deployment="test-deployment",
    )


class TestDagsterPlusGraphQLClientExecuteArbitrary:
    def test_returns_parsed_result(self):
        client = _make_dagster_plus_client()
        response_data = {"test_k": "test_v"}
        client.http_client = Mock()
        client.http_client.post.return_value = _make_mock_response(response_data)

        result = client.execute_arbitrary("{ test }")

        assert result == response_data

    def test_raises_unauthorized_error(self):
        client = _make_dagster_plus_client()
        client.http_client = Mock()
        client.http_client.post.return_value = _make_mock_response(
            {"foo": {"__typename": "UnauthorizedError", "message": "test not allowed"}}
        )

        with pytest.raises(DagsterPlusUnauthorizedError, match="test not allowed"):
            client.execute_arbitrary("{ test }")

    def test_raises_graphql_error(self):
        client = _make_dagster_plus_client()
        client.http_client = Mock()
        client.http_client.post.return_value = _make_mock_response(
            {"foo": {"__typename": "PythonError", "message": "test python error message"}}
        )

        with pytest.raises(DagsterPlusGraphqlError, match="test python error message"):
            client.execute_arbitrary("{ test }")

    def test_passes_through_non_mapping_value(self):
        client = _make_dagster_plus_client()
        response_data = {"count": 1}
        client.http_client = Mock()
        client.http_client.post.return_value = _make_mock_response(response_data)

        data = client.execute_arbitrary("{ test }")

        assert data == response_data


def _make_debug_client() -> tuple[list[str], Mock, DebugGraphQLClient]:
    log_calls: list[str] = []
    http_client = Mock()
    client = DebugGraphQLClient(
        url="https://test.dagster.plus",
        api_token="test-token",
        organization="test-org",
        deployment="test-deployment",
        log=log_calls.append,
        http_client=http_client,
    )
    return (log_calls, http_client, client)


class TestDebugGraphQLClientExecute:
    def test_logs_arguments(self):
        response_data = {"user": {"name": "test_name"}}
        mock_response = _make_mock_response(response_data)

        log_calls, mock_http_client, client = _make_debug_client()
        mock_http_client.post.return_value = mock_response

        variables = {"id": "123"}

        client.execute(
            "{ test }",
            operation_name="get_test",
            variables=variables,
            extra="test_kwarg",
        )

        assert log_calls[0] == "=== GraphQL Query ==="
        assert log_calls[1] == "{ test }"

        assert log_calls[2] == "=== Operation Name ==="
        assert log_calls[3] == "get_test"

        assert log_calls[4] == "=== Variables ==="
        assert log_calls[5] == json.dumps(variables, indent=2)

    def test_does_not_log_missing_arguments(self):
        response_data = {}
        mock_response = _make_mock_response(response_data)

        log_calls, mock_http_client, client = _make_debug_client()
        mock_http_client.post.return_value = mock_response

        client.execute("{ test }")

        assert log_calls[0] == "=== GraphQL Query ==="
        assert log_calls[1] == "{ test }"

        assert "=== Operation Name ===" not in log_calls
        assert "=== Variables ===" not in log_calls
        assert "=== kwargs ===" not in log_calls

    def test_returns_execute_response(self):
        response_data = {"test_k": "test_v"}
        mock_response = _make_mock_response(response_data)

        _, mock_http_client, client = _make_debug_client()
        mock_http_client.post.return_value = mock_response

        result = client.execute("{ test }")

        assert result is mock_response


class TestDebugGraphQLClientGetData:
    def test_logs_response(self):
        log_calls, _, client = _make_debug_client()
        response_data = {"organizationSettings": {"settings": {"sso_default_role": "VIEWER"}}}
        response = _make_mock_response(response_data)

        client.get_data(response)

        assert log_calls[0] == "=== Response ==="
        assert log_calls[1] == json.dumps(response_data, indent=2)

        assert log_calls[2] == "=" * 20

    def test_returns_parsed_data(self):
        _, _, client = _make_debug_client()
        response_data = {"organizationSettings": {"settings": {"sso_default_role": "VIEWER"}}}
        response = _make_mock_response(response_data)

        data = client.get_data(response)

        assert data == response_data


class TestDebugGraphQLClientOverridesUsedByGeneratedMethods:
    def test_logs_arguments_and_response(self):
        response_data = {"organizationSettings": {"settings": {"sso_default_role": "VIEWER"}}}
        mock_response = _make_mock_response(response_data)

        log_calls, mock_http_client, client = _make_debug_client()
        mock_http_client.post.return_value = mock_response

        client.get_organization_settings()

        assert "=== GraphQL Query ===" in log_calls
        assert "=== Operation Name ===" in log_calls
        assert "GetOrganizationSettings" in log_calls
        assert "=== Response ===" in log_calls
        assert json.dumps(response_data, indent=2) in log_calls

    def test_returns_parsed_result(self):
        settings = {"sso_default_role": "VIEWER"}
        response_data = {"organizationSettings": {"settings": settings}}
        mock_response = _make_mock_response(response_data)

        _, mock_http_client, client = _make_debug_client()
        mock_http_client.post.return_value = mock_response

        result = client.get_organization_settings()

        assert result.organization_settings == GetOrganizationSettingsOrganizationSettings(
            settings=settings
        )
