"""general test structure:
seed some runs and backfills
ensure that the get megaruns function returns the expected results

things to test

respects limit
ordering is correct
cursors are respected
runs in a backfill are ignored
no runs or backfills are created
not enough runs/backfills for limit
1 run and a bunch of backfills and vis versa.
"""

import time

from dagster._core.execution.backfill import BulkActionStatus, PartitionBackfill
from dagster._core.storage.dagster_run import DagsterRun
from dagster._core.test_utils import create_run_for_test
from dagster._core.utils import make_new_backfill_id
from dagster._time import get_current_timestamp
from dagster_graphql.test.utils import execute_dagster_graphql

from dagster_graphql_tests.graphql.graphql_context_test_suite import (
    ExecutingGraphQLContextTestMatrix,
)

GET_MEGA_RUNS_QUERY = """
query MegaRunsQuery($cursor: String, $limit: Int!) {
    megaRunsOrError(cursor: $cursor, limit: $limit) {
      ... on MegaRuns {
        results {
          runId
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
      }
      ... on PythonError {
        stack
        message
      }
    }
}

"""


def _create_run(graphql_context) -> DagsterRun:
    return create_run_for_test(
        instance=graphql_context.instance,
    )


def _create_run_for_backfill(graphql_context, backfill_id: str) -> DagsterRun:
    return create_run_for_test(
        instance=graphql_context.instance,
        tags={
            **DagsterRun.tags_for_backfill_id(backfill_id),
        },
    )


def _create_backfill(graphql_context) -> str:
    backfill = PartitionBackfill(
        backfill_id=make_new_backfill_id(),
        serialized_asset_backfill_data="foo",  # the content of the backfill doesn't matter for testing fetching mega runs
        status=BulkActionStatus.COMPLETED,
        reexecution_steps=None,
        tags=None,
        backfill_timestamp=get_current_timestamp(),  # truncate to an integer to make the ordering deterministic since the runs db is in ints
        from_failure=False,
    )
    graphql_context.instance.add_backfill(backfill)
    return backfill.backfill_id


class TestMegaRuns(ExecutingGraphQLContextTestMatrix):
    def test_get_mega_runs(self, graphql_context):
        # seed some runs and backfills in an alternating order
        for _ in range(10):
            _create_run(graphql_context)
            time.sleep(1)
            _create_backfill(graphql_context)

        result = execute_dagster_graphql(
            graphql_context,
            GET_MEGA_RUNS_QUERY,
            variables={
                "limit": 10,
                "cursor": None,
            },
        )

        assert not result.errors
        assert result.data

        assert len(result.data["megaRunsOrError"]["results"]) == 10
        prev_run_time = None
        for res in result.data["megaRunsOrError"]["results"]:
            if prev_run_time:
                assert res["creationTime"] <= prev_run_time
            prev_run_time = res["creationTime"]
