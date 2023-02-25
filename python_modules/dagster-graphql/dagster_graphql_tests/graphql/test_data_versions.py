from typing import Any, Mapping, Optional, Sequence

from dagster import (
    AssetIn,
    DailyPartitionsDefinition,
    RepositoryDefinition,
    TimeWindowPartitionMapping,
    asset,
    repository,
)
from dagster._core.definitions.data_version import DATA_VERSION_TAG
from dagster._core.test_utils import instance_for_test, wait_for_runs_to_finish
from dagster._core.workspace.context import WorkspaceRequestContext
from dagster_graphql.client.query import LAUNCH_PIPELINE_EXECUTION_MUTATION
from dagster_graphql.test.utils import (
    GqlAssetKey,
    define_out_of_process_context,
    execute_dagster_graphql,
    infer_job_or_pipeline_selector,
)

from dagster_graphql_tests.graphql.test_assets import GET_ASSET_DATA_VERSIONS


def get_repo_v1():
    @asset
    def foo():
        return True

    @asset
    def bar(foo):
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
            assert _fetch_data_versions(context_v2, repo_v2)


def test_stale_status():
    repo = get_repo_v1()

    with instance_for_test() as instance:
        with define_out_of_process_context(__file__, "get_repo_v1", instance) as context:
            result = _fetch_data_versions(context, repo)
            foo = _get_asset_node("foo", result)
            assert foo["currentDataVersion"] is None
            assert foo["staleStatus"] == "MISSING"
            assert foo["staleCauses"] == []

            assert _materialize_assets(context, repo)
            wait_for_runs_to_finish(context.instance)

            result = _fetch_data_versions(context, repo)
            foo = _get_asset_node("foo", result)
            assert foo["currentDataVersion"] is not None
            assert foo["staleStatus"] == "FRESH"
            assert foo["staleCauses"] == []

            assert _materialize_assets(context, repo, asset_selection=[AssetKey(["foo"])])
            wait_for_runs_to_finish(context.instance)

            result = _fetch_data_versions(context, repo)
            bar = _get_asset_node("bar", result)
            assert bar["currentDataVersion"] is not None
            assert bar["staleStatus"] == "STALE"
            assert bar["staleCauses"] == [
                {
                    "key": {"path": ["foo"]},
                    "category": "DATA",
                    "reason": "updated data version",
                    "dependency": None,
                }
            ]


def test_data_version_from_tags():
    repo_v1 = get_repo_v1()
    with instance_for_test() as instance:
        with define_out_of_process_context(__file__, "get_repo_v1", instance) as context_v1:
            assert _materialize_assets(context_v1, repo_v1)
            wait_for_runs_to_finish(context_v1.instance)
            result = _fetch_data_versions(context_v1, repo_v1)
            tags = result.data["assetNodes"][0]["assetMaterializations"][0]["tags"]
            dv_tag = next(tag for tag in tags if tag["key"] == DATA_VERSION_TAG)
            assert dv_tag["value"] == result.data["assetNodes"][0]["currentDataVersion"]


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

    @asset
    def b(a):
        return a

    @repository
    def repo():
        return [a, b]

    return repo


def test_partitioned_self_dep():
    repo = get_repo_with_partitioned_self_dep_asset()

    with instance_for_test() as instance:
        with define_out_of_process_context(
            __file__, "get_repo_with_partitioned_self_dep_asset", instance
        ) as context:
            result = _fetch_data_versions(context, repo)
            assert result
            assert result.data
            assert _get_asset_node("a", result)["staleStatus"] == "MISSING"
            assert _get_asset_node("b", result)["staleStatus"] == "MISSING"


def _materialize_assets(
    context: WorkspaceRequestContext,
    repo: RepositoryDefinition,
    asset_selection: Optional[Sequence[GqlAssetKey]] = None,
):
    gql_asset_selection = (
        [AssetKey.to_graphql_input(key) for key in asset_selection] if asset_selection else None
    )
    selector = infer_job_or_pipeline_selector(
        context, repo.get_implicit_asset_job_names()[0], asset_selection=gql_asset_selection
    )
    return execute_dagster_graphql(
        context,
        LAUNCH_PIPELINE_EXECUTION_MUTATION,
        variables={
            "executionParams": {
                "selector": selector,
            }
        },
    )


def _fetch_data_versions(context: WorkspaceRequestContext, repo: RepositoryDefinition):
    selector = infer_job_or_pipeline_selector(context, repo.get_implicit_asset_job_names()[0])
    return execute_dagster_graphql(
        context,
        GET_ASSET_DATA_VERSIONS,
        variables={
            "pipelineSelector": selector,
        },
    )


def _get_asset_node(key: str, result: Any) -> Mapping[str, Any]:
    return next((node for node in result.data["assetNodes"] if node["assetKey"]["path"] == [key]))
