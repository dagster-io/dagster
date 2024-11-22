from typing import Any, Mapping, Optional, Sequence, Union, cast

from dagster import (
    AssetIn,
    DailyPartitionsDefinition,
    OpExecutionContext,
    RepositoryDefinition,
    TimeWindowPartitionMapping,
    asset,
    job,
    op,
    repository,
)
from dagster._config.pythonic_config import Config
from dagster._core.definitions.data_version import DATA_VERSION_TAG, DataVersion
from dagster._core.definitions.decorators.source_asset_decorator import observable_source_asset
from dagster._core.definitions.definitions_class import Definitions
from dagster._core.definitions.events import AssetKey, Output
from dagster._core.definitions.partition import StaticPartitionsDefinition
from dagster._core.definitions.unresolved_asset_job_definition import define_asset_job
from dagster._core.test_utils import instance_for_test, wait_for_runs_to_finish
from dagster._core.workspace.context import WorkspaceRequestContext
from dagster_graphql.client.query import LAUNCH_PIPELINE_EXECUTION_MUTATION
from dagster_graphql.test.utils import (
    GqlAssetKey,
    GqlResult,
    define_out_of_process_context,
    execute_dagster_graphql,
    infer_job_selector,
    infer_repository_selector,
)

from dagster_graphql_tests.graphql.test_assets import (
    GET_ASSET_DATA_VERSIONS,
    GET_ASSET_DATA_VERSIONS_BY_PARTITION,
    GET_ASSET_JOB_NAMES,
)


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
            foo = _get_asset_node(result, "foo")
            assert foo["dataVersion"] is None
            assert foo["staleStatus"] == "MISSING"
            assert foo["staleCauses"] == []

            assert _materialize_assets(context, repo)
            wait_for_runs_to_finish(context.instance)

            result = _fetch_data_versions(context, repo)
            foo = _get_asset_node(result, "foo")
            assert foo["dataVersion"] is not None
            assert foo["staleStatus"] == "FRESH"
            assert foo["staleCauses"] == []

            assert _materialize_assets(context, repo, asset_selection=[AssetKey(["foo"])])
            wait_for_runs_to_finish(context.instance)

            result = _fetch_data_versions(context, repo)
            bar = _get_asset_node(result, "bar")
            assert bar["dataVersion"] is not None
            assert bar["staleStatus"] == "STALE"
            assert bar["staleCauses"] == [
                {
                    "key": {"path": ["foo"]},
                    "category": "DATA",
                    "reason": "has a new materialization",
                    "dependency": None,
                }
            ]


def get_repo_partitioned():
    partitions_def = StaticPartitionsDefinition(["alpha", "beta"])

    class FooConfig(Config):
        prefix: str = "ok"

    @asset(partitions_def=partitions_def)
    def foo(context: OpExecutionContext, config: FooConfig) -> Output[bool]:
        return Output(
            True, data_version=DataVersion(f"{config.prefix}_foo_{context.partition_key}")
        )

    @asset(partitions_def=partitions_def)
    def bar(context: OpExecutionContext, foo) -> Output[bool]:
        return Output(True, data_version=DataVersion(f"ok_bar_{context.partition_key}"))

    @repository
    def repo():
        return [foo, bar]

    return repo


def test_stale_status_partitioned():
    repo = get_repo_partitioned()

    with instance_for_test() as instance:
        with define_out_of_process_context(__file__, "get_repo_partitioned", instance) as context:
            for key in ["foo", "bar"]:
                result = _fetch_partition_data_versions(context, AssetKey([key]))
                node = _get_asset_node(result)
                assert node["dataVersion"] is None
                assert node["dataVersionByPartition"] == [None, None]
                assert (
                    node["staleStatus"] == "FRESH"
                )  # always returns fresh for this undefined field
                assert node["staleStatusByPartition"] == ["MISSING", "MISSING"]
                assert node["staleCauses"] == []  # always returns empty for this undefined field
                assert node["staleCausesByPartition"] == [[], []]

            assert _materialize_assets(
                context, repo, [AssetKey(["foo"]), AssetKey(["bar"])], ["alpha", "beta"]
            )
            wait_for_runs_to_finish(context.instance)

            for key in ["foo", "bar"]:
                result = _fetch_partition_data_versions(context, AssetKey([key]), "alpha")
                node = _get_asset_node(result)
                assert node["dataVersion"] == f"ok_{key}_alpha"
                assert node["dataVersionByPartition"] == [f"ok_{key}_alpha", f"ok_{key}_beta"]
                assert node["staleStatus"] == "FRESH"
                assert node["staleStatusByPartition"] == ["FRESH", "FRESH"]
                assert node["staleCauses"] == []
                assert node["staleCausesByPartition"] == [[], []]

            assert _materialize_assets(
                context,
                repo,
                [AssetKey(["foo"])],
                ["alpha", "beta"],
                run_config_data={"ops": {"foo": {"config": {"prefix": "from_config"}}}},
            )
            wait_for_runs_to_finish(context.instance)

            result = _fetch_partition_data_versions(context, AssetKey(["foo"]), "alpha")
            foo = _get_asset_node(result, "foo")
            assert foo["dataVersion"] == "from_config_foo_alpha"
            assert foo["dataVersionByPartition"] == [
                "from_config_foo_alpha",
                "from_config_foo_beta",
            ]
            assert foo["staleStatus"] == "FRESH"
            assert foo["staleStatusByPartition"] == ["FRESH", "FRESH"]

            result = _fetch_partition_data_versions(
                context, AssetKey(["bar"]), "alpha", ["beta", "alpha"]
            )
            bar = _get_asset_node(result, "bar")
            assert bar["dataVersion"] == "ok_bar_alpha"
            assert bar["dataVersionByPartition"] == ["ok_bar_beta", "ok_bar_alpha"]
            assert bar["staleStatus"] == "STALE"
            assert bar["staleStatusByPartition"] == ["STALE", "STALE"]
            assert bar["staleCauses"] == [
                {
                    "key": {"path": ["foo"]},
                    "partitionKey": "alpha",
                    "category": "DATA",
                    "reason": "has a new data version",
                    "dependency": None,
                    "dependencyPartitionKey": None,
                }
            ]
            assert bar["staleCausesByPartition"] == [
                [
                    {
                        "key": {"path": ["foo"]},
                        "partitionKey": key,
                        "category": "DATA",
                        "reason": "has a new data version",
                        "dependency": None,
                        "dependencyPartitionKey": None,
                    }
                ]
                for key in ["beta", "alpha"]
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
            assert dv_tag["value"] == result.data["assetNodes"][0]["dataVersion"]


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
            result = _fetch_partition_data_versions(
                context, AssetKey(["a"]), partitions=["2020-01-01", "2020-01-02"]
            )
            assert result
            assert result.data
            node = _get_asset_node(result, "a")
            assert node["staleStatusByPartition"] == ["MISSING", "MISSING"]

            result = _fetch_data_versions(context, repo)
            node = _get_asset_node(result, "b")
            assert node["staleStatus"] == "MISSING"


def get_observable_source_asset_repo():
    @asset(partitions_def=StaticPartitionsDefinition(["1"]))
    def foo():
        return 1

    @observable_source_asset
    def bar():
        return DataVersion("1")

    @asset(partitions_def=StaticPartitionsDefinition(["2"]))
    def baz():
        return 1

    @op
    def bop():
        pass

    @job
    def bop_job():
        bop()

    foo_job = define_asset_job("foo_job", [foo])
    bar_job = define_asset_job("bar_job", [bar])

    defs = Definitions(
        assets=[foo, bar, baz],
        jobs=[foo_job, bar_job, bop_job],
    )
    return defs.get_repository_def()


def test_source_asset_job_name():
    get_observable_source_asset_repo()

    with instance_for_test() as instance:
        with define_out_of_process_context(
            __file__, "get_observable_source_asset_repo", instance
        ) as context:
            selector = infer_repository_selector(context)
            result = execute_dagster_graphql(
                context,
                GET_ASSET_JOB_NAMES,
                variables={
                    "selector": selector,
                },
            )
            assert result and result.data
            foo_jobs = _get_asset_node(result.data["repositoryOrError"], "foo")["jobNames"]
            bar_jobs = _get_asset_node(result.data["repositoryOrError"], "bar")["jobNames"]
            baz_jobs = _get_asset_node(result.data["repositoryOrError"], "baz")["jobNames"]

            # All nodes should have separate job sets since there are two different partitions defs
            # and a non-partitioned observable.
            assert foo_jobs and foo_jobs != bar_jobs and foo_jobs != baz_jobs
            assert bar_jobs and bar_jobs != foo_jobs and bar_jobs != baz_jobs
            assert baz_jobs and baz_jobs != foo_jobs and baz_jobs != bar_jobs

            # Make sure none of our assets included in non-asset job
            assert "bop_job" not in foo_jobs
            assert "bop_job" not in bar_jobs
            assert "bop_job" not in baz_jobs

            # Make sure observable source asset does not appear in non-explicit observation job
            assert "foo_job" not in bar_jobs

            # Make sure observable source asset appears in explicit observation job
            assert "bar_job" in bar_jobs


def _materialize_assets(
    context: WorkspaceRequestContext,
    repo: RepositoryDefinition,
    asset_selection: Optional[Sequence[AssetKey]] = None,
    partition_keys: Optional[Sequence[str]] = None,
    run_config_data: Optional[Mapping[str, Any]] = None,
) -> Union[GqlResult, Sequence[GqlResult]]:
    gql_asset_selection = (
        cast(Sequence[GqlAssetKey], [key.to_graphql_input() for key in asset_selection])
        if asset_selection
        else None
    )
    selector = infer_job_selector(
        context, repo.get_implicit_asset_job_names()[0], asset_selection=gql_asset_selection
    )
    if partition_keys:
        results = []
        for key in partition_keys:
            results.append(
                execute_dagster_graphql(
                    context,
                    LAUNCH_PIPELINE_EXECUTION_MUTATION,
                    variables={
                        "executionParams": {
                            "selector": selector,
                            "executionMetadata": {
                                "tags": [{"key": "dagster/partition", "value": key}]
                            },
                            "runConfigData": run_config_data,
                        }
                    },
                )
            )
        return results
    else:
        selector = infer_job_selector(
            context, repo.get_implicit_asset_job_names()[0], asset_selection=gql_asset_selection
        )
        return execute_dagster_graphql(
            context,
            LAUNCH_PIPELINE_EXECUTION_MUTATION,
            variables={
                "executionParams": {
                    "selector": selector,
                    "runConfigData": run_config_data,
                }
            },
        )


def _fetch_data_versions(context: WorkspaceRequestContext, repo: RepositoryDefinition):
    selector = infer_job_selector(context, repo.get_implicit_asset_job_names()[0])
    return execute_dagster_graphql(
        context,
        GET_ASSET_DATA_VERSIONS,
        variables={
            "pipelineSelector": selector,
        },
    )


def _fetch_partition_data_versions(
    context: WorkspaceRequestContext,
    asset_key: AssetKey,
    partition: Optional[str] = None,
    partitions: Optional[Sequence[str]] = None,
):
    return execute_dagster_graphql(
        context,
        GET_ASSET_DATA_VERSIONS_BY_PARTITION,
        variables={
            "assetKey": asset_key.to_graphql_input(),
            "partition": partition,
            "partitions": partitions,
        },
    )


def _get_asset_node(result: Any, key: Optional[str] = None) -> Mapping[str, Any]:
    to_check = result if isinstance(result, dict) else result.data  # GqlResult
    if key is None:  # assume we are dealing with a single-node query
        return to_check["assetNodeOrError"]
    else:
        return (
            to_check["assetNodeOrError"]
            if "assetNodeOrError" in to_check
            else next(node for node in to_check["assetNodes"] if node["assetKey"]["path"] == [key])
        )
