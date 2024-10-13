import time
from typing import Mapping, Optional

import pytest
from dagster._core.execution.backfill import BulkActionStatus, PartitionBackfill
from dagster._core.remote_representation.origin import RemotePartitionSetOrigin
from dagster._core.storage.dagster_run import DagsterRun, DagsterRunStatus
from dagster._core.storage.tags import BACKFILL_ID_TAG
from dagster._core.test_utils import create_run_for_test
from dagster._core.utils import make_new_backfill_id
from dagster._time import get_current_timestamp
from dagster_graphql.implementation.fetch_runs import RunsFeedCursor
from dagster_graphql.test.utils import execute_dagster_graphql

from dagster_graphql_tests.graphql.graphql_context_test_suite import (
    ExecutingGraphQLContextTestMatrix,
)

GET_RUNS_FEED_QUERY = """
query RunsFeedEntryQuery($cursor: String, $limit: Int!, $filter: RunsFilter, $includeRunsFromBackfills: Boolean!) {
    runsFeedOrError(cursor: $cursor, limit: $limit, filter: $filter, includeRunsFromBackfills: $includeRunsFromBackfills) {
      ... on RunsFeedConnection {
          results {
            __typename
            id
            runStatus
            creationTime
            startTime
            endTime
            jobName
            assetSelection {
                path
            }
            assetCheckSelection {
                name
            }
            tags {
                key
                value
            }
          }
          cursor
          hasMore
      }
      ... on PythonError {
        stack
        message
      }
    }
    runsFeedCountOrError(filter: $filter, includeRunsFromBackfills: $includeRunsFromBackfills) {
        ... on RunsFeedCount {
            count
        }
    }
}
"""

# when runs are inserted into the database, sqlite uses CURRENT_TIMESTAMP to set the creation time.
# CURRENT_TIMESTAMP only has second precision for sqlite, so if we create runs and backfills without any delay
# the resulting list is a chunk of runs and then a chunk of backfills when ordered by time. Adding a small
# delay between creating a run and a backfill makes the resulting list more interwoven
CREATE_DELAY = 1


def _create_run(graphql_context, **kwargs) -> DagsterRun:
    return create_run_for_test(instance=graphql_context.instance, **kwargs)


def _create_run_for_backfill(
    graphql_context, backfill_id: str, tags: Optional[Mapping[str, str]] = None, **kwargs
) -> DagsterRun:
    if tags:
        tags = {**tags, **DagsterRun.tags_for_backfill_id(backfill_id)}
    else:
        tags = DagsterRun.tags_for_backfill_id(backfill_id)
    return create_run_for_test(
        instance=graphql_context.instance,
        tags=tags,
        **kwargs,
    )


def _create_backfill(
    graphql_context,
    status: BulkActionStatus = BulkActionStatus.COMPLETED_SUCCESS,
    tags: Optional[Mapping[str, str]] = None,
    partition_set_origin: Optional[RemotePartitionSetOrigin] = None,
) -> str:
    serialized_backfill_data = (
        "foo" if partition_set_origin is None else None
    )  # the content of the backfill doesn't matter for testing fetching mega runs
    backfill = PartitionBackfill(
        backfill_id=make_new_backfill_id(),
        serialized_asset_backfill_data=serialized_backfill_data,
        status=status,
        reexecution_steps=None,
        tags=tags,
        backfill_timestamp=get_current_timestamp(),
        from_failure=False,
        partition_set_origin=partition_set_origin,
    )
    graphql_context.instance.add_backfill(backfill)
    return backfill.backfill_id


def _assert_results_match_count_match_expected(query_result, expected_count):
    assert len(query_result.data["runsFeedOrError"]["results"]) == expected_count
    assert query_result.data["runsFeedCountOrError"]["count"] == expected_count


class TestRunsFeedWithSharedSetup(ExecutingGraphQLContextTestMatrix):
    """Tests for the runs feed that can be done on a instance that has 10 runs and 10 backfills
    created in alternating order. Split these tests into a separate class so that we can make the runs
    and backfills once and re-use them across tests.
    """

    @pytest.fixture(scope="class")
    def gql_context_with_runs_and_backfills(self, class_scoped_graphql_context):
        for _ in range(10):
            _create_run(class_scoped_graphql_context)
            time.sleep(CREATE_DELAY)
            _create_backfill(class_scoped_graphql_context)

        return class_scoped_graphql_context

    def test_get_runs_feed(self, gql_context_with_runs_and_backfills):
        result = execute_dagster_graphql(
            gql_context_with_runs_and_backfills.create_request_context(),
            GET_RUNS_FEED_QUERY,
            variables={
                "limit": 25,
                "cursor": None,
                "filter": None,
                "includeRunsFromBackfills": False,
            },
        )
        _assert_results_match_count_match_expected(result, 20)
        prev_run_time = None
        for res in result.data["runsFeedOrError"]["results"]:
            if prev_run_time:
                assert res["creationTime"] <= prev_run_time
            prev_run_time = res["creationTime"]

        result = execute_dagster_graphql(
            gql_context_with_runs_and_backfills.create_request_context(),
            GET_RUNS_FEED_QUERY,
            variables={
                "limit": 10,
                "cursor": None,
                "filter": None,
                "includeRunsFromBackfills": False,
            },
        )

        assert not result.errors
        assert result.data
        # limit was used, count will differ from number of results returned
        assert len(result.data["runsFeedOrError"]["results"]) == 10

        prev_run_time = None
        for res in result.data["runsFeedOrError"]["results"]:
            if prev_run_time:
                assert res["creationTime"] <= prev_run_time
            prev_run_time = res["creationTime"]

        assert result.data["runsFeedOrError"]["hasMore"]
        old_cursor = result.data["runsFeedOrError"]["cursor"]
        assert old_cursor is not None

        result = execute_dagster_graphql(
            gql_context_with_runs_and_backfills.create_request_context(),
            GET_RUNS_FEED_QUERY,
            variables={
                "limit": 10,
                "cursor": old_cursor,
                "filter": None,
                "includeRunsFromBackfills": False,
            },
        )

        assert len(result.data["runsFeedOrError"]["results"]) == 10
        for res in result.data["runsFeedOrError"]["results"]:
            if prev_run_time:
                assert res["creationTime"] <= prev_run_time
            prev_run_time = res["creationTime"]

        assert not result.data["runsFeedOrError"]["hasMore"]

    def test_get_runs_feed_inexact_limit(self, gql_context_with_runs_and_backfills):
        result = execute_dagster_graphql(
            gql_context_with_runs_and_backfills.create_request_context(),
            GET_RUNS_FEED_QUERY,
            variables={
                "limit": 15,
                "cursor": None,
                "filter": None,
                "includeRunsFromBackfills": False,
            },
        )

        assert not result.errors
        assert result.data

        assert len(result.data["runsFeedOrError"]["results"]) == 15
        prev_run_time = None
        for res in result.data["runsFeedOrError"]["results"]:
            if prev_run_time:
                assert res["creationTime"] <= prev_run_time
            prev_run_time = res["creationTime"]

        assert result.data["runsFeedOrError"]["hasMore"]
        assert result.data["runsFeedOrError"]["cursor"] is not None

        result = execute_dagster_graphql(
            gql_context_with_runs_and_backfills.create_request_context(),
            GET_RUNS_FEED_QUERY,
            variables={
                "limit": 10,
                "cursor": result.data["runsFeedOrError"]["cursor"],
                "filter": None,
                "includeRunsFromBackfills": False,
            },
        )
        # limit was used, count will differ from number of results returned
        assert len(result.data["runsFeedOrError"]["results"]) == 5

        for res in result.data["runsFeedOrError"]["results"]:
            if prev_run_time:
                assert res["creationTime"] <= prev_run_time
            prev_run_time = res["creationTime"]

        assert not result.data["runsFeedOrError"]["hasMore"]

    def test_get_runs_feed_cursor_respected(self, gql_context_with_runs_and_backfills):
        result = execute_dagster_graphql(
            gql_context_with_runs_and_backfills.create_request_context(),
            GET_RUNS_FEED_QUERY,
            variables={
                "limit": 10,
                "cursor": None,
                "filter": None,
                "includeRunsFromBackfills": False,
            },
        )

        assert not result.errors
        assert result.data

        assert len(result.data["runsFeedOrError"]["results"]) == 10
        prev_run_time = None
        for res in result.data["runsFeedOrError"]["results"]:
            if prev_run_time:
                assert res["creationTime"] <= prev_run_time
            prev_run_time = res["creationTime"]

        assert result.data["runsFeedOrError"]["hasMore"]
        assert result.data["runsFeedOrError"]["cursor"] is not None

        old_cursor = RunsFeedCursor.from_string(result.data["runsFeedOrError"]["cursor"])
        run_cursor_run = gql_context_with_runs_and_backfills.instance.get_run_record_by_id(
            old_cursor.run_cursor
        )
        backfill_cursor_backfill = gql_context_with_runs_and_backfills.instance.get_backfill(
            old_cursor.backfill_cursor
        )

        result = execute_dagster_graphql(
            gql_context_with_runs_and_backfills.create_request_context(),
            GET_RUNS_FEED_QUERY,
            variables={
                "limit": 10,
                "cursor": old_cursor.to_string(),
                "filter": None,
                "includeRunsFromBackfills": False,
            },
        )

        assert len(result.data["runsFeedOrError"]["results"]) == 10
        for res in result.data["runsFeedOrError"]["results"]:
            if prev_run_time:
                assert res["creationTime"] <= prev_run_time
            prev_run_time = res["creationTime"]

            assert res["id"] != old_cursor.run_cursor
            assert res["id"] != old_cursor.backfill_cursor

            assert res["creationTime"] <= run_cursor_run.create_timestamp.timestamp()
            assert res["creationTime"] <= backfill_cursor_backfill.backfill_timestamp

        assert not result.data["runsFeedOrError"]["hasMore"]

    def test_get_runs_feed_with_subruns(self, gql_context_with_runs_and_backfills):
        result = execute_dagster_graphql(
            gql_context_with_runs_and_backfills.create_request_context(),
            GET_RUNS_FEED_QUERY,
            variables={
                "limit": 25,
                "cursor": None,
                "filter": None,
                "includeRunsFromBackfills": True,
            },
        )
        _assert_results_match_count_match_expected(result, 10)
        prev_run_time = None
        for res in result.data["runsFeedOrError"]["results"]:
            assert res["__typename"] == "Run"
            if prev_run_time:
                assert res["creationTime"] <= prev_run_time
            prev_run_time = res["creationTime"]

        result = execute_dagster_graphql(
            gql_context_with_runs_and_backfills.create_request_context(),
            GET_RUNS_FEED_QUERY,
            variables={
                "limit": 10,
                "cursor": None,
                "filter": None,
                "includeRunsFromBackfills": True,
            },
        )

        assert not result.errors
        assert result.data

        assert len(result.data["runsFeedOrError"]["results"]) == 10
        prev_run_time = None
        for res in result.data["runsFeedOrError"]["results"]:
            assert res["__typename"] == "Run"
            if prev_run_time:
                assert res["creationTime"] <= prev_run_time
            prev_run_time = res["creationTime"]

        assert not result.data["runsFeedOrError"]["hasMore"]

        result = execute_dagster_graphql(
            gql_context_with_runs_and_backfills.create_request_context(),
            GET_RUNS_FEED_QUERY,
            variables={
                "limit": 5,
                "cursor": None,
                "filter": None,
                "includeRunsFromBackfills": True,
            },
        )

        assert not result.errors
        assert result.data

        assert len(result.data["runsFeedOrError"]["results"]) == 5
        prev_run_time = None
        for res in result.data["runsFeedOrError"]["results"]:
            assert res["__typename"] == "Run"
            if prev_run_time:
                assert res["creationTime"] <= prev_run_time
            prev_run_time = res["creationTime"]

        assert result.data["runsFeedOrError"]["hasMore"]
        old_cursor = result.data["runsFeedOrError"]["cursor"]
        assert old_cursor is not None

        result = execute_dagster_graphql(
            gql_context_with_runs_and_backfills.create_request_context(),
            GET_RUNS_FEED_QUERY,
            variables={
                "limit": 5,
                "cursor": old_cursor,
                "filter": None,
                "includeRunsFromBackfills": True,
            },
        )

        assert len(result.data["runsFeedOrError"]["results"]) == 5
        for res in result.data["runsFeedOrError"]["results"]:
            assert res["__typename"] == "Run"
            if prev_run_time:
                assert res["creationTime"] <= prev_run_time
            prev_run_time = res["creationTime"]

        assert not result.data["runsFeedOrError"]["hasMore"]


class TestRunsFeedUniqueSetups(ExecutingGraphQLContextTestMatrix):
    """Tests for the runs feed that need special ordering of runs and backfills. Split these
    out from the tests that can use a consistent setup because fetching the graphql_context per
    test wipes the run storage, so is incompatible to use with the class-scoped context needed for
    the other test suite.
    """

    def supports_filtering(self):
        return True

    def test_get_runs_feed_ignores_backfill_runs(self, graphql_context):
        for _ in range(10):
            _create_run_for_backfill(graphql_context, backfill_id="foo")
            time.sleep(CREATE_DELAY)
            _create_backfill(graphql_context)

        result = execute_dagster_graphql(
            graphql_context,
            GET_RUNS_FEED_QUERY,
            variables={
                "limit": 10,
                "cursor": None,
                "filter": None,
                "includeRunsFromBackfills": False,
            },
        )

        assert not result.errors
        assert result.data

        _assert_results_match_count_match_expected(result, 10)
        prev_run_time = None
        for res in result.data["runsFeedOrError"]["results"]:
            if prev_run_time:
                assert res["creationTime"] <= prev_run_time
            prev_run_time = res["creationTime"]
            assert res["__typename"] == "PartitionBackfill"

        assert not result.data["runsFeedOrError"]["hasMore"]

    def test_get_runs_feed_no_runs_or_backfills_exist(self, graphql_context):
        result = execute_dagster_graphql(
            graphql_context,
            GET_RUNS_FEED_QUERY,
            variables={
                "limit": 10,
                "cursor": None,
                "filter": None,
                "includeRunsFromBackfills": False,
            },
        )

        assert not result.errors
        assert result.data

        _assert_results_match_count_match_expected(result, 0)
        assert not result.data["runsFeedOrError"]["hasMore"]

    def test_get_runs_feed_one_backfill_long_ago(self, graphql_context):
        backfill_id = _create_backfill(graphql_context)
        time.sleep(1)  # to ensure that all runs are more recent than the backfill
        for _ in range(15):
            _create_run(graphql_context)

        result = execute_dagster_graphql(
            graphql_context,
            GET_RUNS_FEED_QUERY,
            variables={
                "limit": 10,
                "cursor": None,
                "filter": None,
                "includeRunsFromBackfills": False,
            },
        )

        assert not result.errors
        assert result.data

        assert len(result.data["runsFeedOrError"]["results"]) == 10
        prev_run_time = None
        for res in result.data["runsFeedOrError"]["results"]:
            if prev_run_time:
                assert res["creationTime"] <= prev_run_time
            prev_run_time = res["creationTime"]

            # first 10 results should all be runs
            assert res["__typename"] == "Run"

        assert result.data["runsFeedOrError"]["hasMore"]
        assert result.data["runsFeedOrError"]["cursor"] is not None
        # no backfills have been returned yet, so backfill cursor should be None
        assert (
            RunsFeedCursor.from_string(result.data["runsFeedOrError"]["cursor"]).backfill_cursor
            is None
        )

        result = execute_dagster_graphql(
            graphql_context,
            GET_RUNS_FEED_QUERY,
            variables={
                "limit": 10,
                "cursor": result.data["runsFeedOrError"]["cursor"],
                "filter": None,
                "includeRunsFromBackfills": False,
            },
        )

        assert len(result.data["runsFeedOrError"]["results"]) == 6
        for res in result.data["runsFeedOrError"]["results"]:
            if prev_run_time:
                assert res["creationTime"] <= prev_run_time
            prev_run_time = res["creationTime"]

        assert not result.data["runsFeedOrError"]["hasMore"]
        assert result.data["runsFeedOrError"]["cursor"] is not None
        assert (
            RunsFeedCursor.from_string(result.data["runsFeedOrError"]["cursor"]).backfill_cursor
            == backfill_id
        )

    def test_get_runs_feed_one_new_backfill(self, graphql_context):
        for _ in range(15):
            _create_run(graphql_context)

        time.sleep(1)  # to ensure that all runs are older than the backfill
        backfill_id = _create_backfill(graphql_context)

        result = execute_dagster_graphql(
            graphql_context,
            GET_RUNS_FEED_QUERY,
            variables={
                "limit": 10,
                "cursor": None,
                "filter": None,
                "includeRunsFromBackfills": False,
            },
        )

        assert not result.errors
        assert result.data

        assert len(result.data["runsFeedOrError"]["results"]) == 10
        prev_run_time = None
        for res in result.data["runsFeedOrError"]["results"]:
            if prev_run_time:
                assert res["creationTime"] <= prev_run_time
            prev_run_time = res["creationTime"]

        assert result.data["runsFeedOrError"]["hasMore"]
        assert result.data["runsFeedOrError"]["cursor"] is not None
        assert (
            RunsFeedCursor.from_string(result.data["runsFeedOrError"]["cursor"]).backfill_cursor
            == backfill_id
        )

        result = execute_dagster_graphql(
            graphql_context,
            GET_RUNS_FEED_QUERY,
            variables={
                "limit": 10,
                "cursor": result.data["runsFeedOrError"]["cursor"],
                "filter": None,
                "includeRunsFromBackfills": False,
            },
        )

        assert len(result.data["runsFeedOrError"]["results"]) == 6
        for res in result.data["runsFeedOrError"]["results"]:
            if prev_run_time:
                assert res["creationTime"] <= prev_run_time
            prev_run_time = res["creationTime"]

            # all remaining results should be runs
            assert res["__typename"] == "Run"

        assert not result.data["runsFeedOrError"]["hasMore"]
        assert result.data["runsFeedOrError"]["cursor"] is not None
        # even though no backfill was returned, the cursor should point to the backfill that was returned by the previous call
        assert (
            RunsFeedCursor.from_string(result.data["runsFeedOrError"]["cursor"]).backfill_cursor
            == backfill_id
        )

    def test_get_runs_feed_backfill_created_between_calls(self, graphql_context):
        for _ in range(10):
            _create_run(graphql_context)

        result = execute_dagster_graphql(
            graphql_context,
            GET_RUNS_FEED_QUERY,
            variables={
                "limit": 5,
                "cursor": None,
                "filter": None,
                "includeRunsFromBackfills": False,
            },
        )

        assert not result.errors
        assert result.data

        assert len(result.data["runsFeedOrError"]["results"]) == 5
        prev_run_time = None
        for res in result.data["runsFeedOrError"]["results"]:
            if prev_run_time:
                assert res["creationTime"] <= prev_run_time
            prev_run_time = res["creationTime"]

        assert result.data["runsFeedOrError"]["hasMore"]
        assert result.data["runsFeedOrError"]["cursor"] is not None
        assert (
            RunsFeedCursor.from_string(result.data["runsFeedOrError"]["cursor"]).backfill_cursor
            is None
        )

        # create a backfill before the next call
        _create_backfill(graphql_context)

        # the next page of the Runs Feed should not include the newly created backfill, since that would
        # be out of time order with the previous page
        result = execute_dagster_graphql(
            graphql_context,
            GET_RUNS_FEED_QUERY,
            variables={
                "limit": 10,
                "cursor": result.data["runsFeedOrError"]["cursor"],
                "filter": None,
                "includeRunsFromBackfills": False,
            },
        )

        assert len(result.data["runsFeedOrError"]["results"]) == 5
        for res in result.data["runsFeedOrError"]["results"]:
            if prev_run_time:
                assert res["creationTime"] <= prev_run_time
            prev_run_time = res["creationTime"]

            assert res["__typename"] == "Run"

        assert not result.data["runsFeedOrError"]["hasMore"]
        assert result.data["runsFeedOrError"]["cursor"] is not None
        assert (
            RunsFeedCursor.from_string(result.data["runsFeedOrError"]["cursor"]).backfill_cursor
            is None
        )

    def test_get_runs_feed_filter_status(self, graphql_context):
        _create_run(graphql_context, status=DagsterRunStatus.SUCCESS)
        _create_run(graphql_context, status=DagsterRunStatus.CANCELING)
        _create_run(graphql_context, status=DagsterRunStatus.FAILURE)
        _create_run(graphql_context, status=DagsterRunStatus.NOT_STARTED)
        time.sleep(CREATE_DELAY)
        _create_backfill(graphql_context, status=BulkActionStatus.COMPLETED_SUCCESS)
        _create_backfill(graphql_context, status=BulkActionStatus.COMPLETED_FAILED)
        _create_backfill(graphql_context, status=BulkActionStatus.COMPLETED)
        _create_backfill(graphql_context, status=BulkActionStatus.CANCELING)
        _create_backfill(graphql_context, status=BulkActionStatus.CANCELED)

        result = execute_dagster_graphql(
            graphql_context,
            GET_RUNS_FEED_QUERY,
            variables={
                "limit": 10,
                "cursor": None,
                "filter": None,
                "includeRunsFromBackfills": False,
            },
        )

        assert not result.errors
        assert result.data

        _assert_results_match_count_match_expected(result, 9)
        assert not result.data["runsFeedOrError"]["hasMore"]

        result = execute_dagster_graphql(
            graphql_context,
            GET_RUNS_FEED_QUERY,
            variables={
                "limit": 10,
                "cursor": None,
                "filter": {"statuses": ["SUCCESS"]},
                "includeRunsFromBackfills": False,
            },
        )
        assert not result.errors
        assert result.data
        _assert_results_match_count_match_expected(result, 2)

        result = execute_dagster_graphql(
            graphql_context,
            GET_RUNS_FEED_QUERY,
            variables={
                "limit": 10,
                "cursor": None,
                "filter": {"statuses": ["FAILURE"]},
                "includeRunsFromBackfills": False,
            },
        )
        assert not result.errors
        assert result.data
        _assert_results_match_count_match_expected(result, 2)

        result = execute_dagster_graphql(
            graphql_context,
            GET_RUNS_FEED_QUERY,
            variables={
                "limit": 10,
                "cursor": None,
                "filter": {"statuses": ["CANCELING"]},
                "includeRunsFromBackfills": False,
            },
        )
        assert not result.errors
        assert result.data
        _assert_results_match_count_match_expected(result, 2)

        result = execute_dagster_graphql(
            graphql_context,
            GET_RUNS_FEED_QUERY,
            variables={
                "limit": 10,
                "cursor": None,
                "filter": {"statuses": ["CANCELED"]},
                "includeRunsFromBackfills": False,
            },
        )
        assert not result.errors
        assert result.data
        _assert_results_match_count_match_expected(result, 1)

        result = execute_dagster_graphql(
            graphql_context,
            GET_RUNS_FEED_QUERY,
            variables={
                "limit": 10,
                "cursor": None,
                "filter": {"statuses": ["NOT_STARTED"]},
                "includeRunsFromBackfills": False,
            },
        )
        assert not result.errors
        assert result.data
        _assert_results_match_count_match_expected(result, 1)

    def test_get_runs_feed_filter_status_and_show_subruns(self, graphql_context):
        _create_run(graphql_context, status=DagsterRunStatus.SUCCESS)
        _create_run(graphql_context, status=DagsterRunStatus.CANCELING)
        _create_run(graphql_context, status=DagsterRunStatus.FAILURE)
        _create_run(graphql_context, status=DagsterRunStatus.NOT_STARTED)
        time.sleep(CREATE_DELAY)
        _create_backfill(graphql_context, status=BulkActionStatus.COMPLETED_SUCCESS)
        _create_backfill(graphql_context, status=BulkActionStatus.COMPLETED_FAILED)
        _create_backfill(graphql_context, status=BulkActionStatus.COMPLETED)
        _create_backfill(graphql_context, status=BulkActionStatus.CANCELING)
        _create_backfill(graphql_context, status=BulkActionStatus.CANCELED)

        result = execute_dagster_graphql(
            graphql_context,
            GET_RUNS_FEED_QUERY,
            variables={
                "limit": 10,
                "cursor": None,
                "filter": None,
                "includeRunsFromBackfills": True,
            },
        )

        assert not result.errors
        assert result.data

        _assert_results_match_count_match_expected(result, 4)
        assert not result.data["runsFeedOrError"]["hasMore"]

        result = execute_dagster_graphql(
            graphql_context,
            GET_RUNS_FEED_QUERY,
            variables={
                "limit": 10,
                "cursor": None,
                "filter": {"statuses": ["SUCCESS"]},
                "includeRunsFromBackfills": True,
            },
        )
        assert not result.errors
        assert result.data
        _assert_results_match_count_match_expected(result, 1)

        result = execute_dagster_graphql(
            graphql_context,
            GET_RUNS_FEED_QUERY,
            variables={
                "limit": 10,
                "cursor": None,
                "filter": {"statuses": ["FAILURE"]},
                "includeRunsFromBackfills": True,
            },
        )
        assert not result.errors
        assert result.data
        _assert_results_match_count_match_expected(result, 1)

        result = execute_dagster_graphql(
            graphql_context,
            GET_RUNS_FEED_QUERY,
            variables={
                "limit": 10,
                "cursor": None,
                "filter": {"statuses": ["CANCELING"]},
                "includeRunsFromBackfills": True,
            },
        )
        assert not result.errors
        assert result.data
        _assert_results_match_count_match_expected(result, 1)

        result = execute_dagster_graphql(
            graphql_context,
            GET_RUNS_FEED_QUERY,
            variables={
                "limit": 10,
                "cursor": None,
                "filter": {"statuses": ["CANCELED"]},
                "includeRunsFromBackfills": True,
            },
        )
        assert not result.errors
        assert result.data
        _assert_results_match_count_match_expected(result, 0)

    def test_get_runs_feed_filter_create_time(self, graphql_context):
        nothing_created_ts = get_current_timestamp()
        time.sleep(CREATE_DELAY)
        for _ in range(5):
            _create_run(graphql_context)
            time.sleep(CREATE_DELAY)
            _create_backfill(graphql_context)

        time.sleep(CREATE_DELAY)
        half_created_ts = get_current_timestamp()
        time.sleep(CREATE_DELAY)
        for _ in range(5):
            _create_run(graphql_context)
            time.sleep(CREATE_DELAY)
            _create_backfill(graphql_context)

        time.sleep(CREATE_DELAY)
        all_created_ts = get_current_timestamp()

        result = execute_dagster_graphql(
            graphql_context,
            GET_RUNS_FEED_QUERY,
            variables={
                "limit": 25,
                "cursor": None,
                "filter": None,
                "includeRunsFromBackfills": False,
            },
        )

        assert not result.errors
        assert result.data

        _assert_results_match_count_match_expected(result, 20)
        assert not result.data["runsFeedOrError"]["hasMore"]

        result = execute_dagster_graphql(
            graphql_context,
            GET_RUNS_FEED_QUERY,
            variables={
                "limit": 25,
                "cursor": None,
                "filter": {"createdBefore": nothing_created_ts},
                "includeRunsFromBackfills": False,
            },
        )
        assert not result.errors
        assert result.data
        _assert_results_match_count_match_expected(result, 0)
        assert not result.data["runsFeedOrError"]["hasMore"]

        result = execute_dagster_graphql(
            graphql_context,
            GET_RUNS_FEED_QUERY,
            variables={
                "limit": 25,
                "cursor": None,
                "filter": {"createdBefore": half_created_ts},
                "includeRunsFromBackfills": False,
            },
        )
        assert not result.errors
        assert result.data
        _assert_results_match_count_match_expected(result, 10)
        assert not result.data["runsFeedOrError"]["hasMore"]

        result = execute_dagster_graphql(
            graphql_context,
            GET_RUNS_FEED_QUERY,
            variables={
                "limit": 25,
                "cursor": None,
                "filter": {"createdBefore": all_created_ts},
                "includeRunsFromBackfills": False,
            },
        )
        assert not result.errors
        assert result.data
        _assert_results_match_count_match_expected(result, 20)
        assert not result.data["runsFeedOrError"]["hasMore"]

        # ensure the cursor overrides the createdBefore filter when the query is called multiple times for
        # pagination
        result = execute_dagster_graphql(
            graphql_context,
            GET_RUNS_FEED_QUERY,
            variables={
                "limit": 6,
                "cursor": None,
                "filter": {"createdBefore": half_created_ts},
                "includeRunsFromBackfills": False,
            },
        )
        assert not result.errors
        assert result.data
        assert len(result.data["runsFeedOrError"]["results"]) == 6
        assert result.data["runsFeedOrError"]["hasMore"]

        result = execute_dagster_graphql(
            graphql_context,
            GET_RUNS_FEED_QUERY,
            variables={
                "limit": 4,
                "cursor": result.data["runsFeedOrError"]["cursor"],
                "filter": {"createdBefore": half_created_ts},
                "includeRunsFromBackfills": False,
            },
        )
        assert not result.errors
        assert result.data
        assert len(result.data["runsFeedOrError"]["results"]) == 4
        assert not result.data["runsFeedOrError"]["hasMore"]

    def test_get_runs_feed_filter_job_name(self, graphql_context):
        if not self.supports_filtering():
            return pytest.skip("storage does not support filtering backfills by job_name")
        code_location = graphql_context.get_code_location("test")
        repository = code_location.get_repository("test_repo")

        partition_set_origin = RemotePartitionSetOrigin(
            repository_origin=repository.get_remote_origin(),
            partition_set_name="foo_partition",
        )
        for _ in range(3):
            _create_run(graphql_context, job_name="foo")
            time.sleep(CREATE_DELAY)
            backfill_id = _create_backfill(
                graphql_context, partition_set_origin=partition_set_origin
            )
            _create_run_for_backfill(graphql_context, backfill_id, job_name="foo")

        partition_set_origin = RemotePartitionSetOrigin(
            repository_origin=repository.get_remote_origin(),
            partition_set_name="bar_partition",
        )
        for _ in range(3):
            _create_run(graphql_context, job_name="bar")
            time.sleep(CREATE_DELAY)
            backfill_id = _create_backfill(
                graphql_context, partition_set_origin=partition_set_origin
            )
            _create_run_for_backfill(graphql_context, backfill_id, job_name="bar")

        result = execute_dagster_graphql(
            graphql_context,
            GET_RUNS_FEED_QUERY,
            variables={
                "limit": 20,
                "cursor": None,
                "filter": None,
                "includeRunsFromBackfills": False,
            },
        )

        assert not result.errors
        assert result.data

        _assert_results_match_count_match_expected(result, 12)
        assert not result.data["runsFeedOrError"]["hasMore"]

        result = execute_dagster_graphql(
            graphql_context,
            GET_RUNS_FEED_QUERY,
            variables={
                "limit": 10,
                "cursor": None,
                "filter": {"pipelineName": "foo"},
                "includeRunsFromBackfills": False,
            },
        )
        assert not result.errors
        assert result.data
        _assert_results_match_count_match_expected(result, 6)

        result = execute_dagster_graphql(
            graphql_context,
            GET_RUNS_FEED_QUERY,
            variables={
                "limit": 10,
                "cursor": None,
                "filter": {"pipelineName": "bar"},
                "includeRunsFromBackfills": False,
            },
        )
        assert not result.errors
        assert result.data
        _assert_results_match_count_match_expected(result, 6)

    def test_get_runs_feed_filter_tags(self, graphql_context):
        if not self.supports_filtering():
            return pytest.skip("storage does not support filtering backfills by tag")
        for _ in range(3):
            _create_run(graphql_context, tags={"foo": "bar"})
            time.sleep(CREATE_DELAY)
            backfill_id = _create_backfill(graphql_context, tags={"foo": "bar"})
            _create_run_for_backfill(
                graphql_context, backfill_id, tags={"foo": "bar", "baz": "quux"}
            )

        for _ in range(3):
            _create_run(graphql_context, tags={"foo": "baz"})
            time.sleep(CREATE_DELAY)
            backfill_id = _create_backfill(graphql_context, tags={"one": "two"})
            _create_run_for_backfill(graphql_context, backfill_id, tags={"one": "two"})

        result = execute_dagster_graphql(
            graphql_context,
            GET_RUNS_FEED_QUERY,
            variables={
                "limit": 20,
                "cursor": None,
                "filter": None,
                "includeRunsFromBackfills": False,
            },
        )

        assert not result.errors
        assert result.data

        _assert_results_match_count_match_expected(result, 12)
        assert not result.data["runsFeedOrError"]["hasMore"]

        result = execute_dagster_graphql(
            graphql_context,
            GET_RUNS_FEED_QUERY,
            variables={
                "limit": 10,
                "cursor": None,
                "filter": {"tags": [{"key": "foo", "value": "bar"}]},
                "includeRunsFromBackfills": False,
            },
        )
        assert not result.errors
        assert result.data
        _assert_results_match_count_match_expected(result, 6)

        # filtering for tags that are only on sub-runs of backfills should not return the backfill
        result = execute_dagster_graphql(
            graphql_context,
            GET_RUNS_FEED_QUERY,
            variables={
                "limit": 10,
                "cursor": None,
                "filter": {"tags": [{"key": "baz", "value": "quux"}]},
                "includeRunsFromBackfills": False,
            },
        )
        assert not result.errors
        assert result.data
        _assert_results_match_count_match_expected(result, 0)

        result = execute_dagster_graphql(
            graphql_context,
            GET_RUNS_FEED_QUERY,
            variables={
                "limit": 10,
                "cursor": None,
                "filter": {"tags": [{"key": "foo", "value": "baz"}]},
                "includeRunsFromBackfills": False,
            },
        )
        assert not result.errors
        assert result.data
        _assert_results_match_count_match_expected(result, 3)

    def test_get_runs_feed_filters_that_dont_apply_to_backfills(self, graphql_context):
        run = _create_run(graphql_context)
        time.sleep(CREATE_DELAY)
        _create_backfill(graphql_context)

        result = execute_dagster_graphql(
            graphql_context,
            GET_RUNS_FEED_QUERY,
            variables={
                "limit": 20,
                "cursor": None,
                "filter": None,
                "includeRunsFromBackfills": False,
            },
        )

        assert not result.errors
        assert result.data

        _assert_results_match_count_match_expected(result, 2)
        assert not result.data["runsFeedOrError"]["hasMore"]

        result = execute_dagster_graphql(
            graphql_context,
            GET_RUNS_FEED_QUERY,
            variables={
                "limit": 10,
                "cursor": None,
                "filter": {"runIds": [run.run_id]},
                "includeRunsFromBackfills": False,
            },
        )
        assert not result.errors
        assert result.data
        _assert_results_match_count_match_expected(result, 1)

    def test_get_runs_feed_filters_that_dont_apply_to_backfills_and_show_subruns(
        self, graphql_context
    ):
        run = _create_run(graphql_context)
        time.sleep(CREATE_DELAY)
        _create_backfill(graphql_context)

        result = execute_dagster_graphql(
            graphql_context,
            GET_RUNS_FEED_QUERY,
            variables={
                "limit": 20,
                "cursor": None,
                "filter": None,
                "includeRunsFromBackfills": True,
            },
        )

        assert not result.errors
        assert result.data

        _assert_results_match_count_match_expected(result, 1)
        assert not result.data["runsFeedOrError"]["hasMore"]

        result = execute_dagster_graphql(
            graphql_context,
            GET_RUNS_FEED_QUERY,
            variables={
                "limit": 10,
                "cursor": None,
                "filter": {"runIds": [run.run_id]},
                "includeRunsFromBackfills": True,
            },
        )
        assert not result.errors
        assert result.data
        _assert_results_match_count_match_expected(result, 1)

    def test_get_runs_feed_filter_tags_and_status(self, graphql_context):
        if not self.supports_filtering():
            return pytest.skip("storage does not support filtering backfills by tag")
        run_statuses = [
            DagsterRunStatus.SUCCESS,
            DagsterRunStatus.FAILURE,
            DagsterRunStatus.CANCELED,
        ]
        backfill_statuses = [
            BulkActionStatus.COMPLETED_SUCCESS,
            BulkActionStatus.COMPLETED_FAILED,
            BulkActionStatus.CANCELED,
        ]
        for i in range(3):
            _create_run(graphql_context, tags={"foo": "bar"}, status=run_statuses[i])
            time.sleep(CREATE_DELAY)
            backfill_id = _create_backfill(
                graphql_context, tags={"foo": "bar"}, status=backfill_statuses[i]
            )
            _create_run_for_backfill(
                graphql_context,
                backfill_id,
                tags={"foo": "bar", "baz": "quux"},
                status=run_statuses[i],
            )

        for i in range(3):
            _create_run(graphql_context, tags={"foo": "baz"}, status=run_statuses[i])
            time.sleep(CREATE_DELAY)
            backfill_id = _create_backfill(
                graphql_context, tags={"one": "two"}, status=backfill_statuses[i]
            )
            _create_run_for_backfill(
                graphql_context, backfill_id, tags={"one": "two"}, status=run_statuses[i]
            )

        result = execute_dagster_graphql(
            graphql_context,
            GET_RUNS_FEED_QUERY,
            variables={
                "limit": 20,
                "cursor": None,
                "filter": None,
                "includeRunsFromBackfills": False,
            },
        )

        assert not result.errors
        assert result.data

        _assert_results_match_count_match_expected(result, 12)
        assert not result.data["runsFeedOrError"]["hasMore"]

        result = execute_dagster_graphql(
            graphql_context,
            GET_RUNS_FEED_QUERY,
            variables={
                "limit": 10,
                "cursor": None,
                "filter": {"tags": [{"key": "foo", "value": "bar"}], "statuses": ["SUCCESS"]},
                "includeRunsFromBackfills": False,
            },
        )
        assert not result.errors
        assert result.data
        _assert_results_match_count_match_expected(result, 2)

        result = execute_dagster_graphql(
            graphql_context,
            GET_RUNS_FEED_QUERY,
            variables={
                "limit": 10,
                "cursor": None,
                "filter": {
                    "tags": [{"key": "foo", "value": "bar"}],
                    "statuses": ["FAILURE", "CANCELED"],
                },
                "includeRunsFromBackfills": False,
            },
        )
        assert not result.errors
        assert result.data
        _assert_results_match_count_match_expected(result, 4)

        result = execute_dagster_graphql(
            graphql_context,
            GET_RUNS_FEED_QUERY,
            variables={
                "limit": 10,
                "cursor": None,
                "filter": {"tags": [{"key": "foo", "value": "baz"}], "statuses": ["FAILURE"]},
                "includeRunsFromBackfills": False,
            },
        )
        assert not result.errors
        assert result.data
        _assert_results_match_count_match_expected(result, 1)

    def test_get_backfill_id_filter(self, graphql_context):
        backfill_id = _create_backfill(graphql_context)
        _create_run_for_backfill(graphql_context, backfill_id)
        _create_run_for_backfill(graphql_context, backfill_id)
        _create_run_for_backfill(graphql_context, backfill_id)

        result = execute_dagster_graphql(
            graphql_context,
            GET_RUNS_FEED_QUERY,
            variables={
                "limit": 20,
                "cursor": None,
                "filter": None,
                "includeRunsFromBackfills": False,
            },
        )

        assert not result.errors
        assert result.data
        assert len(result.data["runsFeedOrError"]["results"]) == 1
        assert not result.data["runsFeedOrError"]["hasMore"]

        result = execute_dagster_graphql(
            graphql_context,
            GET_RUNS_FEED_QUERY,
            variables={
                "limit": 10,
                "cursor": None,
                "filter": {"tags": [{"key": BACKFILL_ID_TAG, "value": backfill_id}]},
                "includeRunsFromBackfills": False,
            },
        )
        assert not result.errors
        assert result.data
        assert len(result.data["runsFeedOrError"]["results"]) == 1

        assert result.data["runsFeedOrError"]["results"][0]["__typename"] == "PartitionBackfill"
        assert result.data["runsFeedOrError"]["results"][0]["id"] == backfill_id

        result = execute_dagster_graphql(
            graphql_context,
            GET_RUNS_FEED_QUERY,
            variables={
                "limit": 10,
                "cursor": None,
                "filter": {
                    "tags": [
                        {"key": BACKFILL_ID_TAG, "value": backfill_id},
                        {"key": "not", "value": "present"},
                    ]
                },
                "includeRunsFromBackfills": False,
            },
        )
        assert not result.errors
        assert result.data
        _assert_results_match_count_match_expected(result, 0)
