import copy
import tempfile
import time

import pytest
import yaml
from dagster import AssetMaterialization, Output, define_asset_job, job, op, repository
from dagster._core.definitions.decorators.asset_decorator import asset
from dagster._core.definitions.dependency import NodeHandle
from dagster._core.definitions.events import AssetObservation
from dagster._core.definitions.job_base import InMemoryJob
from dagster._core.events import DagsterEvent, DagsterEventType
from dagster._core.events.log import EventLogEntry
from dagster._core.execution.api import execute_run
from dagster._core.execution.plan.handle import StepHandle
from dagster._core.storage.dagster_run import DagsterRunStatus
from dagster._core.storage.tags import PARENT_RUN_ID_TAG, ROOT_RUN_ID_TAG
from dagster._core.test_utils import instance_for_test
from dagster._core.workspace.context import WorkspaceRequestContext
from dagster._utils import Counter, traced_counter
from dagster_graphql.test.utils import (
    define_out_of_process_context,
    execute_dagster_graphql,
    infer_job_selector,
)

from dagster_graphql_tests.graphql.graphql_context_test_suite import (
    ExecutingGraphQLContextTestMatrix,
    ReadonlyGraphQLContextTestMatrix,
)

RUNS_QUERY = """
query PipelineRunsRootQuery($selector: PipelineSelector!) {
  pipelineOrError(params: $selector) {
    ... on Pipeline {
      name
      pipelineSnapshotId
      runs {
        ...RunHistoryRunFragment
      }
    }
  }
}

fragment RunHistoryRunFragment on PipelineRun {
  runId
  status
  repositoryOrigin {
    repositoryLocationName
    repositoryName
    repositoryLocationMetadata {
      key
      value
    }
  }
  pipeline {
    ...on PipelineReference { name }
  }
  executionPlan {
    steps {
      key
    }
  }
  runConfig
  runConfigYaml
  mode
  canTerminate
  tags {
    key
    value
  }
}
"""

DELETE_RUN_MUTATION = """
mutation DeleteRun($runId: String!) {
  deletePipelineRun(runId: $runId) {
    __typename
    ... on DeletePipelineRunSuccess {
      runId
    }
    ... on PythonError {
      message
    }
  }
}
"""

ALL_TAG_KEYS_QUERY = """
{
  runTagKeysOrError {
    __typename
    ... on RunTagKeys {
      keys
    }
    ... on PythonError {
        message
        stack
    }
  }
}
"""

FILTERED_TAGS_QUERY = """
query FilteredRunTagsQuery($tagKeys: [String!]!) {
  runTagsOrError(tagKeys: $tagKeys) {
    ... on RunTags {
      tags {
        key
        values
      }
    }
  }
}
"""


ALL_RUNS_QUERY = """
{
  pipelineRunsOrError {
    ... on PipelineRuns {
      results {
        runId
        pipelineSnapshotId
        pipeline {
          __typename
          ... on PipelineReference {
            name
            solidSelection
          }
        }
      }
    }
  }
}
"""


FILTERED_RUN_QUERY = """
query PipelineRunsRootQuery($filter: RunsFilter!) {
  pipelineRunsOrError(filter: $filter) {
    ... on PipelineRuns {
      results {
        runId
        hasReExecutePermission
        hasTerminatePermission
        hasDeletePermission
      }
    }
  }
}
"""

RUN_IDS_QUERY = """
query RunIds($filter: RunsFilter, $cursor: String, $limit: Int) {
  runIdsOrError(filter: $filter, cursor: $cursor, limit: $limit) {
    ... on RunIds {
      results
    }
  }
}
"""

FILTERED_RUN_COUNT_QUERY = """
query PipelineRunsRootQuery($filter: RunsFilter!) {
  pipelineRunsOrError(filter: $filter) {
    ... on PipelineRuns {
      count
    }
  }
}
"""


RUN_GROUP_QUERY = """
query RunGroupQuery($runId: ID!) {
  runGroupOrError(runId: $runId) {
    ... on RunGroup {
      __typename
      rootRunId
      runs {
        runId
        pipeline {
          __typename
          ... on PipelineReference {
            name
          }
        }
      }
    }
    ... on RunGroupNotFoundError {
      __typename
      runId
      message
    }
  }
}
"""


REPOSITORY_RUNS_QUERY = """
query RepositoryRunsQuery($repositorySelector: RepositorySelector!) {
    repositoryOrError(repositorySelector: $repositorySelector) {
        ... on Repository {
            id
            name
            pipelines {
                id
                name
                runs(limit: 10) {
                    id
                    runId
                }
            }
        }
    }
}
"""

ASSET_RUNS_QUERY = """
query AssetRunsQuery($assetKey: AssetKeyInput!) {
    assetOrError(assetKey: $assetKey) {
        ... on Asset {
            assetMaterializations {
                label
                runOrError {
                    ... on PipelineRun {
                        id
                        runId
                    }
                }
            }
        }
    }
}
"""

RUN_ASSETS_QUERY = """
query RunQuery($runId: ID!) {
  pipelineRunOrError(runId: $runId) {
    __typename
    ... on Run {
      assets {
        id
        key {
          path
        }
      }
    }
  }
}
"""


RUN_CONCURRENCY_QUERY = """
{
  pipelineRunsOrError {
    ... on PipelineRuns {
      results {
        runId
        status
        hasConcurrencyKeySlots
        rootConcurrencyKeys
        allPools
      }
    }
  }
}
"""

RUN_LOGS_QUERY = """
query RunLogsQuery($afterCursor:String, $limit:Int, $runId: ID!) {
  pipelineRunOrError(runId: $runId) {
    __typename
    ... on Run {
        eventConnection(limit: $limit, afterCursor: $afterCursor) {
          cursor
          hasMore
          events {
            ... on ExecutionStepFailureEvent {
              stepKey
              eventType
              errorSource
              error {
                message
                stack
                causes {

                  className
                  stack
                  message
                }
              }
            }
          }
        }
      }
    }
}
"""

RUN_METRICS_QUERY = """
query RunQuery($runId: ID!) {
  pipelineRunOrError(runId: $runId) {
    __typename
    ... on Run {
        runId
        tags {
          key
          value
        }
        hasRunMetricsEnabled
    }
  }
}
"""

RUN_STEP_STATS_QUERY = """
query RunQuery($runId: ID!) {
  pipelineRunOrError(runId: $runId) {
    __typename
    ... on Run {
        runId
        stepStats {
            stepKey
            status
        }
    }
  }
}
"""


def _get_runs_data(result, run_id):
    for run_data in result.data["pipelineOrError"]["runs"]:
        if run_data["runId"] == run_id:
            # so caller can delete keys
            return copy.deepcopy(run_data)

    return None


class TestDeleteRunReadonly(ReadonlyGraphQLContextTestMatrix):
    def test_delete_runs_permission_readonly(self, graphql_context: WorkspaceRequestContext):
        repo = get_repo_at_time_1()
        run_id = graphql_context.instance.create_run_for_job(
            repo.get_job("foo_job"), status=DagsterRunStatus.STARTED.value
        ).run_id

        result = execute_dagster_graphql(
            graphql_context, DELETE_RUN_MUTATION, variables={"runId": run_id}
        )

        assert result.data["deletePipelineRun"]["__typename"] == "UnauthorizedError"

        result = execute_dagster_graphql(
            graphql_context,
            FILTERED_RUN_QUERY,
            variables={"filter": {"runIds": [run_id]}},
        )
        run_response = result.data["pipelineRunsOrError"]["results"][0]
        assert run_response["hasReExecutePermission"] is False
        assert run_response["hasTerminatePermission"] is False
        assert run_response["hasDeletePermission"] is False


class TestGetRuns(ExecutingGraphQLContextTestMatrix):
    def test_get_runs_over_graphql(self, graphql_context: WorkspaceRequestContext):
        # This include needs to be here because its inclusion screws up
        # other code in this file which reads itself to load a repo
        from dagster_graphql_tests.graphql.utils import sync_execute_get_run_log_data

        selector = infer_job_selector(graphql_context, "required_resource_job")

        payload_one = sync_execute_get_run_log_data(
            context=graphql_context,
            variables={
                "executionParams": {
                    "selector": selector,
                    "mode": "default",
                    "runConfigData": {"resources": {"R1": {"config": 2}}},
                    "executionMetadata": {"tags": [{"key": "fruit", "value": "apple"}]},
                }
            },
        )
        run_id_one = payload_one["run"]["runId"]

        read_context = graphql_context

        result = execute_dagster_graphql(read_context, RUNS_QUERY, variables={"selector": selector})

        runs = result.data["pipelineOrError"]["runs"]
        assert len(runs) == 1

        tags = runs[0]["tags"]

        tags_by_key = {tag["key"]: tag["value"] for tag in tags}

        assert tags_by_key["fruit"] == "apple"

        origin = runs[0]["repositoryOrigin"]
        assert origin
        assert origin["repositoryLocationName"] == selector["repositoryLocationName"]
        assert origin["repositoryName"] == selector["repositoryName"]

        payload_two = sync_execute_get_run_log_data(
            context=graphql_context,
            variables={
                "executionParams": {
                    "selector": selector,
                    "mode": "default",
                    "runConfigData": {"resources": {"R1": {"config": 3}}},
                    "executionMetadata": {"tags": [{"key": "veggie", "value": "carrot"}]},
                }
            },
        )

        run_id_two = payload_two["run"]["runId"]

        result = execute_dagster_graphql(read_context, RUNS_QUERY, variables={"selector": selector})

        runs = result.data["pipelineOrError"]["runs"]
        assert len(runs) == 2

        all_tag_keys_result = execute_dagster_graphql(read_context, ALL_TAG_KEYS_QUERY)
        tag_keys = set(all_tag_keys_result.data["runTagKeysOrError"]["keys"])
        # check presence rather than set equality since we might have extra tags in cloud
        assert "fruit" in tag_keys
        assert "veggie" in tag_keys

        filtered_tags_result = execute_dagster_graphql(
            read_context, FILTERED_TAGS_QUERY, variables={"tagKeys": ["fruit"]}
        )
        tags = filtered_tags_result.data["runTagsOrError"]["tags"]
        tags_dict = {item["key"]: item["values"] for item in tags}
        assert len(tags_dict) == 1
        assert tags_dict["fruit"] == ["apple"]

        run_logs_result = execute_dagster_graphql(
            read_context, RUN_LOGS_QUERY, variables={"runId": run_id_one, "limit": 5}
        )
        run_log_events = run_logs_result.data["pipelineRunOrError"]["eventConnection"]["events"]
        assert len(run_log_events) == 5
        assert run_logs_result.data["pipelineRunOrError"]["eventConnection"]["hasMore"]

        cursor = run_logs_result.data["pipelineRunOrError"]["eventConnection"]["cursor"]
        assert cursor

        run_logs_result = execute_dagster_graphql(
            read_context,
            RUN_LOGS_QUERY,
            variables={"runId": run_id_one, "limit": 5000, "afterCursor": cursor},
        )

        assert not run_logs_result.data["pipelineRunOrError"]["eventConnection"]["hasMore"]

        # delete the second run
        result = execute_dagster_graphql(
            read_context, DELETE_RUN_MUTATION, variables={"runId": run_id_two}
        )
        assert result.data["deletePipelineRun"]["__typename"] == "DeletePipelineRunSuccess"
        assert result.data["deletePipelineRun"]["runId"] == run_id_two

        # query it back out
        result = execute_dagster_graphql(read_context, RUNS_QUERY, variables={"selector": selector})

        # first is the same
        run_one_data = _get_runs_data(result, run_id_one)
        assert run_one_data

        # second is gone
        run_two_data = _get_runs_data(result, run_id_two)
        assert run_two_data is None

        # try to delete the second run again
        execute_dagster_graphql(read_context, DELETE_RUN_MUTATION, variables={"runId": run_id_two})

        result = execute_dagster_graphql(
            read_context, DELETE_RUN_MUTATION, variables={"runId": run_id_two}
        )
        assert result.data["deletePipelineRun"]["__typename"] == "RunNotFoundError"

    def test_run_config(self, graphql_context: WorkspaceRequestContext):
        # This include needs to be here because its inclusion screws up
        # other code in this file which reads itself to load a repo
        from dagster_graphql_tests.graphql.utils import sync_execute_get_run_log_data

        selector = infer_job_selector(graphql_context, "required_resource_job")

        sync_execute_get_run_log_data(
            context=graphql_context,
            variables={
                "executionParams": {
                    "selector": selector,
                    "mode": "default",
                    "runConfigData": {"resources": {"R1": {"config": 2}}},
                }
            },
        )
        result = execute_dagster_graphql(
            graphql_context, RUNS_QUERY, variables={"selector": selector}
        )

        runs = result.data["pipelineOrError"]["runs"]
        assert len(runs) == 1
        run = runs[0]
        assert run["runConfig"] == {"resources": {"R1": {"config": 2}}}
        assert run["runConfigYaml"] == yaml.safe_dump(
            run["runConfig"], default_flow_style=False, allow_unicode=True
        )


def get_repo_at_time_1():
    @op
    def op_A():
        pass

    @op
    def op_B():
        pass

    @job
    def evolving_job():
        op_A()
        op_B()

    @job
    def foo_job():
        op_A()

    @repository
    def evolving_repo():
        return [evolving_job, foo_job]

    return evolving_repo


def get_repo_at_time_2():
    @op
    def op_A():
        pass

    @op
    def op_B_prime():
        pass

    @job
    def evolving_job():
        op_A()
        op_B_prime()

    @job
    def bar_job():
        op_A()

    @repository
    def evolving_repo():
        return [evolving_job, bar_job]

    return evolving_repo


def get_asset_repo():
    @op(tags={"dagster/concurrency_key": "foo"})
    def foo():
        yield AssetMaterialization(asset_key="foo", description="foo")
        yield AssetObservation(asset_key="bar", description="bar")
        yield Output(None)

    @job
    def foo_job():
        foo()

    @asset
    def my_fail_asset():
        raise Exception("OOPS")

    my_fail_asset_job = define_asset_job(name="my_fail_asset_job", selection="my_fail_asset")

    @repository
    def asset_repo():
        return [foo_job, my_fail_asset, my_fail_asset_job]

    return asset_repo


def test_runs_over_time():
    with instance_for_test() as instance:
        repo_1 = get_repo_at_time_1()

        full_evolve_run_id = (
            repo_1.get_job("evolving_job").execute_in_process(instance=instance).run_id
        )
        foo_run_id = repo_1.get_job("foo_job").execute_in_process(instance=instance).run_id
        evolve_a_run_id = (
            repo_1.get_job("evolving_job")
            .get_subset(op_selection={"op_A"})
            .execute_in_process(
                instance=instance,
            )
            .run_id
        )
        evolve_b_run_id = (
            repo_1.get_job("evolving_job")
            .get_subset(op_selection={"op_B"})
            .execute_in_process(
                instance=instance,
            )
            .run_id
        )

        with define_out_of_process_context(
            __file__, "get_repo_at_time_1", instance
        ) as context_at_time_1:
            result = execute_dagster_graphql(context_at_time_1, ALL_RUNS_QUERY)
            assert result.data

            t1_runs = {run["runId"]: run for run in result.data["pipelineRunsOrError"]["results"]}

            assert t1_runs[full_evolve_run_id]["pipeline"] == {
                "__typename": "PipelineSnapshot",
                "name": "evolving_job",
                "solidSelection": None,
            }

            assert t1_runs[foo_run_id]["pipeline"] == {
                "__typename": "PipelineSnapshot",
                "name": "foo_job",
                "solidSelection": None,
            }

            assert t1_runs[evolve_a_run_id]["pipeline"] == {
                "__typename": "PipelineSnapshot",
                "name": "evolving_job",
                "solidSelection": None,
            }

            assert t1_runs[evolve_b_run_id]["pipeline"] == {
                "__typename": "PipelineSnapshot",
                "name": "evolving_job",
                "solidSelection": None,
            }

        with define_out_of_process_context(
            __file__, "get_repo_at_time_2", instance
        ) as context_at_time_2:
            result = execute_dagster_graphql(context_at_time_2, ALL_RUNS_QUERY)
            assert result.data

            t2_runs = {run["runId"]: run for run in result.data["pipelineRunsOrError"]["results"]}

            assert t2_runs[full_evolve_run_id]["pipeline"] == {
                "__typename": "PipelineSnapshot",
                "name": "evolving_job",
                "solidSelection": None,
            }

            assert t2_runs[evolve_a_run_id]["pipeline"] == {
                "__typename": "PipelineSnapshot",
                "name": "evolving_job",
                "solidSelection": None,
            }
            # pipeline name changed
            assert t2_runs[foo_run_id]["pipeline"] == {
                "__typename": "PipelineSnapshot",
                "name": "foo_job",
                "solidSelection": None,
            }
            # subset no longer valid - b renamed
            assert t2_runs[evolve_b_run_id]["pipeline"] == {
                "__typename": "PipelineSnapshot",
                "name": "evolving_job",
                "solidSelection": None,
            }


def test_filtered_runs():
    with instance_for_test() as instance:
        repo = get_repo_at_time_1()
        run_id_1 = (
            repo.get_job("foo_job")
            .execute_in_process(instance=instance, tags={"run": "one"})
            .run_id
        )
        run_id_2 = (
            repo.get_job("foo_job")
            .execute_in_process(instance=instance, tags={"run": "two"})
            .run_id
        )
        with define_out_of_process_context(__file__, "get_repo_at_time_1", instance) as context:
            result = execute_dagster_graphql(
                context,
                FILTERED_RUN_QUERY,
                variables={"filter": {"runIds": [run_id_1]}},
            )
            assert result.data
            run_ids = [run["runId"] for run in result.data["pipelineRunsOrError"]["results"]]
            assert len(run_ids) == 1
            assert run_ids[0] == run_id_1

            run_response = result.data["pipelineRunsOrError"]["results"][0]
            assert run_response["hasReExecutePermission"] is True
            assert run_response["hasTerminatePermission"] is True
            assert run_response["hasDeletePermission"] is True

            result = execute_dagster_graphql(
                context,
                FILTERED_RUN_QUERY,
                variables={"filter": {"tags": [{"key": "run", "value": "one"}]}},
            )
            assert result.data
            run_ids = [run["runId"] for run in result.data["pipelineRunsOrError"]["results"]]
            assert len(run_ids) == 1
            assert run_ids[0] == run_id_1

            # test multiple run ids
            result = execute_dagster_graphql(
                context,
                FILTERED_RUN_QUERY,
                variables={"filter": {"runIds": [run_id_1, run_id_2]}},
            )
            assert result.data
            run_ids = [run["runId"] for run in result.data["pipelineRunsOrError"]["results"]]
            assert len(run_ids) == 2
            assert set(run_ids) == set([run_id_1, run_id_2])


def test_filtered_runs_status():
    with instance_for_test() as instance:
        repo = get_repo_at_time_1()
        _ = instance.create_run_for_job(
            repo.get_job("foo_job"), status=DagsterRunStatus.STARTED
        ).run_id
        run_id_2 = instance.create_run_for_job(
            repo.get_job("foo_job"), status=DagsterRunStatus.FAILURE
        ).run_id
        with define_out_of_process_context(__file__, "get_repo_at_time_1", instance) as context:
            result = execute_dagster_graphql(
                context,
                FILTERED_RUN_QUERY,
                variables={"filter": {"statuses": ["FAILURE"]}},
            )
            assert result.data
            run_ids = [run["runId"] for run in result.data["pipelineRunsOrError"]["results"]]
            assert len(run_ids) == 1
            assert run_ids[0] == run_id_2


def test_filtered_runs_multiple_statuses():
    with instance_for_test() as instance:
        repo = get_repo_at_time_1()
        _ = instance.create_run_for_job(
            repo.get_job("foo_job"), status=DagsterRunStatus.STARTED
        ).run_id
        run_id_2 = instance.create_run_for_job(
            repo.get_job("foo_job"), status=DagsterRunStatus.FAILURE
        ).run_id
        run_id_3 = instance.create_run_for_job(
            repo.get_job("foo_job"), status=DagsterRunStatus.SUCCESS
        ).run_id
        with define_out_of_process_context(__file__, "get_repo_at_time_1", instance) as context:
            result = execute_dagster_graphql(
                context,
                FILTERED_RUN_QUERY,
                variables={"filter": {"statuses": ["FAILURE", "SUCCESS"]}},
            )
            assert result.data
            run_ids = [run["runId"] for run in result.data["pipelineRunsOrError"]["results"]]
            assert len(run_ids) == 2
            assert run_id_2 in run_ids
            assert run_id_3 in run_ids


def test_filtered_runs_multiple_filters():
    with instance_for_test() as instance:
        repo = get_repo_at_time_1()

        started_run_with_tags = instance.create_run_for_job(
            repo.get_job("foo_job"),
            status=DagsterRunStatus.STARTED,
            tags={"foo": "bar"},
        )
        failed_run_with_tags = instance.create_run_for_job(
            repo.get_job("foo_job"),
            status=DagsterRunStatus.FAILURE,
            tags={"foo": "bar"},
        )
        started_run_without_tags = instance.create_run_for_job(
            repo.get_job("foo_job"),
            status=DagsterRunStatus.STARTED,
            tags={"baz": "boom"},
        )

        with define_out_of_process_context(__file__, "get_repo_at_time_1", instance) as context:
            result = execute_dagster_graphql(
                context,
                FILTERED_RUN_QUERY,
                variables={
                    "filter": {
                        "statuses": ["STARTED"],
                        "tags": [{"key": "foo", "value": "bar"}],
                    }
                },
            )
            assert result.data
            run_ids = [run["runId"] for run in result.data["pipelineRunsOrError"]["results"]]
            assert len(run_ids) == 1
            assert started_run_with_tags.run_id in run_ids
            assert failed_run_with_tags.run_id not in run_ids
            assert started_run_without_tags.run_id not in run_ids


def test_filtered_runs_count():
    with instance_for_test() as instance:
        repo = get_repo_at_time_1()
        instance.create_run_for_job(  # noqa: B018
            repo.get_job("foo_job"), status=DagsterRunStatus.STARTED
        ).run_id
        instance.create_run_for_job(  # noqa: B018
            repo.get_job("foo_job"), status=DagsterRunStatus.FAILURE
        ).run_id
        with define_out_of_process_context(__file__, "get_repo_at_time_1", instance) as context:
            result = execute_dagster_graphql(
                context,
                FILTERED_RUN_COUNT_QUERY,
                variables={"filter": {"statuses": ["FAILURE"]}},
            )
            assert result.data
            count = result.data["pipelineRunsOrError"]["count"]
            assert count == 1


def test_run_ids():
    with instance_for_test() as instance:
        repo = get_repo_at_time_1()
        run_id_1 = instance.create_run_for_job(
            repo.get_job("foo_job"), status=DagsterRunStatus.STARTED
        ).run_id
        run_id_2 = instance.create_run_for_job(
            repo.get_job("foo_job"), status=DagsterRunStatus.FAILURE
        ).run_id
        run_id_3 = instance.create_run_for_job(
            repo.get_job("foo_job"), status=DagsterRunStatus.FAILURE
        ).run_id
        with define_out_of_process_context(__file__, "get_repo_at_time_1", instance) as context:
            result = execute_dagster_graphql(
                context,
                RUN_IDS_QUERY,
                variables={"filter": {"statuses": ["FAILURE"]}},
            )
            assert result.data
            assert result.data["runIdsOrError"]["results"] == [run_id_3, run_id_2]

            result = execute_dagster_graphql(
                context,
                RUN_IDS_QUERY,
                variables={"filter": {"statuses": ["FAILURE"]}, "limit": 1},
            )
            assert result.data
            assert result.data["runIdsOrError"]["results"] == [run_id_3]

            result = execute_dagster_graphql(
                context,
                RUN_IDS_QUERY,
                variables={"cursor": run_id_2},
            )
            assert result.data
            assert result.data["runIdsOrError"]["results"] == [run_id_1]


def test_run_group():
    with instance_for_test() as instance:
        repo = get_repo_at_time_1()
        foo_job = repo.get_job("foo_job")
        runs = [foo_job.execute_in_process(instance=instance)]
        root_run_id = runs[-1].run_id
        for _ in range(3):
            # https://github.com/dagster-io/dagster/issues/2433
            run = instance.create_run_for_job(
                foo_job,
                parent_run_id=root_run_id,
                root_run_id=root_run_id,
                tags={PARENT_RUN_ID_TAG: root_run_id, ROOT_RUN_ID_TAG: root_run_id},
            )
            execute_run(InMemoryJob(foo_job), run, instance)
            runs.append(run)  # pyright: ignore[reportArgumentType]

        with define_out_of_process_context(
            __file__, "get_repo_at_time_1", instance
        ) as context_at_time_1:
            result_one = execute_dagster_graphql(
                context_at_time_1,
                RUN_GROUP_QUERY,
                variables={"runId": root_run_id},
            )
            assert result_one.data["runGroupOrError"]["__typename"] == "RunGroup"

            assert len(result_one.data["runGroupOrError"]["runs"]) == 4

            result_two = execute_dagster_graphql(
                context_at_time_1,
                RUN_GROUP_QUERY,
                variables={"runId": runs[-1].run_id},
            )
            assert result_one.data["runGroupOrError"]["__typename"] == "RunGroup"
            assert len(result_two.data["runGroupOrError"]["runs"]) == 4

            assert (
                result_one.data["runGroupOrError"]["rootRunId"]
                == result_two.data["runGroupOrError"]["rootRunId"]
            )
            assert (
                result_one.data["runGroupOrError"]["runs"]
                == result_two.data["runGroupOrError"]["runs"]
            )


def test_run_group_not_found():
    with instance_for_test() as instance:
        with define_out_of_process_context(
            __file__, "get_repo_at_time_1", instance
        ) as context_at_time_1:
            result = execute_dagster_graphql(
                context_at_time_1,
                RUN_GROUP_QUERY,
                variables={"runId": "foo"},
            )
            assert result.data
            assert result.data["runGroupOrError"]
            assert result.data["runGroupOrError"]["__typename"] == "RunGroupNotFoundError"
            assert result.data["runGroupOrError"]["runId"] == "foo"
            assert result.data["runGroupOrError"][
                "message"
            ] == "Run group of run {run_id} could not be found.".format(run_id="foo")


def test_asset_batching():
    with instance_for_test() as instance:
        repo = get_asset_repo()
        foo_job = repo.get_job("foo_job")
        for _ in range(3):
            foo_job.execute_in_process(instance=instance)

        my_fail_asset_job = repo.get_job("my_fail_asset_job")
        result = my_fail_asset_job.execute_in_process(instance=instance, raise_on_error=False)

        fail_run_id = result.dagster_run.run_id

        with define_out_of_process_context(__file__, "asset_repo", instance) as context:
            traced_counter.set(Counter())
            result = execute_dagster_graphql(
                context, ASSET_RUNS_QUERY, variables={"assetKey": {"path": ["foo"]}}
            )
            assert result.data
            assert "assetOrError" in result.data
            assert "assetMaterializations" in result.data["assetOrError"]
            materializations = result.data["assetOrError"]["assetMaterializations"]
            assert len(materializations) == 3

            counter = traced_counter.get()
            counts = counter.counts()  # pyright: ignore[reportOptionalMemberAccess]
            assert counts
            assert counts.get("DagsterInstance.get_run_records") == 1

            run_ids = [materialization["runOrError"]["id"] for materialization in materializations]

            run_id = run_ids[0]
            result = execute_dagster_graphql(context, RUN_ASSETS_QUERY, variables={"runId": run_id})

            asset_ids = [asset["id"] for asset in result.data["pipelineRunOrError"]["assets"]]
            assert sorted(asset_ids) == sorted(['["foo"]', '["bar"]'])

            fail_run_result = execute_dagster_graphql(
                context, RUN_ASSETS_QUERY, variables={"runId": fail_run_id}
            )
            # despite no materialization or observation, the asset is returned, because it was planned
            asset_ids = [
                asset["id"] for asset in fail_run_result.data["pipelineRunOrError"]["assets"]
            ]
            assert asset_ids == ['["my_fail_asset"]']


def test_run_has_concurrency_slots():
    with tempfile.TemporaryDirectory() as temp_dir:
        with instance_for_test(
            overrides={
                "event_log_storage": {
                    "module": "dagster.utils.test",
                    "class": "ConcurrencyEnabledSqliteTestEventLogStorage",
                    "config": {"base_dir": temp_dir},
                },
            }
        ) as instance:
            repo = get_asset_repo()
            instance.event_log_storage.set_concurrency_slots("foo", 1)
            run_id = instance.create_run_for_job(
                repo.get_job("foo_job"), status=DagsterRunStatus.FAILURE
            ).run_id

            with define_out_of_process_context(__file__, "asset_repo", instance) as context:
                result = execute_dagster_graphql(context, RUN_CONCURRENCY_QUERY)
                assert result.data
                assert len(result.data["pipelineRunsOrError"]["results"]) == 1
                assert result.data["pipelineRunsOrError"]["results"][0]["runId"] == run_id
                assert not result.data["pipelineRunsOrError"]["results"][0][
                    "hasConcurrencyKeySlots"
                ]
                assert result.data["pipelineRunsOrError"]["results"][0]["rootConcurrencyKeys"]
                assert result.data["pipelineRunsOrError"]["results"][0]["allPools"]

            claim = instance.event_log_storage.claim_concurrency_slot(
                "foo", run_id, "fake_step_key"
            )
            assert claim.is_claimed

            with define_out_of_process_context(__file__, "asset_repo", instance) as context:
                result = execute_dagster_graphql(context, RUN_CONCURRENCY_QUERY)
                assert result.data
                assert len(result.data["pipelineRunsOrError"]["results"]) == 1
                assert result.data["pipelineRunsOrError"]["results"][0]["runId"] == run_id
                assert result.data["pipelineRunsOrError"]["results"][0]["hasConcurrencyKeySlots"]
                assert result.data["pipelineRunsOrError"]["results"][0]["rootConcurrencyKeys"]
                assert result.data["pipelineRunsOrError"]["results"][0]["allPools"]


@pytest.mark.parametrize(
    "run_tag, run_tag_value, run_metrics_enabled, failure_message",
    [
        (None, None, False, "run_metrics tag not present should result to false"),
        (".dagster/run_metrics", "true", True, "run_metrics tag set to true should result to true"),
        (
            ".dagster/run_metrics",
            "false",
            False,
            "run_metrics tag set to falsy value should result to false",
        ),
        (
            "dagster/run_metrics",
            "true",
            True,
            "public run_metrics tag set to true should result to true",
        ),
    ],
)
def test_run_has_run_metrics_enabled(run_tag, run_tag_value, run_metrics_enabled, failure_message):
    with instance_for_test() as instance:
        repo = get_repo_at_time_1()
        tags = (
            {
                run_tag: run_tag_value,
            }
            if run_tag
            else {}
        )
        run = instance.create_run_for_job(
            repo.get_job("foo_job"), status=DagsterRunStatus.STARTED, tags=tags
        )

        with define_out_of_process_context(__file__, "get_repo_at_time_1", instance) as context:
            result = execute_dagster_graphql(
                context,
                RUN_METRICS_QUERY,
                variables={"runId": run.run_id},
            )
            assert result.data
            has_run_metrics_enabled = result.data["pipelineRunOrError"]["hasRunMetricsEnabled"]
            assert has_run_metrics_enabled == run_metrics_enabled, failure_message


def test_event_log_step_stats_retry_with_no_start():
    with instance_for_test() as instance:
        repo = get_repo_at_time_1()
        run = instance.create_run_for_job(repo.get_job("foo_job"), status=DagsterRunStatus.STARTED)
        storage = instance.event_log_storage
        node_handle = NodeHandle("E", None)
        step_handle = StepHandle(node_handle)
        storage.store_event(
            EventLogEntry(
                error_info=None,
                user_message="",
                level="debug",
                run_id=run.run_id,
                timestamp=time.time() - 150,
                step_key=step_handle.to_key(),
                job_name="foo_job",
                dagster_event=DagsterEvent(
                    DagsterEventType.STEP_UP_FOR_RETRY.value,
                    "foo_job",
                    node_handle=node_handle,
                    step_handle=step_handle,
                    event_specific_data=None,
                ),
            )
        )

        with define_out_of_process_context(__file__, "get_repo_at_time_1", instance) as context:
            result = execute_dagster_graphql(
                context,
                RUN_STEP_STATS_QUERY,
                variables={"runId": run.run_id},
            )
            assert result.data
            step_stats = result.data["pipelineRunOrError"]["stepStats"]
            assert len(step_stats) == 1
            step_stat = step_stats[0]
            assert step_stat["stepKey"] == "E"
            assert step_stat["status"] is None
