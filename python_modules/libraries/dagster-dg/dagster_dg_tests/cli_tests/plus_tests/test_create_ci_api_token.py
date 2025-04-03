from typing import Callable, Optional
from unittest import mock

import pytest
import responses
from dagster_dg.utils import ensure_dagster_dg_tests_import

ensure_dagster_dg_tests_import()

from dagster_dg.utils.plus import gql
from dagster_dg_tests.cli_tests.plus_tests.utils import mock_gql_response
from dagster_dg_tests.utils import ProxyRunner, isolated_example_workspace


@pytest.fixture
def mock_get_or_create_agent_token():
    with mock.patch(
        "dagster_dg.cli.scaffold._get_or_create_agent_token"
    ) as mock_get_or_create_agent_token:
        yield mock_get_or_create_agent_token


@pytest.fixture
def mock_token_gql_responses() -> Callable[[str], None]:
    def _mock(description: Optional[str] = None) -> None:
        mock_gql_response(
            query=gql.AGENT_TOKENS_QUERY,
            json_data={
                "data": {
                    "agentTokensOrError": {
                        "__typename": "AgentTokens",
                        "tokens": [],
                    }
                }
            },
        )

        mock_gql_response(
            query=gql.CREATE_AGENT_TOKEN_MUTATION,
            json_data={"data": {"createAgentToken": {"token": "abc123"}}},
            expected_variables={"description": description},
        )

    return _mock


@responses.activate
@pytest.mark.parametrize("description", ["Used in dagster-workspace GitHub Actions", None])
def test_create_ci_api_token(
    dg_plus_cli_config,
    mock_token_gql_responses,
    description: str,
):
    with (
        ProxyRunner.test(use_fixed_test_components=True) as runner,
        isolated_example_workspace(runner),
    ):
        mock_token_gql_responses(description)

        from dagster_dg.cli.scaffold import GITHUB_ACTIONS_WORKFLOW_URL

        responses.add_passthru(GITHUB_ACTIONS_WORKFLOW_URL)

        result = runner.invoke(
            "plus",
            "create-ci-api-token",
            *(["--description", "Used in dagster-workspace GitHub Actions"] if description else []),
        )
        assert result.exit_code == 0, result.output + " " + str(result.exception)

        assert "abc123" in result.output
