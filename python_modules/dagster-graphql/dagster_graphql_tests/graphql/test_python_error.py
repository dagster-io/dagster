import sys
from unittest import mock

from dagster_graphql.client.client_queries import (
    CLIENT_GET_REPO_LOCATIONS_NAMES_AND_PIPELINES_QUERY,
)
from dagster_graphql.implementation.utils import ErrorCapture
from dagster_graphql.schema.errors import GraphenePythonError
from dagster_graphql.test.utils import execute_dagster_graphql

from dagster.utils.error import serializable_error_info_from_exc_info


def test_python_error():
    def func():
        raise Exception("bar")

    python_error = None
    try:
        func()
    except:  # pylint: disable=W0702
        python_error = GraphenePythonError(serializable_error_info_from_exc_info(sys.exc_info()))

    assert python_error
    assert isinstance(python_error.message, str)
    assert isinstance(python_error.stack, list)
    assert len(python_error.stack) == 2
    assert "bar" in python_error.stack[1]


def test_error_capture(graphql_context):
    seen = []

    def _new_on_exc(exc_info):
        seen.append(exc_info)
        return ErrorCapture.default_on_exception(exc_info)

    ErrorCapture.on_exception = _new_on_exc

    with mock.patch(
        "dagster.core.workspace.context.BaseWorkspaceRequestContext.repository_locations",
        new_callable=mock.PropertyMock,
    ) as repo_locs_mock:
        repo_locs_mock.side_effect = Exception("oops all berries")
        execute_dagster_graphql(
            graphql_context,
            CLIENT_GET_REPO_LOCATIONS_NAMES_AND_PIPELINES_QUERY,
        )

    assert len(seen) == 1
