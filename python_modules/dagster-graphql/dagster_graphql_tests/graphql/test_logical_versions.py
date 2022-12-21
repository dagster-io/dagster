from dagster_graphql.client.query import LAUNCH_PIPELINE_EXECUTION_MUTATION
from dagster_graphql.test.utils import (
    define_out_of_process_context,
    execute_dagster_graphql,
    infer_job_or_pipeline_selector,
)
from dagster_graphql_tests.graphql.test_assets import GET_ASSET_LOGICAL_VERSIONS

from dagster import (
    AssetIn,
    DailyPartitionsDefinition,
    RepositoryDefinition,
    TimeWindowPartitionMapping,
    asset,
    repository,
)
from dagster._core.test_utils import instance_for_test, wait_for_runs_to_finish
from dagster._core.workspace.context import WorkspaceRequestContext


def get_repo_v1():
    @asset
    def foo():
        return True

    @asset
    def bar(foo):  # pylint: disable=unused-argument
        return True

    @repository
    def repo():
        return [foo, bar]

    return repo


def get_repo_v2():
    @asset
    def bar():
        return True

    @repository
    def repo():
        return [bar]

    return repo


def test_dependencies_changed():
    repo_v1 = get_repo_v1()
    repo_v2 = get_repo_v2()

    with instance_for_test() as instance:
        with define_out_of_process_context(__file__, "get_repo_v1", instance) as context_v1:
            assert _materialize_assets(context_v1, repo_v1)
            wait_for_runs_to_finish(context_v1.instance)
        with define_out_of_process_context(__file__, "get_repo_v2", instance) as context_v2:
            assert _fetch_logical_versions(context_v2, repo_v2)


def get_repo_with_partitioned_self_dep_asset():
    @asset(
        partitions_def=DailyPartitionsDefinition(start_date="2020-01-01"),
        ins={
            "a": AssetIn(
                partition_mapping=TimeWindowPartitionMapping(start_offset=-1, end_offset=-1)
            )
        },
    )
    def a(a):
        del a

    @repository
    def repo():
        return [a]

    return repo


def test_partitioned_self_dep():
    repo = get_repo_with_partitioned_self_dep_asset()

    with instance_for_test() as instance:
        with define_out_of_process_context(
            __file__, "get_repo_with_partitioned_self_dep_asset", instance
        ) as context:
            result = _fetch_logical_versions(context, repo)
            assert result
            assert result.data
            assert result.data["assetNodes"][0]["projectedLogicalVersion"] is None


def _materialize_assets(context: WorkspaceRequestContext, repo: RepositoryDefinition):
    selector = infer_job_or_pipeline_selector(context, repo.get_base_asset_job_names()[0])
    return execute_dagster_graphql(
        context,
        LAUNCH_PIPELINE_EXECUTION_MUTATION,
        variables={
            "executionParams": {
                "selector": selector,
            }
        },
    )


def _fetch_logical_versions(context: WorkspaceRequestContext, repo: RepositoryDefinition):
    selector = infer_job_or_pipeline_selector(context, repo.get_base_asset_job_names()[0])
    return execute_dagster_graphql(
        context,
        GET_ASSET_LOGICAL_VERSIONS,
        variables={
            "pipelineSelector": selector,
        },
    )
