import shutil
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any, Optional

import pytest
from dagster import (
    AssetIn,
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
from dagster._core.definitions.partitions.definition import (
    DailyPartitionsDefinition,
    DynamicPartitionsDefinition,
    StaticPartitionsDefinition,
)
from dagster._core.definitions.unresolved_asset_job_definition import define_asset_job
from dagster._core.test_utils import wait_for_runs_to_finish
from dagster._core.workspace.context import WorkspaceRequestContext
from dagster_graphql.test.utils import (
    define_out_of_process_context,
    ensure_dagster_graphql_tests_import,
    execute_dagster_graphql,
    infer_job_selector,
    infer_repository_selector,
    materialize_assets,
    temp_workspace_file,
)

ensure_dagster_graphql_tests_import()

from dagster_graphql_tests.graphql.graphql_context_test_suite import (
    ExecutingGraphQLContextTestMatrix,
)
from dagster_graphql_tests.graphql.test_assets import (
    GET_ASSET_DATA_VERSIONS,
    GET_ASSET_DATA_VERSIONS_BY_PARTITION,
    GET_ASSET_JOB_NAMES,
)


class TestDataVersions(ExecutingGraphQLContextTestMatrix):
    # Storage dir is shared between tests in the same class, so we need to clean it out.
    @pytest.fixture(autouse=True)
    def clean_storage_directory(self, graphql_context):
        """Clean IO manager storage directory before each test to prevent pollution."""
        # Clean before test runs
        storage_dir = Path(graphql_context.instance.storage_directory())
        if storage_dir.exists():
            shutil.rmtree(storage_dir)
            storage_dir.mkdir(parents=True)
        yield
        # Clean after test runs
        if storage_dir.exists():
            shutil.rmtree(storage_dir)
            storage_dir.mkdir(parents=True)

    def test_dependencies_changed(self, graphql_context):
        repo_v2 = get_repo_v2()
        instance = graphql_context.instance

        with define_out_of_process_context(__file__, "get_repo_v1", instance) as context_v1:
            assert materialize_assets(context_v1, [AssetKey(["foo"]), AssetKey(["bar"])])
            wait_for_runs_to_finish(context_v1.instance)
        with define_out_of_process_context(__file__, "get_repo_v2", instance) as context_v2:
            assert _fetch_data_versions(context_v2, repo_v2)

    def test_stale_status(self, graphql_context):
        repo = get_repo_v1()
        instance = graphql_context.instance

        with define_out_of_process_context(__file__, "get_repo_v1", instance) as context:
            result = _fetch_data_versions(context, repo)
            foo = _get_asset_node(result, "foo")
            assert foo["dataVersion"] is None
            assert foo["staleStatus"] == "MISSING"
            assert foo["staleCauses"] == []

            assert materialize_assets(context, [AssetKey(["foo"]), AssetKey(["bar"])])
            wait_for_runs_to_finish(context.instance)

        with define_out_of_process_context(__file__, "get_repo_v1", instance) as context:
            result = _fetch_data_versions(context, repo)
            foo = _get_asset_node(result, "foo")
            assert foo["dataVersion"] is not None
            assert foo["staleStatus"] == "FRESH"
            assert foo["staleCauses"] == []

            assert materialize_assets(context, asset_selection=[AssetKey(["foo"])])
            wait_for_runs_to_finish(context.instance)

        with define_out_of_process_context(__file__, "get_repo_v1", instance) as context:
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

    def test_stale_status_partitioned(self, graphql_context):
        instance = graphql_context.instance
        instance.add_dynamic_partitions("dynamic", ["alpha", "beta"])

        with define_out_of_process_context(__file__, "get_repo_partitioned", instance) as context:
            for key in ["foo", "bar", "dynamic_asset"]:
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

            assert materialize_assets(
                context,
                [AssetKey(["foo"]), AssetKey(["bar"]), AssetKey("dynamic_asset")],
                ["alpha", "beta"],
            )
            wait_for_runs_to_finish(context.instance)

        with define_out_of_process_context(__file__, "get_repo_partitioned", instance) as context:
            for key in ["foo", "bar", "dynamic_asset"]:
                result = _fetch_partition_data_versions(context, AssetKey([key]), "alpha")
                node = _get_asset_node(result)
                assert node["dataVersion"] == f"ok_{key}_alpha"
                assert node["dataVersionByPartition"] == [f"ok_{key}_alpha", f"ok_{key}_beta"]
                assert node["staleStatus"] == "FRESH"
                assert node["staleStatusByPartition"] == ["FRESH", "FRESH"]
                assert node["staleCauses"] == []
                assert node["staleCausesByPartition"] == [[], []]

            assert materialize_assets(
                context,
                [AssetKey(["foo"])],
                ["alpha", "beta"],
                run_config_data={"ops": {"foo": {"config": {"prefix": "from_config"}}}},
            )
            wait_for_runs_to_finish(context.instance)

        with define_out_of_process_context(__file__, "get_repo_partitioned", instance) as context:
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

    def test_cross_repo_dependency(self, graphql_context):
        instance = graphql_context.instance

        with (
            temp_workspace_file(
                [
                    ("repo1", __file__, "get_cross_repo_test_repo1"),
                    ("repo2", __file__, "get_cross_repo_test_repo2"),
                ]
            ) as workspace_file,
            define_out_of_process_context(workspace_file, None, instance) as context,
        ):
            # Materialize the downstream asset. Provenance will store the version of foo as INITIAL.
            assert materialize_assets(context, [AssetKey(["bar"])], location_name="repo2")
            wait_for_runs_to_finish(context.instance)

            repo2 = get_cross_repo_test_repo2()
            result = _fetch_data_versions(context, repo2, location_name="repo2")
            bar = _get_asset_node(result, "bar")
            assert bar["staleStatus"] == "FRESH"

    def test_data_version_from_tags(self, graphql_context):
        repo_v1 = get_repo_v1()
        instance = graphql_context.instance

        with define_out_of_process_context(__file__, "get_repo_v1", instance) as context_v1:
            assert materialize_assets(context_v1, [AssetKey(["foo"]), AssetKey(["bar"])])
            wait_for_runs_to_finish(context_v1.instance)
            result = _fetch_data_versions(context_v1, repo_v1)
            tags = result.data["assetNodes"][0]["assetMaterializations"][0]["tags"]
            dv_tag = next(tag for tag in tags if tag["key"] == DATA_VERSION_TAG)
            assert dv_tag["value"] == result.data["assetNodes"][0]["dataVersion"]

    def test_partitioned_self_dep(self, graphql_context):
        repo = get_repo_with_partitioned_self_dep_asset()
        instance = graphql_context.instance

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

    def test_source_asset_job_name(self, graphql_context):
        get_observable_source_asset_repo()
        instance = graphql_context.instance

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

    def test_stale_status_observable_transition(self, graphql_context):
        """Test that downstream assets don't incorrectly become stale when upstream transitions to observable.

        This test reproduces the bug reported in:
        https://dagsterlabs.slack.com/archives/C06GXHNH3T8/p1759938082471509

        Scenario:
        1. Upstream asset is materializable, gets materialized with explicit data version "v1"
        2. Downstream materializes and stores upstream's materialization data version in provenance
        3. Upstream asset is changed to observable (without explicit data version)
        4. Observations are reported for upstream with AUTO-GENERATED data versions
        5. Bug: Downstream incorrectly shows as STALE even though the actual data hasn't changed

        The key issue is that:
        - The downstream's provenance references the upstream's last MATERIALIZATION with data version "v1"
        - When checking staleness, the system retrieves the upstream's last OBSERVATION
        - The observation has an AUTO-GENERATED data version (based on timestamp) that differs from "v1"
        - Even though the actual upstream data hasn't changed, the downstream appears stale
          because the data version scheme changed (explicit -> auto-generated)

        This is the core bug: when an asset transitions from materializable to observable,
        and the observable doesn't return an explicit data version, the auto-generated
        data versions cause false staleness in downstream assets.

        Expected: Downstream should remain FRESH since the actual data hasn't changed
        Actual: Downstream shows as STALE with reason "has a new data version"
        """
        # This test only works in Cloud due to only Cloud having observation info on asset records.
        # We intentionally accept the incorrect behavior is OSS for now, for the sake of
        # performance.
        if type(graphql_context).__name__ != "DagsterCloudWorkspaceRequestContext":
            pytest.skip("Test only works in Dagster Cloud due to observation data availability.")

        # Step 1: Materialize both assets when upstream is materializable
        with define_out_of_process_context(
            __file__, "get_repo_observable_transition", graphql_context.instance
        ) as context:
            assert materialize_assets(context, [AssetKey(["upstream"]), AssetKey(["downstream"])])
            wait_for_runs_to_finish(context.instance)

        # Verify both are fresh after initial materialization
        with define_out_of_process_context(
            __file__, "get_repo_observable_transition", graphql_context.instance
        ) as context:
            repo = get_repo_observable_transition()
            result = _fetch_data_versions(context, repo)
            upstream_node = _get_asset_node(result, "upstream")
            downstream_node = _get_asset_node(result, "downstream")

            assert upstream_node["staleStatus"] == "FRESH"
            assert downstream_node["staleStatus"] == "FRESH"
            assert downstream_node["staleCauses"] == []

        # Step 2: Switch to version where upstream is observable. Make an observation that generates
        # a new data version.
        with define_out_of_process_context(
            __file__, "get_repo_observable_transition_v2", graphql_context.instance
        ) as context:
            # Observe the upstream multiple times with the same data version
            # This simulates the twice-daily observations mentioned in the bug report

            repo = get_repo_observable_transition_v2()
            # upstream_asset = repo.assets_defs_by_key[AssetKey(["upstream"])]
            # Use the upstream asset we stored on the repo
            assert materialize_assets(context, [AssetKey(["upstream"])])
            wait_for_runs_to_finish(context.instance)
            result = _fetch_data_versions(context, repo)
            upstream_node = _get_asset_node(result, "upstream")
            downstream_node = _get_asset_node(result, "downstream")
            assert upstream_node["staleStatus"] == "FRESH"
            assert upstream_node["dataVersion"] == "observation-v1"
            assert downstream_node["staleStatus"] == "STALE"

        # Step 3: Check staleness - this is where the bug manifests
        with define_out_of_process_context(
            __file__, "get_repo_observable_transition_v2", graphql_context.instance
        ) as context:
            repo = get_repo_observable_transition_v2()
            result = _fetch_data_versions(context, repo)

            # This should create a new materialization that has the upstream observation data
            # version in provenance.
            assert materialize_assets(context, [AssetKey(["downstream"])])
            wait_for_runs_to_finish(context.instance)

        with define_out_of_process_context(
            __file__, "get_repo_observable_transition_v2", graphql_context.instance
        ) as context:
            # Re-fetch the status after rematerialization
            result = _fetch_data_versions(context, repo)
            downstream_node = _get_asset_node(result, "downstream")

            # Now downstream should be FRESH because it has the latest observation data version
            # in its provenance. The bug was that it would still show as STALE because the
            # staleness check would compare against newer observations even though the downstream
            # had already materialized against the latest data.
            #
            # With the fix, the staleness check now properly handles the case where an asset
            # transitions from materializable to observable by only comparing against events
            # that are newer than what's in provenance.
            assert downstream_node["staleStatus"] == "FRESH", (
                f"Expected downstream to be FRESH after rematerializing against latest upstream data, "
                f"but got {downstream_node['staleStatus']}. staleCauses: {downstream_node['staleCauses']}."
            )
            assert downstream_node["staleCauses"] == []


# ########################
# ##### REPOSITORY DEFS
# ########################

# These are used to define definition state in the test functions above


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


def get_repo_partitioned():
    partitions_def = StaticPartitionsDefinition(["alpha", "beta"])

    dynamic_partitions_def = DynamicPartitionsDefinition(name="dynamic")

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

    @asset(partitions_def=dynamic_partitions_def)
    def dynamic_asset(context: OpExecutionContext):
        return Output(True, data_version=DataVersion(f"ok_dynamic_asset_{context.partition_key}"))

    @repository
    def repo():
        return [foo, bar, dynamic_asset]

    return repo


def get_cross_repo_test_repo1():
    @asset
    def foo():
        pass

    @repository
    def repo1():
        return [foo]

    return repo1


def get_cross_repo_test_repo2():
    @asset(deps=["foo"])
    def bar():
        pass

    @repository
    def repo2():
        return [bar]

    return repo2


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


def get_repo_observable_transition():
    """Repository that simulates an asset transitioning from materializable to observable.

    This reproduces the bug where:
    1. An upstream asset is initially materializable
    2. It gets materialized
    3. A downstream asset materializes and stores the upstream's materialization data version
    4. The upstream is changed to observable
    5. Observations are reported for the upstream with the same data version
    6. The downstream incorrectly shows as stale because it compares its stored
       materialization-based data version against the current observation-based data version
    """

    @asset
    def upstream():
        """Initially materializable asset."""
        return Output(True, data_version=DataVersion("v1"))

    @asset
    def downstream(upstream):
        """Downstream asset that depends on upstream."""
        return Output(True, data_version=DataVersion("downstream_v1"))

    @repository
    def repo():
        return [upstream, downstream]

    return repo


def get_repo_observable_transition_v2():
    """Version 2: upstream is now observable instead of materializable.

    IMPORTANT: The observable returns a DIFFERENT data version than the original materialization.
    This simulates the real scenario where:
    - The materialization had data version "v1"
    - The observations have timestamp-based or different data versions
    - Even though the actual data hasn't changed, the version scheme changed

    This creates a mismatch: the downstream's provenance has the OLD materialization data
    version "v1", but the staleness check compares against the NEW observation data version,
    causing false staleness.
    """

    @observable_source_asset
    def upstream():
        """Now an observable source asset with a different data version."""
        # Return a different data version to simulate auto-generated or time-based versions
        # This represents observations that have different data versions than the
        # original materialization, even though the actual data is the same
        return DataVersion("observation-v1")

    @asset
    def downstream(upstream):
        """Downstream asset (unchanged)."""
        return Output(True, data_version=DataVersion("downstream_v1"))

    @repository
    def repo():
        return [upstream, downstream]

    return repo


# ########################
# ##### HELPERS
# ########################


def _fetch_data_versions(
    context: WorkspaceRequestContext,
    repo: RepositoryDefinition,
    location_name: Optional[str] = None,
):
    selector = infer_job_selector(
        context, repo.get_implicit_asset_job_names()[0], location_name=location_name
    )
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
