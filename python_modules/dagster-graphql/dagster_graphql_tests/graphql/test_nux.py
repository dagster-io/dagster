import mock
from dagster_graphql.test.utils import (
    execute_dagster_graphql,
)

SET_NUX_SEEN_MUTATION = """
    mutation SetNuxSeen {
       setNuxSeen
    }
"""

GET_SHOULD_SHOW_NUX_QUERY = """
  query ShouldShowNux {
    shouldShowNux
  }

"""


def test_stores_nux_seen_state(graphql_context):
    result = execute_dagster_graphql(graphql_context, GET_SHOULD_SHOW_NUX_QUERY)
    assert not result.errors
    assert result.data
    assert result.data["shouldShowNux"] is True

    execute_dagster_graphql(graphql_context, SET_NUX_SEEN_MUTATION)

    result = execute_dagster_graphql(graphql_context, GET_SHOULD_SHOW_NUX_QUERY)
    assert not result.errors
    assert result.data
    assert result.data["shouldShowNux"] is False


def test_does_not_show_nux_if_read_only_filesystem(graphql_context):
    with mock.patch(
        "dagster._core.nux.nux_seen_filepath", side_effect=OSError("Read-only filesystem")
    ):
        result = execute_dagster_graphql(graphql_context, GET_SHOULD_SHOW_NUX_QUERY)
        assert not result.errors
        assert result.data
        assert result.data["shouldShowNux"] is False
